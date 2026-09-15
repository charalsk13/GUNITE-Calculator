# GUNITE Calculator — Online v8

## Changes in v8

## Deploy

# Online deployment

The modern application is deployed as two services:

```text
Vercel  -> frontend/ (Vite + React)
Render  -> backend/api.py (FastAPI)
```

The legacy `app.py` Streamlit application remains available for local use, but it is not the Vercel entry point.

## 1. Deploy the backend on Render

Create a new **Web Service** from the GitHub repository, or use the repository's `render.yaml` blueprint.

The important settings are:

```text
Runtime:       Python
Build command: pip install -r requirements-modern.txt
Start command: uvicorn backend.api:app --host 0.0.0.0 --port $PORT
Health check:  /api/health
```

After deployment, verify that this URL returns a healthy response:

```text
https://YOUR-RENDER-SERVICE.onrender.com/api/health
```

## 2. Deploy the frontend on Vercel

Create a Vercel project from the same repository and set:

```text
Root Directory:   frontend
Framework Preset: Vite
Build command:    npm run build
Output directory: dist
```

Add this Vercel environment variable for the production environment:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

The frontend reads this value at build time. Redeploy Vercel after adding or changing it.

This repository contains both a root `vercel.json` fallback and `frontend/vercel.json`. If the Vercel project currently shows `Root Directory: ./`, the root configuration runs the Vite build from `frontend/`. With the preferred `Root Directory: frontend`, the frontend configuration uses `npm run build` and output directory `dist`.

Do not configure Vercel as a Python deployment for this setup. In particular, do not use a root-level `pyproject.toml` entrypoint for the frontend project: that would make Vercel inspect the legacy `app.py` path again. The FastAPI entry point belongs to Render and is `backend/api.py`, variable `app`.

## Local development

Backend:

```text
uvicorn backend.api:app --reload --port 8000
```

Frontend:

```text
cd frontend
npm install
npm run dev
```

Without `VITE_API_URL`, the frontend uses `http://127.0.0.1:8000` for local development.
