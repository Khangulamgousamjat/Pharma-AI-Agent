# PharmaAgent AI — Complete Setup Guide

---

## ⚡ Quick Start (Summary)

> Already know what you're doing? Here's the TL;DR:

```bash
# 1. Clone
git clone <https://github.com/Rahil-dope/pharmaagent-ai.git>
cd pharmaagent-ai

# 2. Backend
cd backend && python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env                                          # Fill in keys
cd ..

# 3. Frontend
cd frontend && npm install
# Create frontend/.env.local with: NEXT_PUBLIC_API_URL=http://localhost:8000

# 4. Run (in two separate terminals)
# Terminal 1:  cd backend  && uvicorn app.main:app --reload --port 8000
# Terminal 2:  cd frontend && npm run dev

# 5. Open http://localhost:3000
# Admin login: admin@pharmaagent.com / admin123
```

---

## 1. Project Overview

**PharmaAgent AI** is an autonomous, multi-agent pharmacy system powered by AI. It allows users to:

- 💬 **Chat naturally** to order medicines ("I need paracetamol 10 tablets")
- 📸 **Upload prescriptions** for AI-powered OCR verification
- 🩺 **Check symptoms** with an AI triage assistant
- 🎙 **Speak** their request using voice input
- 🌐 **Converse in Hindi, Marathi, or English**
- 📊 **See refill predictions** before they run out of medicine

Pharmacists can approve prescriptions. Admins manage inventory, view analytics dashboards, and monitor fulfillment webhooks — all with full **LangSmith observability** over every AI decision.

**Tech Stack:**
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, Recharts |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL |
| AI Model | Google Gemini 2.0 Flash |
| Agent Framework | LangChain (ReAct agents) |
| Observability | LangSmith |
| Auth | JWT (python-jose + bcrypt) |

---

## 2. System Requirements

Make sure you have the following installed before starting:

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Python | 3.11 | `python --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| PostgreSQL | 14 | `psql --version` |
| Git | any | `git --version` |

> **Windows users:** If `python` doesn't work, try `py` or `python3`.
> **Mac/Linux users:** Use `python3` and `pip3` where `python` and `pip` are specified.

---

## 3. Clone the Repository

```bash
git clone <https://github.com/Rahil-dope/pharmaagent-ai.git>
cd pharmaagent-ai
```

You will see this folder structure:

```
pharmaagent-ai/
│
├── backend/            ← FastAPI server (Python)
│   ├── app/
│   │   ├── main.py          ← Entry point, all routers registered here
│   │   ├── config.py        ← All settings (loaded from .env)
│   │   ├── database.py      ← PostgreSQL connection
│   │   ├── models/          ← SQLAlchemy DB models
│   │   ├── schemas/         ← Pydantic request/response schemas
│   │   ├── routes/          ← All API endpoint files
│   │   ├── agents/          ← LangChain AI agents
│   │   ├── services/        ← Business logic (analytics, webhooks, voice)
│   │   └── utils/           ← JWT, bcrypt, seed data, retries
│   ├── tests/               ← pytest unit tests
│   ├── requirements.txt     ← Python dependencies
│   └── .env.example         ← Template for environment variables
│
├── frontend/           ← Next.js app (TypeScript)
│   ├── app/
│   │   ├── login/, register/, dashboard/
│   │   ├── chat/            ← AI pharmacy chat
│   │   ├── voice/           ← Voice input chat
│   │   ├── vision/          ← Prescription scanner
│   │   ├── symptom/         ← Symptom checker
│   │   ├── analytics/       ← Admin analytics dashboard
│   │   ├── pharmacist/      ← Pharmacist dashboard
│   │   ├── admin/           ← Admin inventory
│   │   └── settings/        ← User preferences
│   ├── components/          ← Shared UI components
│   ├── lib/                 ← API client (api.ts) and auth helpers
│   └── .env.example         ← Template for frontend env vars
│
└── docs/               ← Architecture and API documentation
```

---

## 4. Backend Setup (FastAPI)

### Step 4.1 — Navigate to backend folder

```bash
cd backend
```

### Step 4.2 — Create a Python virtual environment

A virtual environment isolates this project's Python packages from your system.

```bash
python -m venv venv
```

### Step 4.3 — Activate the virtual environment

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

> ✅ You'll see `(venv)` at the start of your terminal prompt when activated.

### Step 4.4 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy, LangChain, Google Gemini, LangSmith, bcrypt, and all other backend dependencies.

> ⏳ This takes 1–3 minutes. Please wait for it to complete.

---

## 5. PostgreSQL Database Setup

### Step 5.1 — Install PostgreSQL

**Windows:** Download the installer from https://www.postgresql.org/download/windows/
- Use default settings
- Set a password for the `postgres` user (remember this!)
- Default port: `5432`

**Mac (Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql
sudo systemctl start postgresql
```

### Step 5.2 — Create the database

Open the PostgreSQL shell:

**Windows:** Open "pgAdmin" (installed with PostgreSQL) or search "SQL Shell (psql)" in Start Menu.

**Mac/Linux:**
```bash
psql -U postgres
```

Then run these commands in the PostgreSQL shell:

```sql
CREATE DATABASE pharmaagent;
\q
```

> ✅ You should see `CREATE DATABASE` confirmation.

### Step 5.3 — Verify connection

```bash
psql -U postgres -d pharmaagent -c "SELECT 1;"
```

If this prints `1`, your database is working.

---

## 6. Environment Variables (Backend)

### Step 6.1 — Create your `.env` file

Copy the example file:

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

### Step 6.2 — Edit the `.env` file

Open `backend/.env` in any text editor (Notepad, VS Code, etc.) and fill in:

```env
# ── Database ────────────────────────────────────────────────────────────────
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/pharmaagent

# ── Security ─────────────────────────────────────────────────────────────────
# Any random string of 32+ characters (keep this secret!)
JWT_SECRET=change-this-to-any-long-random-string-abc123xyz
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ── Google Gemini AI ─────────────────────────────────────────────────────────
GEMINI_API_KEY=your-gemini-api-key-here

# ── LangSmith Observability ───────────────────────────────────────────────────
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=pharmaagent-ai

# ── App ───────────────────────────────────────────────────────────────────────
APP_ENV=development
CORS_ORIGINS=http://localhost:3000

# ── Phase 3 ───────────────────────────────────────────────────────────────────
USE_SERVER_TTS=false
FULFILLMENT_WEBHOOK_URL=http://localhost:8000/webhook/simulate
WEBHOOK_MAX_RETRIES=3
WEBHOOK_BASE_DELAY=1.0
RATE_LIMIT_PER_MINUTE=60
```

> ⚠️ Replace `YOUR_PASSWORD` with the PostgreSQL password you set during installation.

### Step 6.3 — Get your Gemini API key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key and paste it as `GEMINI_API_KEY` in your `.env`

> The free tier is sufficient for demo purposes.

### Step 6.4 — Get your LangSmith API key

1. Go to **https://smith.langchain.com**
2. Create a free account
3. Go to **Settings → API Keys → Create API Key**
4. Copy the key and paste it as `LANGCHAIN_API_KEY` in your `.env`

> LangSmith is optional for running the app, but required for viewing AI traces.
> If you skip LangSmith, set `LANGCHAIN_TRACING_V2=false`.

---

## 7. Database Initialization

The app automatically creates all database tables and seeds initial data when it starts. No manual migration step is needed.

**What happens on first startup:**
- All 10 database tables are created (users, medicines, orders, prescriptions, etc.)
- 10 sample medicines are seeded (7 OTC + 3 Rx requiring prescription)
- Default admin user is created: `admin@pharmaagent.com` / `admin123`
- Default pharmacist user is created: `pharmacist@pharmaagent.com` / `pharma123`

> ✅ You do NOT need to run Alembic migrations manually. The `lifespan` function in `main.py` handles everything.

---

## 8. Run the Backend Server

Make sure you are inside the `backend/` folder with your virtual environment activated.

```bash
uvicorn app.main:app --reload --port 8000
```

**What this does:**
- `uvicorn` — ASGI server that runs FastAPI
- `app.main:app` — loads the FastAPI app from `backend/app/main.py`
- `--reload` — auto-restarts when you change code (development mode)
- `--port 8000` — runs on port 8000

**Expected output:**
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     ✅ Database initialized
INFO:     ✅ Medicines seeded
INFO:     ✅ Admin user created/verified
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Access points:**
- **API Base URL:** http://localhost:8000
- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

> 🛑 Keep this terminal open. The backend must stay running.

---

## 9. Frontend Setup (Next.js)

Open a **new terminal window** (keep the backend terminal running).

### Step 9.1 — Navigate to frontend folder

```bash
cd frontend
```

(If you're in `backend/`, go up first: `cd ..` then `cd frontend`)

### Step 9.2 — Install Node.js dependencies

```bash
npm install
```

> ⏳ This installs Next.js, React, TypeScript, Recharts, and all other packages. Takes 1–3 minutes.

### Step 9.3 — Create the frontend environment file

**Windows:**
```powershell
# Create the file manually using Notepad or VS Code, OR:
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
```

**Mac / Linux:**
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

The `.env.local` file should contain exactly:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> This tells the Next.js frontend where your FastAPI backend is running.

### Step 9.4 — Run the frontend

```bash
npm run dev
```

**Expected output:**
```
▲ Next.js 15.x.x
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000
```

**Access:** Open your browser and go to **http://localhost:3000**

> 🛑 Keep this terminal open too. You now have two terminals running.

---

## 10. LangSmith Setup (Observability)

LangSmith records every AI agent decision — what tools were called, what Gemini was asked, what it decided, and why.

### Step 10.1 — Create LangSmith account

1. Go to **https://smith.langchain.com**
2. Click **"Sign Up"** (free tier available)
3. Complete registration

### Step 10.2 — Get API key

1. Click your profile icon → **Settings**
2. Click **"API Keys"** in the left panel
3. Click **"Create API Key"**
4. Give it a name (e.g., `pharmaagent-local`)
5. Copy the key — **you won't see it again!**

### Step 10.3 — Add to your `.env`

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_key_here
LANGCHAIN_PROJECT=pharmaagent-ai
```

### Step 10.4 — View traces

After making any chat request or prescription upload:

1. Go to **https://smith.langchain.com**
2. Click **"Projects"** → **pharmaagent-ai**
3. Click any trace to see the full agent reasoning chain

You'll see:
- The user's message
- Which tools the agent called (search_medicines, create_order, etc.)
- The inputs and outputs for each tool
- Token usage and latency

---

## 11. Running the Complete System

Here's the full checklist:

| Step | What to do | Where |
|------|-----------|-------|
| 1 | Ensure PostgreSQL is running | System services / pgAdmin |
| 2 | Start backend | `cd backend && uvicorn app.main:app --reload --port 8000` |
| 3 | Start frontend | `cd frontend && npm run dev` |
| 4 | Open browser | http://localhost:3000 |

**Terminal layout:**
```
Terminal 1 (Backend):
  cd pharmaagent-ai/backend
  venv\Scripts\activate    (or source venv/bin/activate on Mac/Linux)
  uvicorn app.main:app --reload --port 8000

Terminal 2 (Frontend):
  cd pharmaagent-ai/frontend
  npm run dev
```

---

## 12. Default Demo Workflow

Once the application is running, try this demo flow:

### As a Regular User

**1. Register a new account**
- Go to http://localhost:3000/register
- Enter: Name, Email, Password
- Click "Create Account"

**2. Login**
- Go to http://localhost:3000/login
- Use your registered credentials
- You'll be redirected to the Dashboard

**3. Order medicine via Chat**
- Click "Chat" in the navbar → http://localhost:3000/chat
- Type: `I need paracetamol 500mg, 10 tablets`
- The agent will check stock, confirm safety, and create an order

**4. Try a prescription medicine (safety check)**
- Type: `I need amoxicillin 500mg`
- The agent will reject it: "This medicine requires a prescription"

**5. Upload a prescription**
- Click "Vision" → http://localhost:3000/vision
- Upload any image (a photo of any text/document works for demo)
- View the AI extraction result

**6. Use Voice Input**
- Click "Voice" → http://localhost:3000/voice
- Click the 🎙 microphone button
- Speak: "I need ibuprofen 400mg"
- The agent responds (and speaks the answer if TTS is enabled)

**7. Try Symptom Checker**
- Click "Symptom" → http://localhost:3000/symptom
- Type: "I have a headache and mild fever since yesterday"
- Answer the follow-up questions
- Get OTC recommendations with direct order links

### As an Admin

**8. Login as Admin**
```
Email:    admin@pharmaagent.com
Password: admin123
```

**9. View analytics**
- Click "Analytics" → http://localhost:3000/analytics
- See KPI cards, top medicines chart, orders trend, webhook status

**10. Manage inventory**
- Click "Admin" → http://localhost:3000/admin
- Add medicines, update stock, view all orders

### As a Pharmacist

**11. Login as Pharmacist**
```
Email:    pharmacist@pharmaagent.com
Password: pharma123
```

**12. Review prescriptions**
- Click "Pharmacist" → http://localhost:3000/pharmacist
- Approve or reject pending prescriptions with notes

### Viewing AI Traces

**13. Open LangSmith**
- Go to https://smith.langchain.com → Projects → pharmaagent-ai
- Each chat message creates a full trace showing the agent's reasoning

---

## 13. Troubleshooting

### ❌ "Database connection failed" / `psycopg2.OperationalError`

**Cause:** PostgreSQL is not running, or the connection URL is wrong.

**Fix:**
1. Confirm PostgreSQL is running:
   - Windows: Open Services → find "postgresql" → Start
   - Mac: `brew services start postgresql@14`
   - Linux: `sudo systemctl start postgresql`
2. Check your `DATABASE_URL` in `.env` — ensure password is correct
3. Test the connection: `psql -U postgres -d pharmaagent`

---

### ❌ "GEMINI_API_KEY not set" or `google.api_core.exceptions.InvalidArgument`

**Cause:** API key is missing, empty, or invalid.

**Fix:**
1. Make sure you have a valid key from https://aistudio.google.com/app/apikey
2. Paste it in `backend/.env` as: `GEMINI_API_KEY=AIza...`
3. Restart the backend server

---

### ❌ Port 8000 already in use

**Cause:** Another process is using port 8000.

**Fix (Windows):**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**Fix (Mac/Linux):**
```bash
lsof -ti:8000 | xargs kill -9
```

Or run on a different port:
```bash
uvicorn app.main:app --reload --port 8001
```
(Then update `NEXT_PUBLIC_API_URL=http://localhost:8001` in `frontend/.env.local`)

---

### ❌ Port 3000 already in use

**Fix:**
```bash
npm run dev -- --port 3001
```

---

### ❌ LangSmith not logging traces

**Cause:** `LANGCHAIN_TRACING_V2` not set, or wrong API key.

**Fix:**
1. Ensure `LANGCHAIN_TRACING_V2=true` in `.env`
2. Ensure `LANGCHAIN_API_KEY` is valid (test at smith.langchain.com)
3. Restart the backend: traces appear only after a restart
4. Make at least one chat request — then check https://smith.langchain.com

---

### ❌ `Module not found` errors in frontend

**Fix:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

---

### ❌ `venv\Scripts\activate` fails on Windows PowerShell

**Fix:** Run this first to allow scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### ❌ `pip install` fails for `psycopg2-binary`

**Fix:** Install the pre-built binary:
```bash
pip install psycopg2-binary --only-binary :all:
```

---

### ❌ Voice recording not working

**Cause:** Voice input uses the Web Speech API, which requires:
- A modern browser (Chrome, Edge, Safari — Firefox has limited support)
- HTTPS in production (HTTP works on localhost)
- Microphone permission granted

**Fix:** Use Chrome or Edge. When asked for microphone permission, click **Allow**.

---

## 14. Running Tests

```bash
cd backend
pytest tests/ -v --tb=short
```

Run specific test files:
```bash
pytest tests/test_symptom_agent.py -v
pytest tests/test_webhook_service.py -v
```

---

## 15. Project Reset (Start Fresh)

If you want to reset all data (wipe the database and re-seed):

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Drop and recreate the database
DROP DATABASE pharmaagent;
CREATE DATABASE pharmaagent;
\q
```

Then restart the backend — it will re-initialize and re-seed automatically.
