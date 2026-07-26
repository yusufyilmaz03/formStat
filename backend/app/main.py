"""FastAPI uygulama girişi: CORS, tablo oluşturma, router'lar."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (tabloların kaydı için import gerekli)
from .config import settings
from .database import Base, engine
from .routers import analysis, forms, google, reports, responses

# Tabloları oluştur (yoksa)
Base.metadata.create_all(bind=engine)

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
