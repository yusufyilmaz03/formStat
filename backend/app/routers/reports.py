"""Rapor/dışa aktarma: cevapları geniş formatta CSV olarak indir."""
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Form
from ..services.stats.dataframe import build_dataframe

router = APIRouter(prefix="/api/forms/{form_id}/report", tags=["reports"])


@router.get("/export.csv")
def export_csv(form_id: int, db: Session = Depends(get_db)):
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(404, "Form bulunamadı.")

    df, meta = build_dataframe(db, form)
    rename = {m["col"]: m["title"] for m in meta}
    df = df.drop(columns=["__response_id"], errors="ignore").rename(columns=rename)
    # Çoklu seçim listelerini okunur metne çevir
    for col in df.columns:
        df[col] = df[col].apply(lambda v: ", ".join(map(str, v)) if isinstance(v, list) else v)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    filename = f"form_{form_id}_cevaplar.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
