# 🚀 HOW TO START — CRM Intelligence Platform

## Quick Answer

Open **3 PowerShell terminals**, run one command in each:

```
Terminal 1 (Backend):   cd crm-intelligence\backend    →  uvicorn app.main:app --reload --port 8000
Terminal 2 (Frontend):  cd crm-intelligence\frontend   →  npm run dev
Terminal 3 (Data):      cd crm-intelligence\backend    →  python -m scripts.replay_emails --batch
```

Then open: **http://localhost:3000**

---

## Full Setup Guide (First Time)

### Prerequisites
- Python 3.10+  (`python --version`)
- Node.js 18+   (`node --version`)
- HuggingFace API key from https://huggingface.co/settings/tokens
- LangSmith API key from https://smith.langchain.com (optional)

---

### STEP 1 — Set API Keys

Open `crm-intelligence/.env` and update:
```env
HUGGINGFACE_API_KEY=hf_your_real_key_here
LANGCHAIN_API_KEY=lsv2_your_langsmith_key_here
```

---

### STEP 2 — Install Python packages (one-time, ~5 min)

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence\backend
python -m pip install -r requirements.txt
```

---

### STEP 3 — Seed the RAG Knowledge Base (one-time, ~3 min)

```powershell
# Still in the backend/ folder
python -m scripts.seed_rag
```

**What happens:** Downloads embedding model (~90MB), reads 6 policy documents,
creates 280+ vector embeddings, saves to `chroma_db/` folder.

Expected output:
```
Loaded: pricing_policy.md
Loaded: sla_policy.md
...
Successfully stored 287 chunks in ChromaDB
```

> ⚠️ Only needed ONCE. If `chroma_db/` folder exists, skip this step.

---

### STEP 4 — Start Backend (Terminal 1)

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence\backend
uvicorn app.main:app --reload --port 8000
```

**Verify it works:**
```powershell
# In a new terminal
Invoke-WebRequest -Uri "http://localhost:8000/api/health" | Select-Object -ExpandProperty Content
# Returns: {"status":"healthy","version":"1.0.0","env":"development"}
```

**Swagger API docs:** http://localhost:8000/api/docs

---

### STEP 5 — Start Frontend (Terminal 2)

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence\frontend
npm install   # first time only
npm run dev
```

**Dashboard:** http://localhost:3000

---

### STEP 6 — Ingest Email Dataset (Terminal 3)

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence\backend
python -m scripts.replay_emails --batch
```

**What happens:** Reads `email-data-advanced.json`, posts all emails to the backend.
The AI agent processes each email in the background (~5-30s per email, depending
on HuggingFace API speed).

Watch the inbox at http://localhost:3000 fill up with classified emails!

---

## Why Does Processing Take Time?

| Operation | Duration | Reason |
|-----------|----------|--------|
| Seed RAG (first run) | 2–5 min | Model download + embedding 6 documents |
| First AI email classification | 30–90 sec | HuggingFace loads Mistral-7B (cold start) |
| Subsequent AI classification | 5–20 sec | API network round-trip |
| Heuristic filter (spam/legal/security) | <10ms | Pure Python regex, no API call |
| All other API requests | <100ms | Database query only |

**The heuristic filter catches critical threats INSTANTLY** (security/ransomware, legal/C&D,
GDPR requests) without any LLM call. Only regular emails (billing, support, etc.) use the LLM.

---

## Quick Test Commands

After starting the backend, test these in PowerShell:

```powershell
# Test 1: Health check
Invoke-WebRequest -Uri "http://localhost:8000/api/health" | Select-Object -ExpandProperty Content

# Test 2: Ingest a test email
$email = '{"message_id":"manual_001","sender":"test@example.com","subject":"Billing issue","body":"I was charged twice this month. Please help.","timestamp":"2024-01-15T10:00:00Z","thread_id":"t1"}'
Invoke-WebRequest -Uri "http://localhost:8000/api/emails/ingest" -Method POST -ContentType "application/json" -Body $email | Select-Object -ExpandProperty Content

# Test 3: Security threat detection (no LLM needed, instant)
$threat = '{"message_id":"sec_001","sender":"hacker@evil.com","subject":"Pay BTC","body":"Send bitcoin to avoid ransomware dark web leak","timestamp":"2024-01-15T10:01:00Z","thread_id":"t2"}'
Invoke-WebRequest -Uri "http://localhost:8000/api/emails/ingest" -Method POST -ContentType "application/json" -Body $threat | Select-Object -ExpandProperty Content

# Test 4: List emails
Invoke-WebRequest -Uri "http://localhost:8000/api/emails" | Select-Object -ExpandProperty Content

# Test 5: Analytics
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/summary" | Select-Object -ExpandProperty Content
```

---

## One-Click Startup (Optional)

Instead of the steps above, run the helper script:

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence
.\start.ps1
```

This automatically checks dependencies, seeds RAG if needed, and starts both servers.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `HUGGINGFACE_API_KEY missing` | Set key in `.env` file |
| `ModuleNotFoundError` | Run `python -m pip install -r requirements.txt` |
| `ChromaDB collection empty` | Run `python -m scripts.seed_rag` |
| Backend not starting | Check port 8000 is free: `netstat -ano | findstr 8000` |
| Frontend blank page | Check backend is running at port 8000 |
| AI processing slow | Normal! First call is 30-90s (cold start) |
| `email-data-advanced.json not found` | Check file exists at `SenAI2/email-data-advanced.json` |

---

## Folder Structure (Quick Reference)

```
SenAI2/
├── email-data-advanced.json          ← EMAIL DATASET (input)
└── crm-intelligence/
    ├── .env                          ← API KEYS (edit this first!)
    ├── start.ps1                     ← ONE-CLICK STARTUP
    ├── PROJECT_GUIDE.md              ← Full architecture guide
    ├── backend/
    │   ├── requirements.txt
    │   ├── app/
    │   │   ├── main.py               ← FastAPI entry point
    │   │   ├── agent/                ← LangGraph AI agent
    │   │   ├── rag/                  ← ChromaDB retrieval
    │   │   ├── models/               ← SQLite database tables
    │   │   ├── api/                  ← REST API routes
    │   │   └── services/             ← Business logic
    │   ├── knowledge_base/           ← 6 policy .md files
    │   └── scripts/
    │       ├── seed_rag.py           ← RUN ONCE: initialize ChromaDB
    │       └── replay_emails.py      ← Ingest email dataset
    └── frontend/
        └── src/
            ├── pages/InboxPage.jsx   ← Email list dashboard
            ├── pages/ThreadPage.jsx  ← Email detail + AI draft
            └── pages/AnalyticsPage.jsx ← Charts and KPIs
```
