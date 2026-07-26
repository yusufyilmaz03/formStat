"""Betimleyici istatistikler: soru bazlı özet + genel bakış."""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ...models import Form
from .dataframe import build_dataframe, clean_float


def _numeric_summary(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"count": 0}
    hist_counts, hist_edges = np.histogram(s, bins=min(10, max(1, s.nunique())))
    histogram = [
        {
            "bin_start": clean_float(hist_edges[i]),
            "bin_end": clean_float(hist_edges[i + 1]),
            "count": int(hist_counts[i]),
        }
        for i in range(len(hist_counts))
    ]
    return {
        "count": int(s.count()),
        "mean": clean_float(s.mean()),
        "median": clean_float(s.median()),
        "mode": clean_float(s.mode().iloc[0]) if not s.mode().empty else None,
        "std": clean_float(s.std()),
        "min": clean_float(s.min()),
        "max": clean_float(s.max()),
        "q1": clean_float(s.quantile(0.25)),
        "q3": clean_float(s.quantile(0.75)),
        "skew": clean_float(s.skew()),
        "kurtosis": clean_float(s.kurtosis()),
        "histogram": histogram,
        "box": {
            "min": clean_float(s.min()),
            "q1": clean_float(s.quantile(0.25)),
            "median": clean_float(s.median()),
            "q3": clean_float(s.quantile(0.75)),
            "max": clean_float(s.max()),
        },
    }


def _categorical_summary(series: pd.Series) -> dict:
    s = series.dropna()
    s = s[s.astype(str).str.strip() != ""]
    if s.empty:
        return {"count": 0, "distribution": []}
    counts = s.value_counts()
    total = int(counts.sum())
    distribution = [
        {"label": str(label), "count": int(c), "percent": clean_float(100 * c / total, 2)}
        for label, c in counts.items()
    ]
    return {
        "count": total,
        "unique": int(s.nunique()),
        "mode": str(counts.index[0]),
        "distribution": distribution,
    }


def _multi_summary(series: pd.Series) -> dict:
    counter: Counter = Counter()
    respondents = 0
    for val in series:
        if isinstance(val, list) and val:
            respondents += 1
            counter.update(str(v) for v in val)
    if not counter:
        return {"count": 0, "distribution": []}
    distribution = [
        {"label": label, "count": c, "percent": clean_float(100 * c / respondents, 2)}
        for label, c in counter.most_common()
    ]
    return {"count": respondents, "unique": len(counter), "distribution": distribution}


def _text_summary(series: pd.Series) -> dict:
    s = series.dropna()
    s = s[s.astype(str).str.strip() != ""]
    if s.empty:
        return {"count": 0, "top_values": []}
    counts = s.value_counts().head(10)
    lengths = s.astype(str).str.len()
    return {
        "count": int(s.count()),
        "unique": int(s.nunique()),
        "avg_length": clean_float(lengths.mean(), 1),
        "top_values": [{"label": str(k), "count": int(v)} for k, v in counts.items()],
    }


def describe_form(db: Session, form: Form) -> dict:
    df, meta = build_dataframe(db, form)
    n = int(len(df))

    per_question = []
    completeness_num = 0
    for m in meta:
        col = m["col"]
        role = m["role"]
        if col in df.columns:
            if role == "numeric":
                summary = _numeric_summary(df[col])
            elif role == "categorical":
                summary = _categorical_summary(df[col])
            elif role == "multi":
                summary = _multi_summary(df[col])
            else:
                summary = _text_summary(df[col])
        else:
            summary = {"count": 0}
        answered = summary.get("count", 0)
        completeness_num += answered
        per_question.append(
            {
                "id": m["id"],
                "title": m["title"],
                "type": m["type"],
                "role": role,
                "answered": answered,
                "missing": max(0, n - answered),
                "summary": summary,
            }
        )

    total_cells = n * len(meta) if meta else 0
    completion_rate = clean_float(100 * completeness_num / total_cells, 1) if total_cells else None

    return {
        "response_count": n,
        "question_count": len(meta),
        "completion_rate": completion_rate,
        "questions": per_question,
    }
