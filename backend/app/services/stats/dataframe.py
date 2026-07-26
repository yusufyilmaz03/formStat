"""Bir formun cevaplarını analiz için pandas DataFrame'e dönüştürür + yardımcılar."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Form, Response


def qcol(qid: int) -> str:
    return f"q{qid}"


def question_role(qtype: str) -> str:
    if qtype in {"number", "linear_scale"}:
        return "numeric"
    if qtype in {"single_choice", "dropdown"}:
        return "categorical"
    if qtype == "multi_choice":
        return "multi"
    return "text"


def build_dataframe(db: Session, form: Form) -> tuple[pd.DataFrame, list[dict]]:
    """Satır = cevap, sütun = q{soru_id}. meta: her sorunun rol bilgisi."""
    questions = list(form.questions)
    responses = db.scalars(
        select(Response).where(Response.form_id == form.id).order_by(Response.id)
    ).all()

    rows = []
    for resp in responses:
        row: dict = {"__response_id": resp.id}
        ans_by_q = {a.question_id: a for a in resp.answers}
        for q in questions:
            col = qcol(q.id)
            role = question_role(q.type)
            a = ans_by_q.get(q.id)
            if a is None:
                row[col] = np.nan if role == "numeric" else (None if role != "multi" else [])
            elif role == "numeric":
                row[col] = a.value_number if a.value_number is not None else np.nan
            elif role == "multi":
                row[col] = a.value_options or []
            else:
                row[col] = a.value_text
        rows.append(row)

    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["__response_id"] + [qcol(q.id) for q in questions])
    meta = [
        {
            "id": q.id,
            "title": q.title,
            "type": q.type,
            "col": qcol(q.id),
            "role": question_role(q.type),
        }
        for q in questions
    ]
    return df, meta


def clean_float(x, ndigits: int = 4):
    """NaN/inf -> None, aksi halde yuvarlanmış float."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, ndigits)


def to_native(obj):
    """numpy/pandas tiplerini JSON'a uygun native Python tiplerine çevirir."""
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_native(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return clean_float(obj)
    if isinstance(obj, np.ndarray):
        return to_native(obj.tolist())
    if isinstance(obj, float):
        return clean_float(obj)
    return obj
