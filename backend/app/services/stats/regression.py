"""Regresyon: sayısal hedef -> OLS, ikili kategorik hedef -> Lojistik."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sqlalchemy.orm import Session

from ...models import Form
from .dataframe import build_dataframe, clean_float


def _meta_by_id(meta: list[dict]) -> dict:
    return {m["id"]: m for m in meta}


def _build_design(df: pd.DataFrame, predictors: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    parts = []
    for p in predictors:
        col = p["col"]
        if p["role"] == "numeric":
            parts.append(pd.to_numeric(df[col], errors="coerce").rename(p["title"]))
        elif p["role"] == "categorical":
            dummies = pd.get_dummies(df[col].astype("string"), prefix=p["title"], drop_first=True, dtype=float)
            parts.append(dummies)
        # metin/çoklu seçim atlanır
    if not parts:
        return pd.DataFrame(index=df.index), []
    X = pd.concat(parts, axis=1)
    return X, list(X.columns)


def run_regression(db: Session, form: Form, target_id: int, predictor_ids: list[int]) -> dict:
    df, meta = build_dataframe(db, form)
    m = _meta_by_id(meta)
    if target_id not in m:
        return {"error": "Hedef soru bulunamadı."}
    target = m[target_id]
    predictors = [m[pid] for pid in predictor_ids if pid in m and pid != target_id]
    predictors = [p for p in predictors if p["role"] in {"numeric", "categorical"}]
    if not predictors:
        return {"error": "En az bir sayısal veya kategorik bağımsız değişken gerekli."}

    X, feature_names = _build_design(df, predictors)
    if X.empty or not feature_names:
        return {"error": "Bağımsız değişkenlerden tasarım matrisi oluşturulamadı."}

    # Hedef tipi
    if target["role"] == "numeric":
        y = pd.to_numeric(df[target["col"]], errors="coerce")
        model_type = "linear"
    elif target["role"] == "categorical":
        raw = df[target["col"]].astype("string")
        classes = [c for c in raw.dropna().unique() if str(c).strip() != ""]
        if len(classes) != 2:
            return {"error": f"Lojistik regresyon için hedef tam 2 sınıflı olmalı (bulunan: {len(classes)})."}
        positive = sorted(classes)[-1]
        y = (raw == positive).astype(float)
        y[raw.isna()] = np.nan
        model_type = "logistic"
    else:
        return {"error": "Hedef sayısal ya da kategorik olmalı."}

    data = pd.concat([y.rename("__y"), X], axis=1).dropna()
    if len(data) < len(feature_names) + 2:
        return {"error": "Yeterli gözlem yok (değişken sayısına göre çok az satır)."}

    y_fit = data["__y"].astype(float)
    X_fit = sm.add_constant(data[feature_names].astype(float), has_constant="add")

    try:
        if model_type == "linear":
            res = sm.OLS(y_fit, X_fit).fit()
            fit_metrics = {"r_squared": clean_float(res.rsquared), "adj_r_squared": clean_float(res.rsquared_adj)}
        else:
            res = sm.Logit(y_fit, X_fit).fit(disp=0)
            fit_metrics = {"pseudo_r_squared": clean_float(res.prsquared)}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Model uygun değil (tekil matris / ayrışma olabilir): {exc}"}

    coefs = []
    conf = res.conf_int()
    for name in X_fit.columns:
        coefs.append(
            {
                "name": "Sabit (intercept)" if name == "const" else name,
                "coef": clean_float(res.params[name]),
                "std_err": clean_float(res.bse[name]),
                "p_value": clean_float(res.pvalues[name]),
                "ci_low": clean_float(conf.loc[name, 0]),
                "ci_high": clean_float(conf.loc[name, 1]),
                "significant": bool(res.pvalues[name] < 0.05),
            }
        )

    return {
        "model_type": model_type,
        "target": {"id": target["id"], "title": target["title"]},
        "n": int(len(data)),
        "fit": fit_metrics,
        "coefficients": coefs,
        "interpretation": _interpret(model_type, fit_metrics, coefs, target["title"]),
    }


def _interpret(model_type: str, fit: dict, coefs: list[dict], target_title: str) -> str:
    sig = [c["name"] for c in coefs if c["significant"] and c["name"] != "Sabit (intercept)"]
    if model_type == "linear":
        r2 = fit.get("r_squared")
        head = f"Model, '{target_title}' değişkenindeki varyansın %{(r2 or 0) * 100:.1f}'ini açıklıyor. "
    else:
        head = f"'{target_title}' için lojistik model. "
    if sig:
        return head + "Anlamlı değişken(ler): " + ", ".join(sig) + "."
    return head + "İstatistiksel olarak anlamlı değişken bulunamadı."
