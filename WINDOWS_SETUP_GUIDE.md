# PharmaAgent AI — Windows Setup Guide

**Step-by-step procedure to run the project on Windows, including common problems and solutions.**

---

## Table of Contents

1. [Requirements Summary](#1-requirements-summary)
2. [Software to Install](#2-software-to-install)
3. [API Keys & Logins Needed](#3-api-keys--logins-needed)
4. [Step-by-Step Setup](#4-step-by-step-setup)
5. [Running the Project](#5-running-the-project)
6. [Verification](#6-verification)
7. [Common Problems & Solutions](#7-common-problems--solutions)

---

## 1. Requirements Summary

| Category | What You Need |
|----------|---------------|
| **Software** | Python 3.11+, Node.js 18+, npm 9+, Git |
| **Database** | PostgreSQL 14+ **OR** SQLite (no install needed) |
| **APIs** | Google Gemini API key (required for AI features) |
| **Optional** | LangSmith API key (for AI trace observability) |
| **Accounts** | Google account (for Gemini), LangSmith account (optional) |

---

## 2. Software to Install

### 2.1 Python 3.11 or higher

- **Download:** https://www.python.org/downloads/
- **Check:** Open PowerShell and run `python --version` (or `py --version`)
- **Important:** During installation, check **"Add Python to PATH"**

### 2.2 Node.js 18 or higher

- **Download:** https://nodejs.org/ (LTS version recommended)
- **Check:** `node --version` and `npm --version`

### 2.3 Git

- **Download:** https://git-scm.com/download/win
- **Check:** `git --version`

### 2.4 Database (Choose One)

**Option A: SQLite (Easiest — No Installation)**

- SQLite works out of the box with Python
- Use `DATABASE_URL=sqlite:///./pharmaagent.db` in `.env`
- **Recommended for quick local development**

**Option B: PostgreSQL (Production-like)**

- **Download:** https://www.postgresql.org/download/windows/
- Install with default settings
- Remember the password you set for the `postgres` user
- Create database: `CREATE DATABASE pharmaagent;` (via pgAdmin or psql)

---

## 3. API Keys & Logins Needed

### 3.1 Google Gemini API Key (Required for AI features)

- **Website:** https://aistudio.google.com/app/apikey
- **Login:** Google account
- **Steps:**
  1. Sign in with Google
  2. Click **"Create API Key"**
  3. Copy the key (starts with `AIza...`)
  4. Paste into `backend/.env` as `GEMINI_API_KEY=your-key-here`
- **Free tier:** Sufficient for development and demos

### 3.2 LangSmith API Key (Optional — for AI trace observability)

- **Website:** https://smith.langchain.com
- **Login:** Create free account
- **Steps:**
  1. Sign up / Log in
  2. Go to **Settings → API Keys → Create API Key**
  3. Copy the key
  4. Add to `backend/.env`:
     ```
     LANGCHAIN_TRACING_V2=true
     LANGCHAIN_API_KEY=ls__your-key-here
     LANGCHAIN_PROJECT=pharmaagent-ai
     ```
- **To skip:** Set `LANGCHAIN_TRACING_V2=false` in `.env`

### 3.3 No Other Logins Required

- No payment or credit card needed for Gemini free tier
- No other external services required for basic operation

---

## 4. Step-by-Step Setup

### Step 4.1 — Clone or Navigate to Project

```powershell
cd d:\WORK\pharmaagent-ai
# Or: git clone https://github.com/Rahil-dope/pharmaagent-ai.git
#     cd pharmaagent-ai
```

### Step 4.2 — Backend Setup

```powershell
cd backend
```

**Create virtual environment:**

```powershell
python -m venv venv
```

**Activate virtual environment (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

> If you get an execution policy error, run first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Install dependencies:**

```powershell
pip install -r requirements.txt
```

### Step 4.3 — Configure Backend Environment

**Copy the example env file:**

```powershell
copy .env.example .env
```

**Edit `backend/.env`** with a text editor. Minimum required:

```env
# Database — Use SQLite (no PostgreSQL needed):
DATABASE_URL=sqlite:///./pharmaagent.db

# Or for PostgreSQL:
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/pharmaagent

# Security — Change this to a random string:
JWT_SECRET=your-super-secret-jwt-key-change-this

# Google Gemini — REQUIRED for chat, symptom checker, vision:
GEMINI_API_KEY=your-actual-gemini-api-key

# LangSmith — Optional (set false to skip):
LANGCHAIN_TRACING_V2=false
```

### Step 4.4 — Frontend Setup

Open a **new** PowerShell window:

```powershell
cd d:\WORK\pharmaagent-ai\frontend
```

**Install dependencies:**

```powershell
npm install
```

**Create frontend env file:**

```powershell
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
```

Or create `frontend/.env.local` manually with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 5. Running the Project

You need **two terminals** running at the same time.

### Terminal 1 — Backend

```powershell
cd d:\WORK\pharmaagent-ai\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2 — Frontend

```powershell
cd d:\WORK\pharmaagent-ai\frontend
npm run dev
```

**Expected output:**
```
▲ Next.js 16.x.x
- Local:        http://localhost:3000
✓ Ready in Xms
```

### Open in Browser

- **App:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 6. Verification

1. **Backend health:** Visit http://localhost:8000/health — should return `{"status":"healthy"}`
2. **Frontend:** Visit http://localhost:3000 — should show login page
3. **Login as admin:** `admin@pharmaagent.com` / `admin123`
4. **Login as pharmacist:** `pharmacist@pharmaagent.com` / `pharma123`
5. **Register:** Create a new user at http://localhost:3000/register

---

## 7. Common Problems & Solutions

### ❌ `venv\Scripts\Activate.ps1` — Execution Policy Error

**Error:** "Running scripts is disabled on this system"

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Alternative:** Use Command Prompt instead:
```cmd
venv\Scripts\activate.bat
```

---

### ❌ `python` or `pip` not found

**Fix:** Use `py` instead of `python`:
```powershell
py -m venv venv
py -m pip install -r requirements.txt
```

Or add Python to PATH during reinstallation.

---

### ❌ `ModuleNotFoundError: No module named 'email_validator'`

**Fix:**
```powershell
pip install email-validator
# Or: pip install "pydantic[email]"
```

---

### ❌ Database connection failed / `psycopg2.OperationalError`

**Cause:** Using PostgreSQL but it's not running or credentials are wrong.

**Fix (Option 1 — Switch to SQLite):**
In `backend/.env`:
```
DATABASE_URL=sqlite:///./pharmaagent.db
```

**Fix (Option 2 — Use PostgreSQL):**
1. Start PostgreSQL service (Services → postgresql)
2. Verify: `psql -U postgres -d pharmaagent -c "SELECT 1;"`
3. Check `DATABASE_URL` in `.env` has correct password

---

### ❌ Port 8000 already in use

**Find process:**
```powershell
netstat -ano | findstr :8000
```

**Kill process (replace PID with actual number):**
```powershell
taskkill /PID <PID_NUMBER> /F
```

**Or use different port:**
```powershell
uvicorn app.main:app --reload --port 8001
```
Then update `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8001`

---

### ❌ Port 3000 already in use

**Fix:**
```powershell
npm run dev -- --port 3001
```

---

### ❌ GEMINI_API_KEY not set / Invalid API key

**Cause:** AI features (chat, symptom checker, vision) require a valid Gemini key.

**Fix:**
1. Get key from https://aistudio.google.com/app/apikey
2. Add to `backend/.env`: `GEMINI_API_KEY=AIza...`
3. Restart backend server

**Note:** With invalid/dummy key, chat and AI features will fail with API errors.

---

### ❌ `pip install` fails for `psycopg2-binary` (PostgreSQL)

**Fix:**
```powershell
pip install psycopg2-binary --only-binary :all:
```

Or use SQLite to avoid PostgreSQL entirely.

---

### ❌ Frontend shows "Failed to fetch" or API errors

**Causes:**
- Backend not running
- Wrong API URL

**Fix:**
1. Ensure backend is running on port 8000
2. Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Restart frontend after changing `.env.local`

---

### ❌ Voice recording not working

**Cause:** Web Speech API needs microphone permission and a supported browser.

**Fix:**
- Use Chrome or Edge (Firefox has limited support)
- Allow microphone when prompted
- HTTPS required in production (HTTP works on localhost)

---

### ❌ `npm install` or `npm run dev` fails

**Fix:**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules, .next -ErrorAction SilentlyContinue
npm install
npm run dev
```

---

## 8. Default Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@pharmaagent.com` | `admin123` |
| Pharmacist | `pharmacist@pharmaagent.com` | `pharma123` |
| User | Register at `/register` | Your choice |

---

## 9. Quick Reference — Run Commands

```powershell
# Terminal 1 — Backend
cd d:\WORK\pharmaagent-ai\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd d:\WORK\pharmaagent-ai\frontend
npm run dev
```

**Then open:** http://localhost:3000

---

*Document created after successful project setup on Windows. Last updated: March 2025.*
