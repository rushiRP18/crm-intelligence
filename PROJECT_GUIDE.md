# CRM Intelligence Platform — Complete Project Guide

> **Everything you need to understand, run, and demonstrate this project.**

---

## Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Why It Takes Time (Performance Explained)](#why-it-takes-time)
3. [System Architecture](#system-architecture)
4. [How to Start the Project](#how-to-start-the-project)
5. [File Structure](#file-structure)
6. [How Each Component Works](#how-each-component-works)
7. [The AI Agent Flow (Step-by-Step)](#the-ai-agent-flow)
8. [API Endpoints Reference](#api-endpoints-reference)
9. [The Frontend Dashboard](#the-frontend-dashboard)
10. [Special Scenarios Handled](#special-scenarios-handled)
11. [Troubleshooting](#troubleshooting)

---

## What This Project Does

This is an **AI-powered CRM (Customer Relationship Management) Email Triage System**. When a customer sends an email, the system:

1. **Receives** the email via an API endpoint
2. **Filters** obvious spam/security threats instantly (heuristic filter, <10ms)
3. **Searches** a knowledge base of company policies using semantic AI (RAG)
4. **Classifies** the email using an open-source LLM (Mistral-7B on HuggingFace)
5. **Decides** the correct action: auto-reply, escalate to human, flag legal/security, create ticket
6. **Drafts** a reply (if appropriate) citing actual policy documents
7. **Stores** everything: email, classification, reasoning trace, draft, escalations
8. **Displays** everything on a React dashboard with live statistics

**Built for:** SenAI AI Intern Technical Assessment  
**Demonstrates:** LangChain, LangGraph, RAG, FastAPI, React, SQLite, HuggingFace

---

## Why It Takes Time

This is the most important thing to understand before running the project.

### Slow Operations (and why)

| Operation | Time | Why |
|-----------|------|-----|
| `python -m scripts.seed_rag` | 2–5 minutes | Downloads `all-MiniLM-L6-v2` model (~90MB), embeds all 6 policy documents |
| First email AI processing | 30–90 seconds | HuggingFace loads Mistral-7B model into memory on first call |
| Subsequent email AI processing | 5–20 seconds | HuggingFace Inference API network round-trip |
| Email ingestion (without AI) | <100ms | Heuristic filter only, very fast |
| All other API calls | <50ms | Pure database queries, very fast |

### Why HuggingFace is Slow

The system uses `mistralai/Mistral-7B-Instruct-v0.3` — a 7 billion parameter language model hosted on HuggingFace's free Inference API. This is a **remote API call** that:

- Takes 5–90 seconds depending on server load
- The first call of the day may trigger a "cold start" (model loading into memory)
- Free tier has rate limits

**This is expected and normal.** The heuristic filter (spam, legal, security, GDPR) runs in <10ms without touching the LLM. Most dangerous emails (ransomware, C&D letters, GDPR requests) are caught by heuristics before the LLM is even called.

### How We Minimized Slowness

```python
# nodes.py — LLM is cached after first creation
@lru_cache(maxsize=1)
def _get_llm():
    return HuggingFaceEndpoint(...)  # Only instantiated ONCE

# LLM call has 60s timeout — won't hang forever
HuggingFaceEndpoint(timeout=60, ...)

# Email ingestion is non-blocking
# Agent runs in background via FastAPI BackgroundTasks
@router.post("/emails/ingest")
async def ingest(background_tasks: BackgroundTasks, ...):
    # Returns immediately after DB write + heuristic check
    background_tasks.add_task(run_agent, ...)  # AI runs async
    return {"status": "accepted"}
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REACT DASHBOARD (Port 3000)                  │
│  Inbox | Thread Workspace | Analytics | Live Stats               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST + WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Port 8000)                   │
│                                                                   │
│  POST /api/emails/ingest                                         │
│       │                                                          │
│       ├─► Heuristic Filter ──► spam? → mark_spam (0ms)          │
│       │                        legal? → flag_legal (0ms)         │
│       │                        security? → flag_security (0ms)   │
│       │                        gdpr? → gdpr_compliance (0ms)     │
│       │                                                          │
│       └─► Background Task: LangGraph Agent                       │
│                │                                                 │
│                ├─► Fetch Thread History (SQLite)                 │
│                ├─► RAG Search (ChromaDB + MiniLM)               │
│                ├─► Classify Email (Mistral-7B via HuggingFace)  │
│                ├─► Evaluate Churn/Sentiment Risk                 │
│                ├─► Decision Node (routing logic)                 │
│                └─► Action Node → persist to SQLite              │
│                                                                  │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌──────────────────────┐
│  SQLite Database │       │  ChromaDB Vector Store│
│  crm_intel.db    │       │  chroma_db/           │
│                  │       │  (6 policy docs,      │
│  • emails        │       │   ~300 chunks,        │
│  • threads       │       │   384-dim embeddings) │
│  • contacts      │       └──────────────────────┘
│  • drafts        │
│  • escalations   │       ┌──────────────────────┐
│  • tickets       │       │  HuggingFace API      │
│  • agent_runs    │       │  Mistral-7B-Instruct  │
│  • audit_logs    │       │  (remote inference)   │
│  • rag_retrieval │       └──────────────────────┘
└──────────────────┘
```

---

## How to Start the Project

### Prerequisites

Before starting, make sure you have:
- Python 3.10 or higher
- Node.js 18 or higher
- Your HuggingFace API key (`hf_...`)
- Your LangSmith API key (`lsv2_...`) — optional but recommended

### Step 1 — Set Your API Keys

Open the file `crm-intelligence/.env` and replace the placeholders:

```env
HUGGINGFACE_API_KEY=hf_YOUR_ACTUAL_KEY_HERE
LANGCHAIN_API_KEY=lsv2_YOUR_LANGSMITH_KEY_HERE
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=crm-intelligence
```

> **Where to get keys:**
> - HuggingFace key: https://huggingface.co/settings/tokens (click "New token", read access)
> - LangSmith key: https://smith.langchain.com → Settings → API Keys

### Step 2 — Install Python Dependencies

Open a terminal/PowerShell **inside** `crm-intelligence/backend/`:

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence\backend
pip install -r requirements.txt
```

This installs FastAPI, LangChain, LangGraph, SQLAlchemy, ChromaDB, sentence-transformers, etc.

> ⚠️ **This may take 5–10 minutes the first time** because `sentence-transformers` is large.

### Step 3 — Seed the RAG Knowledge Base (One-Time Only)

```powershell
# Still inside the backend folder
python -m scripts.seed_rag
```

**What this does:**
- Reads all 6 `.md` files in `knowledge_base/`
- Downloads `all-MiniLM-L6-v2` embedding model (~90MB, one-time download)
- Splits documents into ~300 text chunks (400 tokens each)
- Creates vector embeddings for each chunk
- Stores them in `chroma_db/` folder

**Expected output:**
```
Loading knowledge base documents...
Loaded 6 documents, 6 chunks before splitting
Splitting into smaller chunks...
Created 287 chunks
Embedding and storing in ChromaDB...
SUCCESS: 287 chunks stored in ChromaDB
Test queries passed ✓
```

> ⏱️ **Time:** 2–5 minutes the first run (model download). Subsequent runs: 30 seconds.

### Step 4 — Start the Backend Server

```powershell
# In backend/ folder
uvicorn app.main:app --reload --port 8000
```

**Expected output (clean — no SQL spam):**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
2026-06-10 22:33:24 | INFO | app.main | [STARTED] CRM Intelligence Platform
2026-06-10 22:33:24 | INFO | app.main |   Environment : development
2026-06-10 22:33:24 | INFO | app.main |   LLM Model   : mistralai/Mistral-7B-Instruct-v0.3
2026-06-10 22:33:24 | INFO | app.main |   LangSmith   : enabled
INFO:     Application startup complete.
```

**Verify it works:**
```powershell
# In a new terminal
Invoke-WebRequest -Uri "http://localhost:8000/api/health" | Select-Object -ExpandProperty Content
# Should return: {"status":"healthy","version":"1.0.0","env":"development"}
```

📌 API Documentation: http://localhost:8000/api/docs (Swagger UI)

### Step 5 — Start the Frontend

Open a **new terminal** in `crm-intelligence/frontend/`:

```powershell
cd C:\Users\Gayatri\Desktop\SenAI2\crm-intelligence\frontend
npm install     # first time only
npm run dev
```

**Expected output:**
```
  VITE v5.4.21  ready in 607 ms
  ➜  Local:   http://localhost:3000/
```

📌 Dashboard: http://localhost:3000

### Step 6 — Ingest the Email Dataset

```powershell
# In backend/ folder, with backend server running
python -m scripts.replay_emails --batch
```

**What this does:**
- Reads all emails from `SenAI2/email-data-advanced.json`
- Posts each email to `POST /api/emails/ingest`
- The backend stores each email in SQLite
- Background AI agent processes each email (may take a few minutes total)

> Or use streaming mode (one email per second):
> ```powershell
> python -m scripts.replay_emails --speed 1.0
> ```

### Step 7 — View Results

Open http://localhost:3000 and:
1. Click **Mission Control** to see all emails with classifications
2. Click any email row to open the **Thread Workspace** (3-column view)
3. Click **Analytics** to see sentiment trends and category breakdown

---

## File Structure

```
crm-intelligence/
│
├── .env                          ← Your API keys go here (REQUIRED)
├── .env.example                  ← Template for .env
├── README.md                     ← Quick start guide
├── docker-compose.yml            ← Run everything with Docker
│
├── backend/
│   ├── requirements.txt          ← Python packages
│   ├── Dockerfile
│   │
│   ├── app/
│   │   ├── main.py               ← FastAPI app entry point
│   │   ├── config.py             ← All settings from .env
│   │   ├── database.py           ← SQLite + SQLAlchemy setup
│   │   │
│   │   ├── models/               ← Database table definitions
│   │   │   ├── email.py          ← Email table (central)
│   │   │   ├── thread.py         ← Conversation threads
│   │   │   ├── contact.py        ← Customer profiles + churn risk
│   │   │   ├── draft.py          ← AI-generated reply drafts
│   │   │   ├── escalation.py     ← Human/legal/security escalations
│   │   │   ├── ticket.py         ← Internal support tickets
│   │   │   ├── agent_run.py      ← AI reasoning traces per email
│   │   │   ├── audit_log.py      ← Immutable change history
│   │   │   ├── rag_retrieval.py  ← Which KB chunks were used
│   │   │   └── web_intel.py      ← Public review cache (6h TTL)
│   │   │
│   │   ├── schemas/              ← Request/response data shapes (Pydantic)
│   │   │
│   │   ├── api/                  ← HTTP routes (10 routers)
│   │   │   ├── emails.py         ← POST /ingest, GET /emails, etc.
│   │   │   ├── threads.py        ← GET /threads
│   │   │   ├── contacts.py       ← GET /contacts, PATCH /status
│   │   │   ├── drafts.py         ← GET /drafts, POST /approve
│   │   │   ├── analytics.py      ← /summary, /sentiment-trend, /category-breakdown
│   │   │   ├── rag.py            ← /rag/search (debug the KB)
│   │   │   ├── intelligence.py   ← /intelligence/reputation
│   │   │   ├── agent.py          ← /agent/dry-run (test without side effects)
│   │   │   ├── audit.py          ← /audit/{entity}/{id}
│   │   │   └── tickets.py        ← GET /tickets
│   │   │
│   │   ├── agent/                ← The LangGraph AI agent
│   │   │   ├── state.py          ← AgentState TypedDict (all fields)
│   │   │   ├── nodes.py          ← 10 workflow nodes (the actual logic)
│   │   │   ├── graph.py          ← Wires nodes into the graph
│   │   │   └── tools.py          ← LangChain tools the agent can call
│   │   │
│   │   ├── rag/                  ← Knowledge base retrieval
│   │   │   ├── loader.py         ← Reads .md files, splits into chunks
│   │   │   ├── embedder.py       ← Converts text to 384-dim vectors
│   │   │   └── retriever.py      ← ChromaDB search by cosine similarity
│   │   │
│   │   └── services/             ← Business logic helpers
│   │       ├── heuristic_filter.py   ← Fast pre-AI rules engine
│   │       ├── thread_builder.py     ← Loads conversation context
│   │       ├── sentiment_tracker.py  ← Detects sentiment deterioration
│   │       ├── web_scraper.py        ← Mock G2/Trustpilot data
│   │       └── audit_service.py      ← log_action() helper
│   │
│   ├── knowledge_base/           ← 6 policy documents for RAG
│   │   ├── pricing_policy.md
│   │   ├── sla_policy.md
│   │   ├── refund_policy.md
│   │   ├── api_docs.md
│   │   ├── compliance_faq.md
│   │   └── escalation_matrix.md
│   │
│   └── scripts/
│       ├── seed_rag.py           ← Initialize ChromaDB
│       └── replay_emails.py      ← Feed emails into the system
│
└── frontend/
    ├── package.json
    ├── vite.config.js            ← Proxies /api → localhost:8000
    ├── index.html
    └── src/
        ├── main.jsx              ← React entry point
        ├── App.jsx               ← Route config
        ├── index.css             ← Global dark SaaS design system
        ├── lib/
        │   └── api.js            ← Axios client for all endpoints
        ├── components/
        │   └── Layout.jsx        ← Sidebar navigation
        └── pages/
            ├── InboxPage.jsx     ← Email list with filters/search
            ├── ThreadPage.jsx    ← 3-column email detail workspace
            └── AnalyticsPage.jsx ← Charts + KPI dashboard
```

---

## How Each Component Works

### 1. Heuristic Filter (`services/heuristic_filter.py`)

Runs **before** the AI agent. Uses keyword matching and regex patterns:

| Flag | Keywords Checked | Action |
|------|-----------------|--------|
| `is_spam` | nigerian prince, click here, buy now, lottery, etc. | `mark_spam` immediately |
| `is_security_threat` | ransomware, bitcoin, dark web, BTC wallet, north korea | `flag_security` → NEVER reply |
| `is_legal` | cease and desist, lawsuit, attorney, litigation | `flag_legal` → NEVER reply |
| `is_gdpr` | GDPR, data portability, right to erasure, Article 17 | `gdpr_compliance` workflow |
| `is_churn_risk` | cancel subscription, switching to, disappointed | elevate human review |
| `is_internal` | @company.com sender | skip AI, mark internal |

This runs in **<10ms** — critical for ransomware/legal emails that must NEVER get auto-replied.

### 2. RAG Pipeline (`rag/`)

**What is RAG?** Retrieval-Augmented Generation — instead of the LLM guessing policies from training data, we give it real policy text at runtime.

```
Email: "I want a refund after 20 days"
   │
   ▼
Embedder converts email to 384-dim vector
   │
   ▼
ChromaDB cosine similarity search across 287 policy chunks
   │
   ▼
Returns top-3 most relevant chunks:
  1. refund_policy.md: "No refunds after 14 days..." (score: 0.87)
  2. refund_policy.md: "Exception via billing@company.com..." (score: 0.79)
  3. sla_policy.md: "SLA credits as account credits..." (score: 0.61)
   │
   ▼
LLM prompt includes these chunks → accurate, policy-backed response
```

### 3. LangGraph Agent (`agent/`)

The agent is a **state machine** — each step reads the current state and returns updates:

```
AgentState = {
    email_id, sender, subject, body,     ← input
    thread_history,                       ← loaded from DB
    rag_context,                          ← from ChromaDB
    heuristic_flags,                      ← from heuristic filter
    classification,                       ← from LLM
    decision,                             ← routing result
    draft,                                ← generated reply
    final_action,                         ← what was done
    reasoning_trace,                      ← full Thought→Action→Observation log
}
```

**Graph flow:**
```
preprocess → fetch_thread → retrieve_rag → classify → evaluate_risk → decide
                                                                         │
                              ┌──────────────────────────────────────────┤
                              │                                          │
                           (route)                                       │
                              │                                          │
              ┌───────────────┼───────────────┐                         │
              ▼               ▼               ▼                         │
       draft_reply    escalate_human    flag_legal         ...more      │
              │               │               │                         │
              └───────────────┴───────────────┴─────────────────────────┘
                                              ▼
                                       persist_results
                                              ▼
                                             END
```

### 4. LangSmith Tracing

Every agent run is tagged and traced automatically. View at https://smith.langchain.com:
- See exact prompts sent to Mistral-7B
- See RAG chunks retrieved
- See latency of each node
- Debug failed classifications

---

## The AI Agent Flow (Step-by-Step)

Here is exactly what happens when you call `POST /api/emails/ingest`:

### Example: Customer complains about billing

```json
{
  "message_id": "msg_001",
  "sender": "angry.customer@gmail.com",
  "subject": "Wrong charge on my account!",
  "body": "I was charged $299 but I'm on the Standard plan at $99. I want a refund immediately or I'm cancelling.",
  "timestamp": "2024-01-15T10:30:00Z",
  "thread_id": "thread_001"
}
```

**What happens:**

1. **FastAPI receives** the email at `POST /api/emails/ingest`

2. **Heuristic filter** runs in 5ms:
   - Not spam ✓
   - Not legal/security ✓  
   - Contains "refund", "cancelling" → sets `is_churn_risk=True`
   - Returns: `{"is_churn_risk": True, "spam_score": 0.05}`

3. **Database write** — email saved with `status="pending"` (3ms)

4. **API returns immediately** → `{"status": "accepted", "email_id": 1}`
   (The customer doesn't wait for the AI)

5. **Background agent starts** (FastAPI BackgroundTasks):

   ```
   Node 1 - preprocess:
   "Thought: Email from angry.customer@gmail.com, subject: 'Wrong charge...'. Churn risk flagged."
   
   Node 2 - fetch_thread:
   "Thought: Thread 'thread_001' has 0 previous messages. Fresh conversation."
   
   Node 3 - retrieve_rag:
   "Action: search_knowledge_base('Wrong charge billing refund $299 Standard plan')"
   "Observation: Retrieved 3 chunks in 180ms. Sources: [pricing_policy.md, refund_policy.md, refund_policy.md]"
   
   Node 4 - classify (Mistral-7B):
   LLM prompt includes: email + policy chunks
   LLM returns: {
     "category": "Billing",
     "sentiment": "Negative",
     "sentiment_score": -0.72,
     "urgency": "High",
     "requires_human": false,
     "confidence": 0.88,
     "suggested_reply": null,
     "detected_entities": {"monetary_amounts": ["$299", "$99"]}
   }
   
   Node 5 - evaluate_risk:
   "Thought: Churn risk 0.65 (moderate). No sentiment deterioration (first email). Risk level: medium."
   
   Node 6 - decide:
   "Decision: category=Billing, urgency=High, confidence=0.88 >= 0.70 threshold, no requires_human → draft_reply"
   
   Node 7 - action_draft_reply:
   LLM generates: "Dear [Customer], I apologize for the billing discrepancy. Per our pricing policy,
   the Standard plan is $99/month. Our billing team has been notified and will issue a full credit
   of $200 within 3-5 business days. [Policy reference: pricing_policy.md]"
   Draft saved with status="pending" (awaiting human approval)
   
   Node 8 - persist_results:
   Email status → "pending_review"
   AgentRun saved with full reasoning trace
   ```

6. **Dashboard updates** — Inbox shows email with Billing badge, Negative sentiment, draft ready for review

7. **Human reviews draft** in Thread Workspace → clicks "Approve & Send"

---

## API Endpoints Reference

All endpoints under `http://localhost:8000/api/`

### Email Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/emails/ingest` | Submit single email for processing |
| `POST` | `/emails/ingest/batch` | Submit multiple emails at once |
| `GET` | `/emails` | List emails (with filter params) |
| `GET` | `/emails/{id}` | Get single email with agent trace |
| `POST` | `/emails/{id}/process` | Manually re-trigger AI agent |

### Thread Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/threads` | List all conversation threads |
| `GET` | `/threads/{id}` | Get thread with all emails |

### Draft Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/drafts` | List pending drafts needing approval |
| `PATCH` | `/drafts/{id}` | Edit draft body |
| `POST` | `/drafts/{id}/approve` | Approve draft → email resolved |

### Analytics Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics/summary` | KPI numbers (total, escalated, etc.) |
| `GET` | `/analytics/sentiment-trend?days=30` | Daily sentiment scores |
| `GET` | `/analytics/category-breakdown?days=30` | Email category counts |

### Agent/Debug Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agent/dry-run/{email_id}` | Run agent without saving anything |
| `GET` | `/agent/runs/{email_id}` | Get previous agent run trace |
| `GET` | `/rag/search?q=refund+policy&k=3` | Directly query the knowledge base |

---

## The Frontend Dashboard

### Page 1: Mission Control (Inbox)

- **Tab filters**: All / Needs Human / Escalated / Pending Draft / Spam / Internal
- **Email table**: Sender, subject, category emoji, sentiment badge + score bar, urgency, status, confidence%, time ago
- **Search**: Filters by subject/sender/body
- **Auto-refresh**: Every 6 seconds (shows new emails as agent processes them)
- **Red left border**: Unread/pending emails highlighted

### Page 2: Thread Workspace (3 columns)

**Left column — Classification:**
- Category, sentiment (with score), urgency, confidence%, needs human?
- Escalation reason if applicable
- "Run AI Agent" / "Dry Run" / "Re-Process" buttons

**Center column — Email + Draft:**
- Full email body with detected entities (order IDs, amounts, deadlines)
- AI draft editor (editable textarea)
- Policy citations shown below draft
- "Approve & Send" / "Save Edits" / "Reject" buttons

**Right column — Intelligence:**
- Contact profile: status, company, account value, churn risk %
- Agent reasoning trace (collapsible — Thought/Action/Observation/Decision blocks)
- RAG knowledge sources used (with similarity scores)
- Agent run metadata (decision, action, duration, tool calls)

### Page 3: Analytics Dashboard

- **KPI cards**: Total, Escalated, Needs Human, Auto Replied, Spam, Avg Confidence, Avg Sentiment, At-Risk Contacts
- **Sentiment trend**: Line chart of daily average sentiment score (-1 to +1)
- **Category breakdown**: Pie chart + bar chart
- **Public reputation**: Mock G2/Trustpilot/Capterra data with star ratings, trend, top complaints
- **Rate cards**: Escalation rate, auto-reply rate, avg confidence bar gauges

---

## Special Scenarios Handled

These are the critical scenarios from the assessment that the system handles correctly:

### 🔒 Ransomware Email
- **Triggered by**: "BTC", "dark web", "ransom", "pay immediately"
- **Heuristic catches it** before LLM (0ms)
- **Result**: `flag_security` → Critical escalation → security@company.com + CTO notified
- **NEVER auto-replies** to attacker — this is a disqualification criterion

### ⚖️ Cease and Desist Letter
- **Triggered by**: "cease and desist", "attorney", "lawsuit", "legal action"
- **Heuristic catches it** before LLM (0ms)
- **Result**: `flag_legal` → Critical escalation → legal@company.com
- **NEVER auto-replies** — this is a disqualification criterion

### 📋 GDPR Data Request
- **Triggered by**: "GDPR", "data portability", "right to erasure", "Article 17/20"
- **Heuristic catches it** before LLM (0ms)
- **Result**: `gdpr_compliance` workflow:
  1. Escalation → dpo@company.com
  2. Compliance ticket created
  3. **Formal GDPR acknowledgement drafted** (cites 30-day statutory window, NOT a generic reply)
  4. Draft awaits human approval before sending

### 😤 Churn Risk Customer (3+ unanswered negative emails)
- **Detected by**: `sentiment_tracker.py` — counts consecutive negative emails per sender
- **Result**: Churn risk score elevated → escalate to Account Manager + VP Sales
- **RAG retrieves**: VIP churn retention playbook from `refund_policy.md`

### 🤖 Chatbot Gave Wrong Info
- **RAG retrieves**: Actual refund policy text
- **LLM compares**: What chatbot said vs what policy says
- **Draft includes**: Correction + policy citation + apology
- **Escalation if**: Significant discrepancy (compliance risk)

---

## Troubleshooting

### Problem: Backend won't start — "HUGGINGFACE_API_KEY missing"
```
Fix: Open .env and set HUGGINGFACE_API_KEY=hf_your_real_key
```

### Problem: `seed_rag.py` takes forever
```
Normal: First run downloads ~90MB model. Subsequent runs: ~30 seconds.
Check: Is your internet connection working?
```

### Problem: AI processing is very slow (60+ seconds per email)
```
Normal: Mistral-7B on free HuggingFace tier can be slow.
Options:
  1. Wait — subsequent calls are faster (model stays warm for ~15 min)
  2. Use the dry-run mode first: POST /api/agent/dry-run/{id}
  3. Only critical emails need AI — spam/legal/security use heuristics only
```

### Problem: "Module not found" errors in Python
```
Fix: cd backend && pip install -r requirements.txt
Make sure you're using Python 3.10+: python --version
```

### Problem: Frontend shows blank / can't connect to backend
```
Check:
  1. Is backend running? curl http://localhost:8000/api/health
  2. Is vite.config.js proxying correctly? Should have: proxy: { '/api': 'http://localhost:8000' }
  3. Any CORS error in browser console? Add your origin to ALLOWED_ORIGINS in .env
```

### Problem: "ChromaDB collection not found" error
```
Fix: Run python -m scripts.seed_rag before processing any emails
```

### Problem: Inbox is empty after replay_emails
```
Check: python -m scripts.replay_emails --batch
Look for errors — ensure email-data-advanced.json exists in SenAI2/ folder
Try manually: POST http://localhost:8000/api/emails/ingest with a test email
```

---

## Quick Verification Checklist

Run these commands in order to verify everything works:

```powershell
# 1. Backend health
Invoke-WebRequest -Uri "http://localhost:8000/api/health" | Select-Object -ExpandProperty Content

# 2. Analytics (should return zeros if no emails yet)
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/summary" | Select-Object -ExpandProperty Content

# 3. Test RAG search (after seeding)
Invoke-WebRequest -Uri "http://localhost:8000/api/rag/search?q=refund+policy" | Select-Object -ExpandProperty Content

# 4. Ingest a test email
$body = '{"message_id":"test_001","sender":"test@example.com","subject":"Test","body":"I need help","timestamp":"2024-01-01T00:00:00Z","thread_id":"t1"}'
Invoke-WebRequest -Uri "http://localhost:8000/api/emails/ingest" -Method POST -ContentType "application/json" -Body $body | Select-Object -ExpandProperty Content

# 5. Check inbox
Invoke-WebRequest -Uri "http://localhost:8000/api/emails" | Select-Object -ExpandProperty Content
```

---

*Built for SenAI AI Intern Technical Assessment · June 2026*  
*Stack: Python 3.10 · FastAPI · LangGraph · ChromaDB · SQLite · React · Vite*
