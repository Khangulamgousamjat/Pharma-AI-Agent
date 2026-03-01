# 🏥 PharmaAgent AI — Demo Checklist for Judges

> **Time required:** ~10 minutes for full end-to-end demo

---

## 🚀 Setup (One-time)

```bash
# Terminal 1 — Backend
cd pharmaagent-ai/backend
.\venv\Scripts\activate          # Windows
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd pharmaagent-ai/frontend
npm run dev
```

Then load demo data:
```bash
# Terminal 3 (one-time)
cd pharmaagent-ai/backend
.\venv\Scripts\activate
python scripts/load_demo_data.py
```

Open **http://localhost:3000**

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| 👤 User | `john@example.com` | `user123` |
| 🔧 Admin | `admin@pharmaagent.com` | `admin123` |
| 👨‍⚕️ Pharmacist | `pharmacist@pharmaagent.com` | `pharma123` |

---

## 📋 Step-by-Step Demo Flow

### Step 1 — Login as User
1. Go to `http://localhost:3000/login`
2. Click **"user"** tab → pre-fills `john@example.com / user123`
3. Click **Sign In as User**
4. ✅ Lands on Chat page

---

### Step 2 — Chat: Order an OTC Medicine
1. In the chat box, type: `I need paracetamol 500mg, 10 tablets`
2. Wait for agent response
3. ✅ Agent confirms order, quotes price, creates order in DB
4. Check LangSmith: https://smith.langchain.com → Projects → `pharmaagent-ai`

---

### Step 3 — Safety Enforcement (Prescription Required)
1. In chat, type: `I need amoxicillin 500mg`
2. ✅ Agent **rejects** the order: "This medicine requires a prescription"

---

### Step 4 — Voice Input
1. Navigate to **Voice** in sidebar (or `/voice`)
2. Click the 🎙 microphone button
3. Speak: *"I need ibuprofen 400mg"*
4. ✅ Speech transcribed → agent responds in text (and speaks it back)

---

### Step 5 — Upload Prescription (Vision Agent)
1. Navigate to **Vision** in sidebar (or `/vision`)
2. Click **Upload** and select any image with text
3. ✅ Gemini Vision extracts medicine info and displays structured result

---

### Step 6 — Symptom Checker
1. Navigate to **Symptom Check** in sidebar (or `/symptom`)
2. Describe: *"I have a headache and mild fever"*
3. Answer the follow-up MCQ questions
4. ✅ System recommends OTC medicines (never suggests Rx)

---

### Step 7 — Export My Orders (User)
1. Go to **My Orders** in sidebar (or `/dashboard`)
2. Click **📥 Export** next to "Recent Orders"
3. ✅ Downloads `my_orders.xlsx` with formatted order history

---

### Step 8 — Login as Admin
1. Click **Sign Out** in the sidebar
2. Login with `admin@pharmaagent.com / admin123`
3. ✅ Lands on Admin dashboard (no chat icon visible)

---

### Step 9 — Admin: View Analytics
1. Click **Analytics** in sidebar
2. ✅ See KPI cards, revenue charts, top medicines chart

---

### Step 10 — Admin: Export All Orders
1. Click **Inventory & Orders** in sidebar (or `/admin`)
2. Click **📥 Export Orders** button in header
3. ✅ Downloads `orders_export.xlsx` with all system orders

---

### Step 11 — Login as Pharmacist
1. Click **Sign Out**
2. Login with `pharmacist@pharmaagent.com / pharma123`
3. ✅ Lands on Pharmacist dashboard

---

### Step 12 — Pharmacist: Approve Prescription
1. If prescriptions are pending, click **Approve** or **Reject**
2. ✅ Status updates immediately

---

### Step 13 — Pharmacist: Export Inventory
1. Click **📥 Export Inventory** button
2. ✅ Downloads `medicine_inventory.xlsx` with all medicines, stock, expiry dates

---

### Step 14 — Show LangSmith Traces
1. Go to https://smith.langchain.com
2. Projects → `pharmaagent-ai`
3. Click on any trace from the chat orders above
4. ✅ Show: agent reasoning, tool calls (search_medicines, create_order), token usage

---

## ✅ Acceptance Checklist

| Feature | Status |
|---------|--------|
| Role-based login | ✅ |
| AI chat ordering | ✅ |
| Prescription safety enforcement | ✅ |
| Voice input (STT) | ✅ |
| Vision agent (OCR) | ✅ |
| Symptom checker | ✅ |
| User order export | ✅ |
| Admin order export | ✅ |
| Pharmacist inventory export | ✅ |
| Email notification (on payment) | ✅ |
| LangSmith observability | ✅ |
| Dark/Light mode toggle | ✅ |
| Logout button | ✅ |

---

*Built with Google Gemini 2.0 Flash · LangChain · FastAPI · Next.js*
