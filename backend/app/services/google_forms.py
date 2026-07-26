"""Google Forms entegrasyonu: OAuth, form dışa aktarma+yayınlama, cevap senkronizasyonu."""
from __future__ import annotations

import json
import os
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AppSetting, Form, Question, Response
from .answers import build_answer

TOKEN_KEY = "google_token"


# ---------- OAuth ----------
def _require_client_secret() -> None:
    if not os.path.exists(settings.google_client_secret_file):
        raise FileNotFoundError(
            "client_secret.json bulunamadı. Google Cloud'dan indirdiğin 'Desktop' "
            f"istemci dosyasını şuraya koy: {settings.google_client_secret_file}"
        )


def _get_flow():
    from google_auth_oauthlib.flow import Flow

    _require_client_secret()
    return Flow.from_client_secrets_file(
        settings.google_client_secret_file,
        scopes=settings.google_scopes,
        redirect_uri=settings.oauth_redirect_uri,
    )


def _save_creds(db: Session, creds) -> None:
    data = json.loads(creds.to_json())
    setting = db.get(AppSetting, TOKEN_KEY)
    if setting is None:
        db.add(AppSetting(key=TOKEN_KEY, value=data))
    else:
        setting.value = data
    db.commit()


def get_credentials(db: Session):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    setting = db.get(AppSetting, TOKEN_KEY)
    if not setting or not setting.value:
        return None
    creds = Credentials.from_authorized_user_info(setting.value, settings.google_scopes)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_creds(db, creds)
    return creds


def is_connected(db: Session) -> bool:
    try:
        return get_credentials(db) is not None
    except Exception:  # noqa: BLE001
        return False


def build_auth_url() -> str:
    flow = _get_flow()
    url, _state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return url


def exchange_code(db: Session, code: str) -> None:
    flow = _get_flow()
    flow.fetch_token(code=code)
    _save_creds(db, flow.credentials)


def disconnect(db: Session) -> None:
    setting = db.get(AppSetting, TOKEN_KEY)
    if setting:
        db.delete(setting)
        db.commit()


# ---------- Forms API ----------
def _service(db: Session):
    from googleapiclient.discovery import build

    creds = get_credentials(db)
    if not creds:
        raise RuntimeError("Google bağlantısı yok. Önce 'Google'a Bağlan' ile yetkilendir.")
    return build("forms", "v1", credentials=creds, cache_discovery=False)


_GCHOICE = {"single_choice": "RADIO", "multi_choice": "CHECKBOX", "dropdown": "DROP_DOWN"}


def _question_to_item(q: Question, index: int) -> dict:
    question: dict = {"required": bool(q.required)}
    if q.type in _GCHOICE:
        question["choiceQuestion"] = {
            "type": _GCHOICE[q.type],
            "options": [{"value": str(o)} for o in (q.options or [])],
        }
    elif q.type == "long_text":
        question["textQuestion"] = {"paragraph": True}
    elif q.type == "linear_scale":
        question["scaleQuestion"] = {
            "low": q.scale_min if q.scale_min is not None else 1,
            "high": q.scale_max if q.scale_max is not None else 5,
        }
    elif q.type == "date":
        question["dateQuestion"] = {"includeYear": True}
    else:  # short_text, email, number -> metin
        question["textQuestion"] = {"paragraph": False}

    return {
        "createItem": {
            "item": {"title": q.title, "questionItem": {"question": question}},
            "location": {"index": index},
        }
    }


def _publish(service, form_id: str) -> bool:
    body = {"publishSettings": {"publishState": {"isPublished": True, "isAcceptingResponses": True}}}
    try:
        service.forms().setPublishSettings(formId=form_id, body=body).execute()
        return True
    except AttributeError:
        # Yüklü istemci sürümünde publish metodu yoksa (eski API): form zaten yanıt alabilir
        return False
    except Exception:  # noqa: BLE001
        return False


def export_form(db: Session, form: Form) -> dict:
    """Uygulamadaki formu Google Forms'a aktarır, yayınlar ve kimlikleri saklar."""
    service = _service(db)
    created = service.forms().create(
        body={"info": {"title": form.title, "documentTitle": form.title}}
    ).execute()
    gid = created["formId"]

    questions = list(form.questions)
    requests: list[dict] = []
    if form.description:
        requests.append(
            {"updateFormInfo": {"info": {"description": form.description}, "updateMask": "description"}}
        )
    item_start = len(requests)
    for i, q in enumerate(questions):
        requests.append(_question_to_item(q, i))

    if requests:
        result = service.forms().batchUpdate(formId=gid, body={"requests": requests}).execute()
        replies = result.get("replies", [])
        # createItem yanıtlarını sorularımızla eşle (aynı sırada)
        create_replies = [r for r in replies if "createItem" in r]
        for q, reply in zip(questions, create_replies[: len(questions)] if create_replies else []):
            ci = reply.get("createItem", {})
            q.google_item_id = ci.get("itemId")
            qids = ci.get("questionId") or []
            q.google_question_id = qids[0] if qids else None
        _ = item_start  # okunabilirlik

    published = _publish(service, gid)
    info = service.forms().get(formId=gid).execute()
    form.google_form_id = gid
    form.google_responder_uri = info.get("responderUri")
    form.published = published
    db.commit()
    db.refresh(form)
    return {
        "google_form_id": gid,
        "responder_uri": form.google_responder_uri,
        "published": published,
        "edit_url": f"https://docs.google.com/forms/d/{gid}/edit",
    }


def sync_responses(db: Session, form: Form) -> dict:
    """Google Forms cevaplarını çekip yerel DB'ye normalize eder (yeni olanları ekler)."""
    if not form.google_form_id:
        raise RuntimeError("Bu form Google'a aktarılmamış.")
    service = _service(db)

    # Google questionId -> yerel Question eşlemesi
    q_by_gqid = {q.google_question_id: q for q in form.questions if q.google_question_id}
    if not q_by_gqid:
        # Eşleme yoksa forms.get ile başlık üzerinden kur
        q_by_gqid = _rebuild_question_map(db, service, form)

    existing = set(
        db.scalars(
            select(Response.external_id).where(
                Response.form_id == form.id, Response.source == "google"
            )
        ).all()
    )

    imported = 0
    page_token = None
    while True:
        params = {"formId": form.google_form_id}
        if page_token:
            params["pageToken"] = page_token
        result = service.forms().responses().list(**params).execute()
        for gr in result.get("responses", []):
            rid = gr.get("responseId")
            if rid in existing:
                continue
            resp = Response(
                form_id=form.id,
                source="google",
                external_id=rid,
                submitted_at=_parse_time(gr.get("lastSubmittedTime") or gr.get("createTime")),
            )
            for gqid, ans in (gr.get("answers") or {}).items():
                question = q_by_gqid.get(gqid)
                if not question:
                    continue
                values = [a.get("value") for a in ans.get("textAnswers", {}).get("answers", [])]
                raw = values if question.type == "multi_choice" else (values[0] if values else None)
                obj = build_answer(question, raw)
                if obj is not None:
                    resp.answers.append(obj)
            if resp.answers:
                db.add(resp)
                existing.add(rid)
                imported += 1
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    db.commit()
    return {"imported": imported}


def _rebuild_question_map(db: Session, service, form: Form) -> dict:
    info = service.forms().get(formId=form.google_form_id).execute()
    title_to_q = {q.title: q for q in form.questions}
    mapping = {}
    for item in info.get("items", []):
        qitem = item.get("questionItem")
        if not qitem:
            continue
        gqid = qitem.get("question", {}).get("questionId")
        local = title_to_q.get(item.get("title"))
        if gqid and local:
            local.google_question_id = gqid
            local.google_item_id = item.get("itemId")
            mapping[gqid] = local
    db.commit()
    return mapping


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
