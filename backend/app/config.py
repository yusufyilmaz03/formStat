"""Uygulama ayarları. Tüm yollar makul varsayılanlarla gelir; .env ile ezilebilir."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend/ -> formstat/
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{DATA_DIR / 'formstat.db'}"
    frontend_origin: str = "http://localhost:5173"
    # Prod'da derlenmiş React arayüzünün yolu (boşsa ../frontend/dist denenir)
    frontend_dist: str = ""

    # Google OAuth (Faz 6)
    google_client_secret_file: str = str(DATA_DIR / "client_secret.json")
    google_token_file: str = str(DATA_DIR / "google_token.json")
    oauth_redirect_uri: str = "http://localhost:8000/api/google/callback"
    google_scopes: list[str] = [
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.responses.readonly",
    ]


settings = Settings()
