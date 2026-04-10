<div align="center">

# 🏥 PharmaAgent AI

### Autonomous Multi-Agent Pharmacy System

**Powered by Google Gemini 2.0 Flash · LangChain · FastAPI · Next.js**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat)](https://langchain.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![LangSmith](https://img.shields.io/badge/LangSmith-Traced-FF6B35?style=flat)](https://smith.langchain.com)

---

*A fully agentic, production-structured pharmacy AI system built for a hackathon.*
*Handles prescription safety, multi-agent coordination, voice interaction, symptom triage, and real-time analytics.*

</div>

---

## 🔍 Problem Statement

Traditional pharmacy systems are rigid, error-prone, and inaccessible. Patients forget refills. Prescription safety is manual and slow. Pharmacists spend hours on paperwork. There is no intelligent layer that connects the patient, pharmacist, and medicine inventory.

**PharmaAgent AI solves this** by replacing brittle rule-based logic with a network of intelligent AI agents that autonomously handle the full pharmacy workflow — from a natural language order request to verified prescription dispensing.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 💬 **Conversational Ordering** | Chat naturally to order medicines — the agent handles search, safety checks, and order creation |
| 🔒 **Prescription Safety Enforcement** | Rx medicines are automatically blocked unless a pharmacist has approved a valid prescription |
| 📸 **Vision Agent (OCR)** | Upload a photo of a prescription — Gemini Vision extracts medicine names, dosages, and instructions |
| 🔁 **Refill Prediction** | Proactively predicts when patients will run out based on order history and sends alerts |
| 🩺 **Symptom Checker** | Safe, MCQ-style triage with dual red-flag detection — never suggests Rx medicines |
| 🎙 **Voice Interaction** | Browser-based Speech-to-Text and Text-to-Speech — works in Hindi, Marathi, and English |
| 🌐 **Multilingual Support** | Full support for English, Hindi (हिंदी), and Marathi (मराठी) |
| 📡 **Webhook Automation** | Orders trigger fulfillment webhooks with exponential backoff retry and idempotency |
| 📊 **Admin Analytics** | Real-time charts for top medicines, daily revenue, refill stats, and webhook success rates |
| 🔭 **LangSmith Observability** | Every agent decision is fully traced — see tools called, inputs, outputs, and token usage |
| 👨‍⚕️ **Pharmacist Dashboard** | Pharmacists review, approve, or reject prescriptions with notes |
| ⚙️ **User Settings** | Persistent UI theme (dark/light) and language preference stored in the database |

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│  Next.js 15 (TypeScript) — Glassmorphism UI                    │
│  Pages: Chat · Voice · Vision · Symptom · Analytics · Admin    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/JSON (REST API)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Python)                     │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Auth Routes │  │ Agent Routes │  │ Analytics/Webhook/     │  │
│  │ JWT + bcrypt│  │ /agent/chat  │  │ Symptom/Voice/Settings│  │
│  └─────────────┘  └──────┬───────┘  └───────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐│
│  │                    AGENT LAYER                              ││
│  │  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐  ││
│  │  │ Pharmacy     │  │ Vision      │  │ Symptom          │  ││
│  │  │ Agent        │  │ Agent       │  │ Agent            │  ││
│  │  │ (ReAct)      │  │ (OCR)       │  │ (MCQ triage)     │  ││
│  │  └──────────────┘  └─────────────┘  └──────────────────┘  ││
│  │  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐  ││
│  │  │ Refill       │  │ Safety      │  │ Voice            │  ││
│  │  │ Agent        │  │ Agent       │  │ Agent            │  ││
│  │  └──────────────┘  └─────────────┘  └──────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐│
│  │              SERVICES LAYER                                 ││
│  │  Analytics · Webhook (retry+idempotency) · Voice · Refill  ││
│  └─────────────────────────────────────────────────────────────┘│
└───────────────────────────┬─────────────────────────────────────┘
                            │ SQLAlchemy ORM
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               POSTGRESQL DATABASE                                │
│  Users · Medicines · Orders · Prescriptions · RefillAlerts     │
│  SymptomSessions · WebhookEvents                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│           GOOGLE GEMINI 2.0 FLASH                               │
│  All agents use Gemini as the underlying LLM                    │
│  Every call is traced in LangSmith                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Frontend Framework** | Next.js | 15 |
| **Frontend Language** | TypeScript | 5 |
| **UI Styling** | TailwindCSS | 3 |
| **Charts** | Recharts | 2 |
| **Backend Framework** | FastAPI | 0.115 |
| **Backend Language** | Python | 3.11+ |
| **ORM** | SQLAlchemy | 2 |
| **Database** | PostgreSQL | 14+ |
| **AI Model** | Google Gemini 2.0 Flash | latest |
| **Agent Framework** | LangChain | 0.3 |
| **Observability** | LangSmith | 0.1 |
| **Authentication** | JWT (python-jose) + bcrypt | — |
| **Voice STT/TTS** | Web Speech API (browser-native) | — |
| **Database Driver** | psycopg2-binary | 2.9 |
| **Validation** | Pydantic | 2 |

---

## 📸 Screenshots

> Add screenshots here — recommended screens to capture:
>
> 1. **Chat interface** — showing a successful medicine order conversation
> 2. **Voice page** — with active transcript
> 3. **Symptom Checker** — OTC recommendation result
> 4. **Admin Analytics** — charts and KPI cards
> 5. **Pharmacist Dashboard** — prescription approval queue
> 6. **LangSmith trace** — full agent reasoning chain

```
[ Paste screenshot images here ]
```

---

## 🚀 Setup Instructions

For complete setup instructions, see **[SET_UP.md](./SET_UP.md)**.

### Quick Start (3 Commands)

```bash
# 1. Backend
cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
cp .env.example .env   # ← Fill in GEMINI_API_KEY and DATABASE_URL

# 2. Frontend
cd ../frontend && npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 3. Run (two terminals)
# Terminal 1: cd backend && uvicorn app.main:app --reload --port 8000
# Terminal 2: cd frontend && npm run dev
```

Open http://localhost:3000

---

## 🎮 Demo Workflow

### Default Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@pharmaagent.com` | `admin123` |
| Pharmacist | `pharmacist@pharmaagent.com` | `pharma123` |
| User | Register at `/register` | Your choice |

### Step-by-Step Demo

**1. Patient Journey:**
```
Register → Login → Chat: "I need paracetamol 500mg 10 tablets"
→ Agent searches inventory → Confirms OTC safe → Creates order
→ Voice: Click 🎙, say "I need ibuprofen"
→ Symptom: Describe "headache and fever" → Answer MCQs → Get OTC suggestions
```

**2. Safety Enforcement:**
```
Chat: "I need amoxicillin 500mg"
→ Agent blocks: "This medicine requires a prescription"
→ Upload prescription via Vision → Pharmacist approves
→ Chat again → Order now allowed
```

**3. Admin View:**
```
Login as admin → Analytics: See charts, KPIs, webhook success rate
→ Admin: View all orders, manage inventory
→ LangSmith: https://smith.langchain.com → pharmaagent-ai project
```

---

## 🤖 Agent Architecture

### Pharmacy Agent (Core)

The primary LangChain **ReAct agent** powered by Gemini 2.0 Flash. Uses tool-calling to:

1. `search_medicines(query)` — Find medicines in the PostgreSQL inventory
2. `check_prescription_status(user_id, medicine_id)` — Verify prescription approval
3. `create_pharmacy_order(user_id, medicine_id, quantity)` — Place the order
4. `get_order_history(user_id)` — Retrieve past orders
5. `check_refill_alerts(user_id)` — Get proactive refill recommendations

**Safety:** The `create_pharmacy_order` tool has hardcoded blocks:
- `prescription_required = True` → Rejected unless pharmacist-approved prescription exists
- `stock < quantity` → Rejected with stock information

### Vision Agent (Phase 2)

Uses **Gemini Vision** to extract medicine information from uploaded prescription images. Returns structured JSON with medicine names, dosages, and instructions for pharmacist review.

### Refill Prediction Agent (Phase 2)

Analyzes order history patterns to predict when a patient will run low on regularly ordered medicines. Sends proactive alerts before the patient runs out.

### Symptom Checker Agent (Phase 3)

Safe, **non-diagnostic** triage system with two-layer red-flag detection:
1. **Local keyword matching** — Instantly detects emergency symptoms (chest pain, unconsciousness, severe bleeding) before calling any LLM
2. **Gemini analysis** — Provides contextual red-flag check on top
3. **6-question MCQ flow** — Progressively narrows down the situation
4. **Tiered output** — `otc` (suggest OTC medicines) / `doctor` (refer) / `emergency` (call 112)
5. **Hard OTC filter** — DB query ensures only `prescription_required=False` medicines are ever suggested

### Voice Agent (Phase 3)

Thin coordinator that validates language, delegates to the pharmacy agent with language context, and returns text suitable for browser TTS.

### Advanced Agent Architecture (Phase 3)
A formal 10-agent proxy sequence managed by the `AgentCoordinator`. Handles fulfillment pipelines sequentially:
**Conversation** → **Stock** → **Prescription** → **Payment** → **Order** → **Delivery** → **Notification**. 
Every single node enforces strict rules, compliance, predictive logic, and connects to LangSmith.

---

## 🔭 Observability (LangSmith)

Every agent interaction creates a fully structured LangSmith trace:

```
Trace: "I need paracetamol 10 tablets"
├── pharmacy_agent_run
│   ├── tool: search_medicines("paracetamol")
│   │   └── result: [{id: 1, name: "Paracetamol 500mg", stock: 95, price: 5.0}]
│   ├── tool: create_pharmacy_order(user_id=1, medicine_id=1, quantity=10)
│   │   └── result: {order_id: 42, total: 50.0, status: "confirmed"}
│   └── final_response: "✅ Order created! 10 × Paracetamol 500mg for ₹50..."
```

**Access:** https://smith.langchain.com → Projects → `pharmaagent-ai`

---

## 📂 Project Structure

```
pharmaagent-ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py               ← FastAPI app + all routers registered
│   │   ├── config.py             ← Pydantic settings (env vars)
│   │   ├── database.py           ← SQLAlchemy engine + session
│   │   ├── models/               ← DB table definitions
│   │   │   ├── user.py
│   │   │   ├── medicine.py
│   │   │   ├── order.py
│   │   │   ├── prescription.py
│   │   │   ├── refill_alert.py
│   │   │   ├── webhook_event.py  ← Phase 3
│   │   │   └── symptom_session.py ← Phase 3
│   │   ├── agents/
│   │   │   ├── pharmacy_agent.py ← Core ReAct agent
│   │   │   ├── safety_agent.py   ← Prescription safety enforcement
│   │   │   ├── vision_agent.py   ← OCR via Gemini Vision
│   │   │   ├── refill_agent.py   ← Proactive refill prediction
│   │   │   ├── symptom_agent.py  ← MCQ triage (Phase 3)
│   │   │   └── voice_agent.py    ← Voice coordinator (Phase 3)
│   │   ├── routes/
│   │   │   ├── auth.py           ← /auth/register, /auth/login
│   │   │   ├── medicines.py      ← /medicines
│   │   │   ├── orders.py         ← /orders
│   │   │   ├── agent.py          ← /agent/chat
│   │   │   ├── prescriptions.py  ← /prescriptions
│   │   │   ├── pharmacist.py     ← /pharmacist
│   │   │   ├── refill_alerts.py  ← /refill-alerts
│   │   │   ├── voice_routes.py   ← /agent/voice-message (Phase 3)
│   │   │   ├── symptom_routes.py ← /symptom (Phase 3)
│   │   │   ├── webhook_routes.py ← /webhook (Phase 3)
│   │   │   ├── analytics_routes.py ← /analytics (Phase 3)
│   │   │   └── settings_routes.py ← /settings (Phase 3)
│   │   └── services/
│   │       ├── webhook_service.py ← Retry logic + idempotency
│   │       ├── analytics_service.py ← KPI computations
│   │       └── voice_service.py   ← Voice message processing
│   ├── tests/
│   │   ├── test_webhook_service.py
│   │   └── test_symptom_agent.py
│   └── requirements.txt
│
└── frontend/
    ├── app/
    │   ├── chat/page.tsx
    │   ├── voice/page.tsx         ← Phase 3
    │   ├── vision/page.tsx
    │   ├── symptom/page.tsx       ← Phase 3
    │   ├── analytics/page.tsx     ← Phase 3
    │   ├── pharmacist/page.tsx
    │   ├── admin/page.tsx
    │   ├── settings/page.tsx      ← Phase 3
    │   ├── dashboard/page.tsx
    │   ├── login/page.tsx
    │   └── register/page.tsx
    ├── components/
    │   ├── Navbar.tsx
    │   ├── GlassCard.tsx
    │   ├── ChatInterface.tsx
    │   ├── VoiceRecorder.tsx      ← Phase 3
    │   ├── LanguageSelector.tsx   ← Phase 3
    │   ├── SymptomFlow.tsx        ← Phase 3
    │   └── AnalyticsCharts.tsx    ← Phase 3
    └── lib/
        ├── api.ts                 ← Typed API client
        └── auth.ts                ← JWT helpers
```

---

## 🏆 Hackathon Compliance

| Requirement | Implementation |
|-------------|---------------|
| **Autonomous AI agents** | LangChain ReAct agents with real tool-calling and multi-step reasoning |
| **Production architecture** | Clean separation of models / schemas / routes / services / agents |
| **Observability** | Full LangSmith integration — every agent call is traced |
| **Safety constraints** | Prescription enforcement at tool level, not prompt level |
| **Multi-agent coordination** | Vision → Safety → Pharmacy pipeline with shared DB state |
| **Real-world use case** | Realistic pharmacy domain with actual safety implications |
| **Frontend** | Premium glassmorphism UI with responsive design |
| **Database** | PostgreSQL with proper foreign keys and relationships |
| **Testing** | pytest unit tests for critical safety components |
| **Documentation** | Comprehensive SET_UP.md + inline code comments |

---

## 📋 API Reference

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Key endpoints:

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login, get JWT |
| `POST` | `/agent/chat` | Chat with pharmacy agent |
| `POST` | `/agent/voice-message` | Voice message (multilingual) |
| `GET` | `/medicines` | List inventory |
| `POST` | `/orders/create` | Create order |
| `POST` | `/prescriptions/upload` | Upload prescription image |
| `POST` | `/pharmacist/prescriptions/{id}/verify` | Approve/reject prescription |
| `POST` | `/symptom/check` | Start symptom triage |
| `POST` | `/symptom/continue` | Submit MCQ answer |
| `GET` | `/analytics/overview` | Admin KPIs |
| `POST` | `/webhook/simulate` | Mock warehouse webhook |
| `GET/PUT` | `/settings/preferences` | User theme + language |
| `GET` | `/health` | System health check |

---

## 🔒 Security Notes

- All passwords hashed with **bcrypt** (12 rounds)
- JWT tokens expire after **24 hours** (configurable)
- Prescription safety enforced at the **database tool level** — cannot be bypassed by prompt injection
- Voice audio **never leaves the browser** — STT runs locally via Web Speech API
- Symptom checker always includes **medical disclaimer** and blocks Rx medicine suggestions

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests
4. Run: `cd backend && pytest tests/ -v`
5. Run: `cd frontend && npx tsc --noEmit`
6. Submit a pull request

---

## 📄 License

MIT License — see LICENSE file for details.

---

<div align="center">

**Built with ❤️ GOUS KHAN**

*PharmaAgent AI — Making pharmacy intelligent, safe, and accessible*

</div>
