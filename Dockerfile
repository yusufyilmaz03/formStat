# FormStat — tek konteyner: React arayüzü derlenir, FastAPI hem API'yi hem arayüzü sunar.
# Render / Railway / Fly / Hugging Face Spaces gibi Docker destekleyen her yerde çalışır.

# ---- Aşama 1: frontend derle ----
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
# npm install (npm ci değil): lock dosyası macOS'ta üretildiği için Linux'ta
# platforma özgü native binary'leri güvenle çözer
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- Aşama 2: backend + sunum ----
FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SEED_DEMO=1

# scikit-learn / scipy çalışma zamanı için OpenMP
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend /app/frontend/dist frontend/dist

WORKDIR /app/backend
EXPOSE 8000
# PORT ortam değişkeni (Render/Railway/Fly bunu ayarlar); yoksa 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
