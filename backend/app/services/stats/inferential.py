"""Çıkarımsal testler: ki-kare, t-testi, ANOVA, korelasyon + çapraz tablo."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from ...models import Form
from .dataframe import build_dataframe, clean_float

ALPHA = 0.05


def _meta_by_id(meta: list[dict]) -> dict:
    return {m["id"]: m for m in meta}


def _sig_text(p: float) -> str:
    if p is None:
        return "Test hesaplanamadı."
    return (
        f"p = {p:.4f} < 0.05 → istatistiksel olarak anlamlı bir ilişki/fark var."
        if p < ALPHA
        else f"p = {p:.4f} ≥ 0.05 → anlamlı bir ilişki/fark bulunamadı."
    )


def _cramers_v(chi2: float, n: int, r: int, c: int) -> float | None:
    denom = n * (min(r, c) - 1)
    if denom <= 0:
        return None
    return float(np.sqrt(chi2 / denom))


def _chi_square(df: pd.DataFrame, a: dict, b: dict) -> dict:
    sub = df[[a["col"], b["col"]]].dropna()
    sub = sub[(sub[a["col"]].astype(str).str.strip() != "") & (sub[b["col"]].astype(str).str.strip() != "")]
    table = pd.crosstab(sub[a["col"]], sub[b["col"]])
    if table.size == 0 or table.shape[0] < 2 or table.shape[1] < 2:
        return {"test": "chi_square", "error": "Ki-kare için her iki değişkende en az 2 kategori gerekli."}
    chi2, p, dof, _ = stats.chi2_contingency(table)
    v = _cramers_v(chi2, int(table.values.sum()), table.shape[0], table.shape[1])
    return {
        "test": "chi_square",
        "test_label": "Ki-kare bağımsızlık testi",
        "statistic": clean_float(chi2),
        "p_value": clean_float(p),
        "dof": int(dof),
        "effect_size": {"name": "Cramér's V", "value": clean_float(v)},
        "n": int(table.values.sum()),
        "interpretation": _sig_text(p),
    }


def _cohens_d(g1: np.ndarray, g2: np.ndarray) -> float | None:
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return None
    pooled = np.sqrt(((n1 - 1) * g1.var(ddof=1) + (n2 - 1) * g2.var(ddof=1)) / (n1 + n2 - 2))
    if pooled == 0:
        return None
    return float((g1.mean() - g2.mean()) / pooled)


def _numeric_by_group(df: pd.DataFrame, num: dict, cat: dict) -> dict:
    sub = df[[num["col"], cat["col"]]].copy()
    sub[num["col"]] = pd.to_numeric(sub[num["col"]], errors="coerce")
    sub = sub.dropna()
    sub = sub[sub[cat["col"]].astype(str).str.strip() != ""]
    groups = [g[num["col"]].values for _, g in sub.groupby(cat["col"]) if len(g) >= 2]
    labels = [str(k) for k, g in sub.groupby(cat["col"]) if len(g) >= 2]
    if len(groups) < 2:
        return {"test": "group_compare", "error": "Karşılaştırma için en az 2 grupta yeterli veri yok."}

    group_stats = [
        {"group": lbl, "n": int(len(g)), "mean": clean_float(np.mean(g)), "std": clean_float(np.std(g, ddof=1))}
        for lbl, g in zip(labels, groups)
    ]

    if len(groups) == 2:
        t, p = stats.ttest_ind(groups[0], groups[1], equal_var=False)  # Welch
        d = _cohens_d(groups[0], groups[1])
        return {
            "test": "t_test",
            "test_label": "Bağımsız örneklem t-testi (Welch)",
            "statistic": clean_float(t),
            "p_value": clean_float(p),
            "effect_size": {"name": "Cohen's d", "value": clean_float(d)},
            "groups": group_stats,
            "interpretation": _sig_text(p),
        }

    f, p = stats.f_oneway(*groups)
    # eta-kare (etki büyüklüğü)
    all_vals = np.concatenate(groups)
    grand = all_vals.mean()
    ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    ss_total = ((all_vals - grand) ** 2).sum()
    eta2 = float(ss_between / ss_total) if ss_total > 0 else None

    posthoc = None
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd

        flat_vals = np.concatenate(groups)
        flat_lbls = np.concatenate([[lbl] * len(g) for lbl, g in zip(labels, groups)])
        tuk = pairwise_tukeyhsd(flat_vals, flat_lbls)
        posthoc = [
            {
                "group1": str(row[0]),
                "group2": str(row[1]),
                "mean_diff": clean_float(row[2]),
                "p_adj": clean_float(row[3]),
                "reject": bool(row[6]),
            }
            for row in tuk.summary().data[1:]
        ]
    except Exception:  # noqa: BLE001
        posthoc = None

    return {
        "test": "anova",
        "test_label": "Tek yönlü ANOVA",
        "statistic": clean_float(f),
        "p_value": clean_float(p),
        "effect_size": {"name": "Eta-kare (η²)", "value": clean_float(eta2)},
        "groups": group_stats,
        "posthoc": posthoc,
        "interpretation": _sig_text(p),
    }


def _correlation(df: pd.DataFrame, a: dict, b: dict) -> dict:
    sub = df[[a["col"], b["col"]]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(sub) < 3:
        return {"test": "correlation", "error": "Korelasyon için en az 3 tam gözlem gerekli."}
    x, y = sub[a["col"]].values, sub[b["col"]].values
    pear_r, pear_p = stats.pearsonr(x, y)
    spear_r, spear_p = stats.spearmanr(x, y)
    scatter = [{"x": clean_float(xi), "y": clean_float(yi)} for xi, yi in zip(x, y)]
    strength = abs(pear_r)
    level = "güçlü" if strength >= 0.5 else "orta" if strength >= 0.3 else "zayıf"
    direction = "pozitif" if pear_r > 0 else "negatif"
    return {
        "test": "correlation",
        "test_label": "Korelasyon (Pearson & Spearman)",
        "pearson": {"r": clean_float(pear_r), "p_value": clean_float(pear_p)},
        "spearman": {"r": clean_float(spear_r), "p_value": clean_float(spear_p)},
        "statistic": clean_float(pear_r),
        "p_value": clean_float(pear_p),
        "n": int(len(sub)),
        "scatter": scatter,
        "interpretation": (
            f"Pearson r = {pear_r:.3f} ({direction}, {level}). " + _sig_text(pear_p)
        ),
    }


def run_test(db: Session, form: Form, qa_id: int, qb_id: int) -> dict:
    df, meta = build_dataframe(db, form)
    m = _meta_by_id(meta)
    if qa_id not in m or qb_id not in m:
        return {"error": "Soru bulunamadı."}
    a, b = m[qa_id], m[qb_id]
    ra, rb = a["role"], b["role"]

    base = {"question_a": {"id": a["id"], "title": a["title"], "role": ra},
            "question_b": {"id": b["id"], "title": b["title"], "role": rb}}

    if ra == "numeric" and rb == "numeric":
        result = _correlation(df, a, b)
    elif ra == "numeric" and rb == "categorical":
        result = _numeric_by_group(df, a, b)
    elif ra == "categorical" and rb == "numeric":
        result = _numeric_by_group(df, b, a)
    elif ra == "categorical" and rb == "categorical":
        result = _chi_square(df, a, b)
    else:
        return {**base, "error": "Bu soru tipleri için otomatik test desteklenmiyor (metin/çoklu seçim)."}

    return {**base, **result}


def crosstab(db: Session, form: Form, qa_id: int, qb_id: int) -> dict:
    df, meta = build_dataframe(db, form)
    m = _meta_by_id(meta)
    if qa_id not in m or qb_id not in m:
        return {"error": "Soru bulunamadı."}
    a, b = m[qa_id], m[qb_id]
    if a["role"] not in {"categorical"} or b["role"] not in {"categorical"}:
        return {"error": "Çapraz tablo için her iki soru da kategorik (tek/çoklu seçim) olmalı."}

    sub = df[[a["col"], b["col"]]].dropna()
    sub = sub[(sub[a["col"]].astype(str).str.strip() != "") & (sub[b["col"]].astype(str).str.strip() != "")]
    table = pd.crosstab(sub[a["col"]], sub[b["col"]])
    if table.size == 0:
        return {"error": "Çapraz tablo için yeterli veri yok."}

    row_labels = [str(x) for x in table.index]
    col_labels = [str(x) for x in table.columns]
    counts = table.values.tolist()
    total = int(table.values.sum())
    row_pct = (table.div(table.sum(axis=1), axis=0) * 100).round(1).values.tolist()

    chi = _chi_square(df, a, b)
    return {
        "question_a": {"id": a["id"], "title": a["title"]},
        "question_b": {"id": b["id"], "title": b["title"]},
        "row_labels": row_labels,
        "col_labels": col_labels,
        "counts": counts,
        "row_percent": row_pct,
        "total": total,
        "chi_square": {k: chi.get(k) for k in ("statistic", "p_value", "effect_size", "interpretation", "error")},
    }
