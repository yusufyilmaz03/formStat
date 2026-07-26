"""Google Forms uç noktaları: OAuth durum/bağlan/callback + form dışa aktarma & senkron."""
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Form
from ..services import google_forms as gf

router = APIRouter(tags=["google"])


@router.get("/api/google/status")
def status(db: Session = Depends(get_db)):
    return {
        "client_configured": os.path.exists(settings.google_client_secret_file),
        "connected": gf.is_connected(db),
    }


@router.get("/api/google/auth")
def auth():
    try:
        return {"url": gf.build_auth_url()}
    except FileNotFoundError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/api/google/callback")
def callback(code: str = Query(default=""), error: str = Query(default=""), db: Session = Depends(get_db)):
    if error:
        return RedirectResponse(f"{settings.frontend_origin}/?google=error")
    if not code:
        raise HTTPException(400, "Yetkilendirme kodu yok.")
    try:
        gf.exchange_code(db, code)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Yetkilendirme başarısız: {exc}") from exc
    return RedirectResponse(f"{settings.frontend_origin}/?google=connected")


@router.post("/api/google/disconnect")
def disconnect(db: Session = Depends(get_db)):
    gf.disconnect(db)
    return {"connected": False}


def _get_form(form_id: int, db: Session) -> Form:
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(404, "Form bulunamadı.")
    return form


@router.post("/api/forms/{form_id}/google/export")
def export_to_google(form_id: int, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    if not form.questions:
        raise HTTPException(400, "Formda hiç soru yok.")
    try:
        return gf.export_form(db, form)
    except FileNotFoundError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Google Forms hatası: {exc}") from exc


@router.post("/api/forms/{form_id}/google/sync")
def sync_from_google(form_id: int, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    if not form.google_form_id:
        raise HTTPException(400, "Bu form önce Google'a aktarılmalı.")
    try:
        return gf.sync_responses(db, form)
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Google Forms hatası: {exc}") from exc
