"""Otomatik içgörü: anlamlı ilişkiler + dağılım ve veri kalitesi uyarıları."""
from __future__ import annotations

from itertools import combinations

import pandas as pd
from sqlalchemy.orm import Session

from ...models import Form
from . import inferential as inf
from .dataframe import build_dataframe, clean_float


def _pair_finding(df: pd.DataFrame, a: dict, b: dict) -> dict | None:
    ra, rb = a["role"], b["role"]
    if ra == "numeric" and rb == "numeric":
        r = inf._correlation(df, a, b)
        if "error" in r or r.get("statistic") is None:
            return None
        mag = abs(r["statistic"])
        level = "güçlü" if mag >= 0.5 else "orta" if mag >= 0.3 else "zayıf"
        return {
            "p_value": r.get("p_value"),
            "effect": mag,
            "title": f"{a['title']} ↔ {b['title']}",
            "detail": f"{level.capitalize()} korelasyon (r={r['statistic']}, p={r['p_value']}).",
            "related": [a["id"], b["id"]],
        }
    if {ra, rb} == {"numeric", "categorical"}:
        num, cat = (a, b) if ra == "numeric" else (b, a)
        r = inf._numeric_by_group(df, num, cat)
        if "error" in r:
            return None
        es = (r.get("effect_size") or {}).get("value")
        return {
            "p_value": r.get("p_value"),
            "effect": abs(es) if es is not None else 0.0,
            "title": f"{cat['title']} → {num['title']}",
            "detail": f"'{cat['title']}' gruplarına göre '{num['title']}' ortalaması farklılaşıyor (p={r['p_value']}).",
            "related": [num["id"], cat["id"]],
        }
    if ra == "categorical" and rb == "categorical":
        r = inf._chi_square(df, a, b)
        if "error" in r:
            return None
        es = (r.get("effect_size") or {}).get("value")
        return {
            "p_value": r.get("p_value"),
            "effect": abs(es) if es is not None else 0.0,
            "title": f"{a['title']} ↔ {b['title']}",
            "detail": f"Anlamlı ilişki (Cramér's V={es}, p={r['p_value']}).",
            "related": [a["id"], b["id"]],
        }
    return None


def generate_insights(db: Session, form: Form) -> dict:
    df, meta = build_dataframe(db, form)
    n = int(len(df))
    findings: list[dict] = []

    if n < 3:
        return {
            "response_count": n,
            "findings": [
                {
                    "type": "info",
                    "severity": "low",
                    "title": "Yetersiz veri",
                    "detail": "Otomatik içgörü için en az 3 cevap gerekli.",
                    "related": [],
                }
            ],
        }

    usable = [m for m in meta if m["role"] in {"numeric", "categorical"}]

    # 1) Anlamlı ilişkiler (etki büyüklüğüne göre sıralı)
    relations = []
    for a, b in combinations(usable, 2):
        f = _pair_finding(df, a, b)
        if f and f.get("p_value") is not None and f["p_value"] < 0.05:
            relations.append(f)
    relations.sort(key=lambda x: x["effect"], reverse=True)
    for f in relations[:10]:
        findings.append(
            {
                "type": "relationship",
                "severity": "high" if f["effect"] >= 0.5 else "medium",
                "title": f["title"],
                "detail": f["detail"],
                "related": f["related"],
            }
        )

    # 2) Dağılım notları
    for m in meta:
        col = m["col"]
        if col not in df.columns:
            continue
        if m["role"] == "categorical":
            s = df[col].dropna()
            s = s[s.astype(str).str.strip() != ""]
            if len(s) >= 5:
                top_pct = 100 * s.value_counts().iloc[0] / len(s)
                if top_pct >= 70:
                    findings.append(
                        {
                            "type": "distribution",
                            "severity": "low",
                            "title": f"Baskın yanıt: {m['title']}",
                            "detail": f"Cevapların %{top_pct:.0f}'i tek bir seçenekte toplanmış ('{s.value_counts().index[0]}').",
                            "related": [m["id"]],
                        }
                    )
        elif m["role"] == "numeric":
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) >= 5 and abs(s.skew()) >= 1:
                yon = "sağa" if s.skew() > 0 else "sola"
                findings.append(
                    {
                        "type": "distribution",
                        "severity": "low",
                        "title": f"Çarpık dağılım: {m['title']}",
                        "detail": f"Dağılım {yon} çarpık (çarpıklık={clean_float(s.skew(), 2)}); ortalama yerine medyan daha temsili olabilir.",
                        "related": [m["id"]],
                    }
                )

    # 3) Veri kalitesi (eksik veri)
    for m in meta:
        col = m["col"]
        if col not in df.columns:
            continue
        answered = int(df[col].apply(lambda v: v not in (None, "") and not (isinstance(v, float) and pd.isna(v)) and v != []).sum())
        if n > 0 and answered / n < 0.5:
            findings.append(
                {
                    "type": "quality",
                    "severity": "medium",
                    "title": f"Yüksek eksik veri: {m['title']}",
                    "detail": f"Bu soru cevapların yalnızca %{100 * answered / n:.0f}'inde yanıtlanmış.",
                    "related": [m["id"]],
                }
            )

    if not findings:
        findings.append(
            {
                "type": "info",
                "severity": "low",
                "title": "Belirgin bulgu yok",
                "detail": "Değişkenler arasında istatistiksel olarak anlamlı güçlü bir ilişki tespit edilmedi.",
                "related": [],
            }
        )

    return {"response_count": n, "findings": findings}
