"""CSV içe aktarma: geçici yükleme, önizleme ve sütun->soru eşlemesiyle kayıt."""
from __future__ import annotations

import io
import uuid

import pandas as pd

from ..config import DATA_DIR

IMPORT_DIR = DATA_DIR / "imports"
IMPORT_DIR.mkdir(parents=True, exist_ok=True)


def _read_csv(raw: bytes) -> pd.DataFrame:
    """CSV'yi esnek şekilde okur (virgül/nokta-virgül, UTF-8/Latin-1)."""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=sep, encoding=encoding, dtype=str)
                if df.shape[1] > 1 or sep == "\t":
                    return df.fillna("")
            except Exception:
                continue
    # Son çare
    return pd.read_csv(io.BytesIO(raw), dtype=str).fillna("")


def save_upload_preview(raw: bytes, sample_rows: int = 5) -> dict:
    """Yüklenen CSV'yi geçici saklar; sütunları ve örnek satırları döner."""
    df = _read_csv(raw)
    import_id = uuid.uuid4().hex
    # Kendi yazıp okuduğumuz için sabit format (virgül, UTF-8) — pyarrow gerektirmez
    df.to_csv(IMPORT_DIR / f"{import_id}.csv", index=False, encoding="utf-8")
    return {
        "import_id": import_id,
        "columns": list(df.columns),
        "row_count": int(len(df)),
        "sample": df.head(sample_rows).to_dict(orient="records"),
    }


def load_import(import_id: str) -> pd.DataFrame:
    path = IMPORT_DIR / f"{import_id}.csv"
    if not path.exists():
        raise FileNotFoundError("İçe aktarma dosyası bulunamadı veya süresi doldu.")
    return pd.read_csv(path, dtype=str, encoding="utf-8").fillna("")


def cleanup_import(import_id: str) -> None:
    path = IMPORT_DIR / f"{import_id}.csv"
    if path.exists():
        path.unlink()
