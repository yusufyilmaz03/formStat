"""FastAPI uygulama girişi: CORS, tablo oluşturma, router'lar, (prod) statik frontend."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (tabloların kaydı için import gerekli)
from .config import settings
from .database import Base, engine
from .routers import analysis, forms, google, reports, responses
from .seed import seed_if_empty

# Tabloları oluştur (yoksa) ve demo verisini tohumla (boşsa)
Base.metadata.create_all(bind=engine)
seed_if_empty()

app = FastAPI(title="FormStat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "app": "FormStat"}


app.include_router(forms.router)
app.include_router(responses.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(google.router)


# ---- Prod: derlenmiş React arayüzünü aynı origin'den sun (frontend/dist varsa) ----
# backend/app/main.py -> backend/ -> proje kökü -> frontend/dist
FRONTEND_DIST = Path(
    settings.frontend_dist or (Path(__file__).resolve().parent.parent.parent / "frontend" / "dist")
)

if FRONTEND_DIST.is_dir():
    if (FRONTEND_DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        # API yolları buraya düşmez (yukarıda eşleşir); güvenlik için 404
        if full_path.startswith("api/"):
            raise HTTPException(404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")  # SPA fallback
