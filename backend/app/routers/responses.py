"""Cevap toplama: listeleme, manuel ekleme, CSV içe aktarma."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Answer, Form, Question, Response
from ..schemas import CsvImportRequest, ResponseCreate, ResponseOut
from ..services import importers
from ..services.answers import build_answer

router = APIRouter(prefix="/api/forms/{form_id}/responses", tags=["responses"])


def _get_form(form_id: int, db: Session) -> Form:
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(404, "Form bulunamadı.")
    return form


@router.get("", response_model=list[ResponseOut])
def list_responses(form_id: int, db: Session = Depends(get_db)):
    _get_form(form_id, db)
    return db.scalars(
        select(Response).where(Response.form_id == form_id).order_by(Response.id)
    ).all()


@router.post("", response_model=ResponseOut, status_code=201)
def create_response(form_id: int, payload: ResponseCreate, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    q_by_id = {q.id: q for q in form.questions}

    resp = Response(
        form_id=form_id,
        source=payload.source or "manual",
        external_id=payload.external_id,
        submitted_at=payload.submitted_at or datetime.now(timezone.utc),
    )
    for a in payload.answers:
        question = q_by_id.get(a.question_id)
        if not question:
            continue
        ans = build_answer(question, a.value)
        if ans is not None:
            resp.answers.append(ans)
    db.add(resp)
    db.commit()
    db.refresh(resp)
    return resp


@router.delete("/{response_id}", status_code=204)
def delete_response(form_id: int, response_id: int, db: Session = Depends(get_db)):
    resp = db.get(Response, response_id)
    if not resp or resp.form_id != form_id:
        raise HTTPException(404, "Cevap bulunamadı.")
    db.delete(resp)
    db.commit()


@router.delete("", status_code=204)
def clear_responses(form_id: int, db: Session = Depends(get_db)):
    """Formun tüm cevaplarını siler (dikkat!)."""
    _get_form(form_id, db)
    for resp in db.scalars(select(Response).where(Response.form_id == form_id)).all():
        db.delete(resp)
    db.commit()


# ---------- CSV içe aktarma ----------
@router.post("/import/preview")
async def import_preview(form_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    _get_form(form_id, db)
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Boş dosya.")
    try:
        return importers.save_upload_preview(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"CSV okunamadı: {exc}") from exc


@router.post("/import")
def import_apply(form_id: int, payload: CsvImportRequest, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    q_by_id = {q.id: q for q in form.questions}

    try:
        df = importers.load_import(payload.import_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    # Yalnızca geçerli eşlemeleri al
    valid_maps = [m for m in payload.mappings if m.question_id in q_by_id and m.column in df.columns]
    if not valid_maps:
        raise HTTPException(400, "Geçerli sütun-soru eşlemesi yok.")

    imported = 0
    for _, row in df.iterrows():
        resp = Response(form_id=form_id, source="csv")
        for m in valid_maps:
            question = q_by_id[m.question_id]
            ans = build_answer(question, row[m.column])
            if ans is not None:
                resp.answers.append(ans)
        if resp.answers:  # tamamen boş satırları atla
            db.add(resp)
            imported += 1
    db.commit()
    importers.cleanup_import(payload.import_id)
    return {"imported": imported}
