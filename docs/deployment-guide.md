---
output:
  html_document: default
  pdf_document: default
---

# Deployment Guide

MockStar runs across three cloud services: **Cloud Run** (FastAPI backend), **Cloud SQL** (PostgreSQL), and **Vercel** (Next.js frontend). This guide covers a production deployment from scratch.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| `gcloud` CLI | Cloud Run and Cloud SQL provisioning |
| `vercel` CLI | Frontend deployment |
| Google Cloud project with billing enabled | Backend + database |
| Google OAuth credentials | NextAuth sign-in |
| OpenAI API key | Whisper transcription |
| Google AI API key | Gemini 2.5 Flash |

---

## 1. Cloud SQL — PostgreSQL Database

### Create the instance

```bash
gcloud sql instances create mockstar-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-auto-increase
```

### Create the database and user

```bash
gcloud sql databases create mockstar --instance=mockstar-db

gcloud sql users create mockstar_user \
  --instance=mockstar-db \
  --password=YOUR_DB_PASSWORD
```

### Get the connection name

```bash
gcloud sql instances describe mockstar-db --format="value(connectionName)"
# e.g. your-project:us-central1:mockstar-db
```

---

## 2. Backend — Cloud Run

### Create a `Dockerfile` at the repo root

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

> The `libgl1-mesa-glx` and `libglib2.0-0` packages are required by OpenCV.

### Build and push the image

```bash
gcloud builds submit \
  --tag gcr.io/YOUR_PROJECT_ID/mockstar-backend
```

### Deploy to Cloud Run

```bash
gcloud run deploy mockstar-backend \
  --image gcr.io/YOUR_PROJECT_ID/mockstar-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT:us-central1:mockstar-db \
  --set-env-vars \
    OPENAI_API_KEY=YOUR_OPENAI_KEY,\
    GOOGLE_API_KEY=YOUR_GOOGLE_AI_KEY,\
    DATABASE_URL=postgresql+asyncpg://mockstar_user:YOUR_DB_PASSWORD@/mockstar?host=/cloudsql/YOUR_PROJECT:us-central1:mockstar-db
```

Note the `DATABASE_URL` format for Cloud SQL Unix socket connections — the host is `/cloudsql/<connection-name>` rather than a TCP hostname.

### Run Alembic migrations

After the first deploy, run migrations against Cloud SQL using the Cloud SQL Auth Proxy:

```bash
# Download and start the proxy
cloud-sql-proxy YOUR_PROJECT:us-central1:mockstar-db &

# Run migrations (in a local virtualenv with requirements installed)
DATABASE_URL="postgresql+asyncpg://mockstar_user:YOUR_DB_PASSWORD@localhost:5432/mockstar" \
  alembic upgrade head
```

---

## 3. Frontend — Vercel

### Install the Vercel CLI and deploy

```bash
cd frontend
npm install -g vercel
vercel --prod
```

Vercel auto-detects Next.js and configures the build. Set the following environment variables in the Vercel project dashboard (or via `vercel env add`):

| Variable | Value |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `AUTH_SECRET` | Random secret (generate with `openssl rand -base64 32`) |
| `NEXT_PUBLIC_API_URL` | Cloud Run service URL (e.g. `https://mockstar-backend-xyz-uc.a.run.app`) |

### Update the OAuth redirect URI

In Google Cloud Console → APIs & Services → Credentials, add the Vercel deployment URL to **Authorised redirect URIs**:

```
https://your-app.vercel.app/api/auth/callback/google
```

---

## 4. Environment Variables Reference

### Backend (`.env` at repo root)

```env
OPENAI_API_KEY=           # OpenAI — Whisper transcription
GOOGLE_API_KEY=           # Google AI Studio — Gemini 2.5 Flash
DATABASE_URL=             # postgresql+asyncpg://user:password@host:5432/mockstar
```

### Frontend (`frontend/.env.local`)

```env
GOOGLE_CLIENT_ID=         # Google OAuth client ID
GOOGLE_CLIENT_SECRET=     # Google OAuth client secret
AUTH_SECRET=              # Random secret for NextAuth session signing
NEXT_PUBLIC_API_URL=      # Backend base URL (no trailing slash)
```

---

## 5. Local Development

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations (requires a local PostgreSQL instance or Cloud SQL Proxy)
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:3000` and expects the backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

---

## 6. Health Check

Once deployed, verify the backend is running:

```bash
curl https://your-backend.run.app/docs
```

FastAPI's auto-generated Swagger UI should load. If it does, the service is up and all routes are registered.
