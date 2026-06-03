# PharmaAgent AI — Setup Guide for a New Machine

> **Estimated setup time:** 10–15 minutes  
> **Requirements:** Python 3.11+, Node.js 20+, PostgreSQL 14+ (or skip with SQLite)

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [API Keys You Need](#3-api-keys-you-need)
4. [Backend Setup (FastAPI)](#4-backend-setup-fastapi)
5. [Frontend Setup (Next.js)](#5-frontend-setup-nextjs)
6. [Running the System](#6-running-the-system)
7. [Default Login Credentials](#7-default-login-credentials)
8. [Verify Everything Works](#8-verify-everything-works)
9. [Database Options (PostgreSQL vs SQLite)](#9-database-options-postgresql-vs-sqlite)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

Install these tools before starting:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11 or 3.12 | https://www.python.org/downloads/ |
| Node.js | 20 LTS | https://nodejs.org/ |
| PostgreSQL | 14+ | https://www.postgresql.org/download/ |
| Git | any | https://git-scm.com/ |

> **Shortcut (SQLite):** You can skip PostgreSQL and use SQLite for local dev. See [Section 9](#9-database-options-postgresql-vs-sqlite).

---

## 2. Clone the Repository

```bash
git clone https://github.com/your-username/pharmaagent-ai.git
cd pharmaagent-ai
```

---

## 3. API Keys You Need

### 3.1 Google Gemini API Key (Required)

The AI agent, symptom checker, and vision features all use Gemini.

1. Go to: https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Copy the key — it starts with `AIza...`

### 3.2 LangSmith API Key (Required for observability, optional for basic use)

LangSmith traces all LangChain/LangGraph agent calls. You can disable it by setting `LANGCHAIN_TRACING_V2=false`.

1. Go to: https://smith.langchain.com
2. Sign up for free
3. Click your avatar → **Settings** → **API Keys** → **Create API Key**
4. Copy the key — it starts with `lsv2_...`

---

## 4. Backend Setup (FastAPI)

### 4.1 Create a virtual environment

```bash
cd backend

# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 4.3 Create the `.env` file

Copy the example and fill in your values:

```bash
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
```

Then edit `backend/.env`:

```env
# ─── DATABASE ─────────────────────────────────────────────────────────────────
# Option A: PostgreSQL (recommended for production)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/pharmaagent

# Option B: SQLite (easier for dev — no PostgreSQL needed)
# DATABASE_URL=sqlite:///./pharmaagent.db

# ─── SECURITY ─────────────────────────────────────────────────────────────────
JWT_SECRET=change-this-to-a-random-32-char-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ─── GOOGLE GEMINI AI ─────────────────────────────────────────────────────────
GEMINI_API_KEY=AIzaSy...your-gemini-key-here

# ─── LANGSMITH OBSERVABILITY ──────────────────────────────────────────────────
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=lsv2_pt_...your-langsmith-key-here
LANGCHAIN_PROJECT=pharmaagent-ai

# ─── APP SETTINGS ─────────────────────────────────────────────────────────────
APP_ENV=development
CORS_ORIGINS=http://localhost:3000
UPLOAD_DIR=uploads
```

> **Note:** The project uses `LANGSMITH_API_KEY` (not `LANGCHAIN_API_KEY`). This is the correct variable name.

### 4.4 Create the PostgreSQL database (skip for SQLite)

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE pharmaagent;
\q
```

### 4.5 Start the backend

```bash
# Make sure your venv is active
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# On macOS/Linux:
python -m uvicorn app.main:app --reload --port 8000
```

On first startup, the backend automatically:
- Creates all database tables
- Seeds 10 medicines (7 OTC + 3 Rx)
- Creates the admin, pharmacist, and demo user accounts

---

## 5. Frontend Setup (Next.js)

### 5.1 Install Node.js dependencies

```bash
cd frontend
npm install
```

### 5.2 Configure environment

The `frontend/.env.local` file should already exist. Verify it contains:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If the file doesn't exist, create it with the above content.

### 5.3 Start the frontend

```bash
npm run dev
```

The frontend runs on http://localhost:3000 by default.

---

## 6. Running the System

Start both servers in **separate terminal windows**:

**Terminal 1 — Backend:**
```bash
cd backend
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS/Linux
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Then open: **http://localhost:3000**

---

## 7. Default Login Credentials

These accounts are created automatically on first start:

| Role | Email | Password | Access |
|------|-------|----------|--------|
| **Admin** | admin@pharmaagent.com | admin123 | Full admin dashboard, analytics |
| **Pharmacist** | pharmacist@pharmaagent.com | pharma123 | Prescription approval, inventory |
| **Demo User** | john@example.com | user123 | Chat, orders, symptom checker |

> **Security:** Change these passwords before deploying to production.

---

## 8. Verify Everything Works

### Check backend health:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"PharmaAgent AI Backend",...}
```

### Check API documentation:
Open: http://localhost:8000/docs *(Swagger UI)*

### Run tests:
```bash
cd backend
.\venv\Scripts\activate
pytest tests/ -v
```

### Expected test output:
```
tests/test_symptom_agent.py::test_red_flag_detection_chest_pain PASSED
tests/test_symptom_agent.py::test_no_red_flag_for_normal_symptoms PASSED
...
```

---

## 9. Database Options (PostgreSQL vs SQLite)

### Option A: PostgreSQL (default, recommended)

Requires PostgreSQL installed. Better for teams, production use, and if you need the full feature set.

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/pharmaagent
```

### Option B: SQLite (zero-config, dev only)

No installation needed. Great for quick local testing. Just change one line in `backend/.env`:

```env
DATABASE_URL=sqlite:///./pharmaagent.db
```

SQLite is auto-detected by the app — no code changes needed.

---

## 10. Troubleshooting

### ❌ Backend fails with `connection refused` (PostgreSQL)

Make sure PostgreSQL is running and you created the `pharmaagent` database:
```bash
pg_ctl start                    # Linux/macOS
net start postgresql-x64-14    # Windows (adapt version)
```

### ❌ `GEMINI_API_KEY` not found / invalid

Double-check `backend/.env` has a valid key (starts with `AIza...`). Get a new key at https://aistudio.google.com/app/apikey

### ❌ LangSmith traces not appearing

Make sure `LANGSMITH_API_KEY` (not `LANGCHAIN_API_KEY`) is set in `backend/.env`. The key should start with `lsv2_...`.

### ❌ Frontend error: `Failed to connect to backend`

Ensure the backend is running on port 8000 and `frontend/.env.local` has:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### ❌ Port 3000 or 8000 already in use

```bash
# Find and kill the process using the port (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :3000
kill -9 <PID>
```

### ❌ `psycopg2` install failure on Windows

Install the binary version:
```bash
pip install psycopg2-binary
```

---

## 📂 Project Structure

```
pharmaagent-ai/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── agents/           # LangGraph AI agents (pharmacy, symptom, voice, vision)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── routes/           # FastAPI route handlers
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic services
│   │   ├── utils/            # Security, seed data, retry utilities
│   │   ├── constants/        # Language config
│   │   ├── config.py         # Pydantic settings (reads .env)
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   └── main.py           # FastAPI app entry point
│   ├── tests/                # pytest test suite
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Your local environment variables
└── frontend/                 # Next.js 16 + TypeScript + Tailwind
    ├── app/                  # Next.js App Router pages
    ├── components/           # React components
    ├── lib/                  # API client, auth utilities
    ├── .env.local            # Frontend environment variables
    └── package.json
```

---

## 🔑 API Keys Summary

| Service | Variable Name | Where to Get |
|---------|--------------|--------------|
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |
| LangSmith | `LANGSMITH_API_KEY` | https://smith.langchain.com → Settings → API Keys |

Both services have **free tiers** that are sufficient for development and demos.
