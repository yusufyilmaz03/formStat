"""Segmentasyon: sayısal cevaplar üzerinde K-means kümeleme + PCA görselleştirme."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from ...models import Form
from .dataframe import build_dataframe, clean_float


def run_segmentation(
    db: Session, form: Form, question_ids: list[int] | None, n_clusters: int | None
) -> dict:
    df, meta = build_dataframe(db, form)
    numeric_meta = [m for m in meta if m["role"] == "numeric"]
    if question_ids:
        numeric_meta = [m for m in numeric_meta if m["id"] in question_ids]
    if len(numeric_meta) < 2:
        return {"error": "Segmentasyon için en az 2 sayısal soru gerekli."}

    cols = [m["col"] for m in numeric_meta]
    X = df[cols].apply(pd.to_numeric, errors="coerce")
    # Eksikleri sütun ortalamasıyla doldur
    X = X.fillna(X.mean())
    X = X.dropna(axis=1, how="all")
    if X.shape[1] < 2:
        return {"error": "Yeterli sayısal veri yok."}
    X = X.dropna()
    if len(X) < 4:
        return {"error": "Segmentasyon için en az 4 cevap gerekli."}

    Xs = StandardScaler().fit_transform(X)

    # Küme sayısı otomatik seçimi (silhouette)
    silhouettes = {}
    if not n_clusters:
        max_k = min(6, len(X) - 1)
        best_k, best_score = 2, -1.0
        for k in range(2, max_k + 1):
            labels_k = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(Xs)
            if len(set(labels_k)) < 2:
                continue
            score = silhouette_score(Xs, labels_k)
            silhouettes[k] = clean_float(score, 3)
            if score > best_score:
                best_k, best_score = k, score
        n_clusters = best_k

    n_clusters = max(2, min(int(n_clusters), len(X) - 1))
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = km.fit_predict(Xs)
    sil = clean_float(silhouette_score(Xs, labels), 3) if len(set(labels)) > 1 else None

    # Küme profilleri (orijinal ölçekte ortalamalar)
    title_by_col = {m["col"]: m["title"] for m in numeric_meta}
    profiled = X.copy()
    profiled["__cluster"] = labels
    clusters = []
    for cid, group in profiled.groupby("__cluster"):
        clusters.append(
            {
                "cluster": int(cid),
                "size": int(len(group)),
                "means": {
                    title_by_col[c]: clean_float(group[c].mean())
                    for c in cols
                    if c in group.columns
                },
            }
        )

    # 2B PCA görselleştirme
    points = []
    if Xs.shape[1] >= 2:
        coords = PCA(n_components=2, random_state=42).fit_transform(Xs)
        points = [
            {"x": clean_float(coords[i, 0]), "y": clean_float(coords[i, 1]), "cluster": int(labels[i])}
            for i in range(len(coords))
        ]

    return {
        "n_clusters": int(n_clusters),
        "silhouette": sil,
        "silhouette_by_k": silhouettes,
        "features": [m["title"] for m in numeric_meta],
        "clusters": clusters,
        "scatter": points,
        "interpretation": (
            f"{n_clusters} segment bulundu (silhouette={sil}). "
            "Her segmentin ortalama profili aşağıdadır."
        ),
    }
