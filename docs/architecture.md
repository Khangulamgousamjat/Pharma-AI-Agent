# PharmaAgent AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│         Next.js App (localhost:3000) — Glassmorphism UI         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP Fetch (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (localhost:8000)              │
│                                                                 │
│  ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌───────────────┐  │
│  │ /auth    │  │/medicines │  │ /orders │  │  /agent/chat  │  │
│  └────┬─────┘  └─────┬─────┘  └────┬────┘  └──────┬────────┘  │
│       │               │             │               │            │
│  ┌────▼───────────────▼─────────────▼───────────────▼────────┐  │
│  │                   Service Layer                            │  │
│  │  auth_service │ medicine_service │ order_service │ payment │  │
│  └────────────────────────────────────────────────────────────┘  │
│       │                                             │            │
│  ┌────▼────────────────────────────────────────┐    │            │
│  │              PostgreSQL Database             │◄───┘            │
│  │     Users │ Medicines │ Orders               │                │
│  └────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                         │ /agent/chat LangChain
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangChain ReAct Agent                       │
│                                                                 │
│   User Message → Gemini 2.0 Flash LLM → Tool Selection         │
│                                                                 │
│   Tools Available:                                              │
│   ├── check_medicine_availability(name)                         │
│   │       └─ Queries DB, returns stock + prescription_required  │
│   ├── create_pharmacy_order(medicine_id, quantity, user_id)     │
│   │       ├─ Safety Check: prescription_required? → BLOCK       │
│   │       ├─ Stock Check: stock >= quantity? else → REJECT       │
│   │       └─ Creates Order + Deducts Stock                      │
│   └── get_order_history(user_id)                               │
│               └─ Returns recent orders for user                 │
│                                                                 │
│   LangSmith: Every execution is traced automatically            │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Flow

1. Request hits FastAPI route handler
2. Route extracts JWT from header, verifies with `verify_token()`
3. Route calls appropriate service function (business logic)
4. Service interacts with DB via SQLAlchemy ORM
5. Response serialized via Pydantic schema and returned as JSON

## Agent Flow (POST /agent/chat)

1. Route validates JWT + user_id match
2. `get_pharmacy_agent()` returns singleton `PharmacyAgent`
3. `set_db_session(db)` injects DB session into tool functions
4. `executor.ainvoke()` starts the ReAct loop:
   - LLM reads user message
   - LLM chooses a tool and generates arguments
   - Tool executes with real DB access
   - LLM reads tool result (Observation)
   - Repeats until confident in final answer
5. Action type extracted from intermediate steps
6. Response returned with `action`, `order_id`, and `trace_url`

## Frontend Flow

1. User lands at `/login` → enters credentials
2. `loginUser()` POSTs to `/auth/login` → gets JWT
3. JWT stored in localStorage via `saveAuth()`
4. `authHeader()` adds `Authorization: Bearer <token>` to all requests
5. Chat page renders `<ChatInterface userId={user.id} />`
6. On send: `sendAgentMessage()` → `/agent/chat` → updates message list
7. If `action === "order_created"` → "Pay Now" button triggers `/payment/process`

## Safety Logic

```python
# In agents/tools.py — create_pharmacy_order()

if medicine.prescription_required:
    return "⚠️ This medicine requires a prescription. Cannot order."

if medicine.stock < quantity:
    return "❌ Insufficient stock available."

# Both checks passed — create the order
order = create_order(db, user_id, medicine_id, quantity)
return "✅ Order created: #{order.id}"
```

## Database Schema

```
users
  id PK | name | email UNIQUE | password_hash | role | created_at

medicines
  id PK | name UNIQUE | stock | unit | price | prescription_required | expiry_date | description

orders
  id PK | user_id FK→users | medicine_id FK→medicines | quantity | total_price | status | created_at
```
