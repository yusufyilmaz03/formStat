#!/usr/bin/env bash
# FormStat — backend (FastAPI, :8000) + frontend (Vite, :5173) birlikte başlatır.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ Backend hazırlanıyor…"
cd "$ROOT/backend"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACK=$!

echo "▶ Frontend hazırlanıyor…"
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then npm install; fi
npm run dev &
FRONT=$!

trap 'echo; echo "Kapatılıyor…"; kill $BACK $FRONT 2>/dev/null' EXIT INT TERM

echo ""
echo "✅ FormStat çalışıyor:"
echo "   • Uygulama : http://localhost:5173"
echo "   • API      : http://localhost:8000  (dokümantasyon: /docs)"
echo "   Durdurmak için Ctrl+C."
wait
