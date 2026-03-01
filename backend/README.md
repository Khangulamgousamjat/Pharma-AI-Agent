# PharmaAgent AI — Backend README

## Overview
FastAPI backend for PharmaAgent AI — an autonomous pharmacy system powered by LangChain + Gemini 2.0 Flash.

## Tech Stack
- **FastAPI** — REST API framework
- **SQLAlchemy** — ORM for PostgreSQL
- **LangChain + Gemini 2.0 Flash** — AI agent
- **LangSmith** — Agent observability and tracing
- **bcrypt + JWT** — Authentication

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in your DATABASE_URL, GEMINI_API_KEY, JWT_SECRET, LANGCHAIN_API_KEY
```

### 3. Create PostgreSQL database
```sql
CREATE DATABASE pharmaagent;
```

### 4. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

Database tables are created automatically and seed data is inserted on startup.

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login (get JWT) |
| GET | /medicines | List all medicines |
| GET | /medicines/search?q= | Search medicines |
| POST | /orders/create | Create order |
| GET | /orders/user/{id} | User's orders |
| GET | /orders/all | All orders (admin) |
| POST | /agent/chat | Chat with AI agent |
| POST | /payment/process | Process payment |

## Default Admin Account
- Email: `admin@pharmaagent.com`
- Password: `admin123`

## Architecture
```
app/
├── main.py          # FastAPI entry point
├── config.py        # Environment-based settings
├── database.py      # SQLAlchemy engine & sessions
├── models/          # ORM models (User, Medicine, Order)
├── schemas/         # Pydantic validation schemas
├── routes/          # HTTP route handlers
├── services/        # Business logic layer
├── agents/          # LangChain pharmacy agent
└── utils/           # Security (JWT/bcrypt), seed data
```
