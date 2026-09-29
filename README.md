# 📊 FormStat — Survey & Statistical Analysis App

🇹🇷 [Türkçe README](README.tr.md)

Build a survey, collect responses, and get a **full statistical analysis** in one place. FormStat picks the right test for each pair of variables, runs regression and segmentation, and turns the results into interactive charts and plain-language insights.

It works end to end on its own (CSV import and manual entry), and can optionally publish forms to **Google Forms** and pull responses back.

- **Backend:** FastAPI (Python), SQLite, pandas, SciPy, statsmodels, scikit-learn
- **Frontend:** React, TypeScript, Vite, Recharts
- **Deployment:** single Docker container (API + built frontend), one-click Render blueprint

---

## Features

| Area | What it does |
|------|--------------|
| **Form builder** | 9 question types: short/long text, single/multiple choice, dropdown, rating scale, number, date, email |
| **Response collection** | CSV import with a column-to-question mapping wizard, manual entry, Google Forms sync |
| **Descriptive statistics** | Mean, median, mode, standard deviation, quartiles, skewness/kurtosis, histograms, frequency tables |
| **Inferential statistics** | Chi-square (+ Cramér's V), t-test (+ Cohen's d), ANOVA (+ Tukey HSD), Pearson/Spearman correlation, with **automatic test selection** based on variable types |
| **Cross-tabulation** | Heatmap pivot of two categorical variables with a chi-square test |
| **Regression** | Linear (numeric target) and logistic (binary target): coefficient table, p-values, R² / pseudo-R² |
| **Segmentation** | K-means with automatic cluster count (silhouette score), PCA visualization, segment profiles |
| **Automatic insights** | Scans for significant relationships and flags distribution and data-quality issues |
| **Export** | Download responses as a wide-format CSV |

All statistics are computed on the backend; the frontend only visualizes the results.

---

## Quick start

Requirements: **Python 3.10+** and **Node.js 18+**.

```bash
cd formstat
./run.sh
```

Then open **http://localhost:5173**. Dependencies are installed automatically on the first run.

### Manual setup

```bash
# Backend (:8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (:5173), in a separate terminal
cd frontend
npm install
npm run dev
```

Interactive API docs: **http://localhost:8000/docs**

### Docker

```bash
docker build -t formstat .
docker run -p 8000:8000 formstat
# http://localhost:8000
```

The container serves both the API and the built React app, and starts with demo data (`SEED_DEMO=1`).

---

## Deploying a live demo

The repo includes a `render.yaml` blueprint:

1. On [render.com](https://render.com), choose **New → Blueprint** and select this repository.
2. Render builds the Dockerfile and gives you a public URL.
3. The free tier sleeps when idle, so the first request can take about a minute.

Railway and Fly.io also work with the included `Dockerfile`. Serverless platforms such as Vercel are not a good fit, because the backend needs heavy scientific libraries and a persistent process.

---

## How to use

> The interface is currently in Turkish. Button names below are given in English with the Turkish label in parentheses.

1. **Create a form:** New Form (*Yeni Form*) → add questions → Save (*Kaydet*).
2. **Collect responses** on the Responses tab:
   - import `sample_responses.csv` with **CSV import** (columns are mapped automatically), or
   - enter responses manually, or
   - **sync from Google** if the form was exported to Google Forms.
3. **Analyze** on the Analysis tab: charts, tests, regression, segmentation and automatic insights.

The app ships with a sample "Customer Satisfaction Survey" (40 responses), so you can try the analysis right away. Delete `data/formstat.db` to start fresh.

---

## Google Forms integration (optional)

To create real Google Forms from the app and pull their responses, a one-time Google Cloud setup is needed:

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project.
2. **APIs & Services → Library:** enable the **Google Forms API**.
3. **OAuth consent screen:** choose **External**, set an app name, and add your Google account under **Test users**.
4. **Credentials → Create Credentials → OAuth client ID**, application type **Desktop app**.
5. Download the client JSON and save it as `data/client_secret.json`.
6. Restart the app and click **Connect to Google** (*Google'a Bağlan*, top right).
7. On a form, choose **Edit → Export to Google Forms**, share the response link, then use **Responses → Sync from Google** as answers arrive.

Scopes used: `forms.body` (create/update) and `forms.responses.readonly` (read responses).

> Forms created through the API after 30 June 2026 are unpublished by default. FormStat publishes them automatically right after creation via `setPublishSettings`.

---

## Project structure

```
formstat/
├── backend/app/
│   ├── main.py            # FastAPI app, CORS, table creation
│   ├── models.py          # Form, Question, Response, Answer
│   ├── routers/           # forms, responses, analysis, reports, google
│   └── services/
│       ├── google_forms.py    # OAuth, export, sync
│       ├── importers.py       # CSV import
│       └── stats/             # descriptive, inferential, regression, segmentation, insights
├── frontend/src/
│   ├── pages/             # FormsList, FormBuilder, ResponsesPage, AnalysisDashboard
│   └── components/        # charts, analysis views, GoogleConnect, FormHeader
├── data/                  # SQLite DB, temp imports, Google credentials (git-ignored)
├── sample_responses.csv   # sample file for CSV import
├── Dockerfile / render.yaml
└── run.sh
```

---

## Privacy

All data stays local in `data/formstat.db`. Nothing is sent anywhere except during Google sync, and only for forms you have authorized.
