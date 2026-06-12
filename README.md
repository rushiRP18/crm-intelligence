# 🤖 CRM Intelligence Platform
> **AI-Powered Autonomous Email Triage, Semantic RAG Routing, and Human-in-the-Loop Dashboard**

The **CRM Intelligence Platform** is an enterprise-grade AI triage engine built with a FastAPI backend and a Vite+React frontend. It automatically ingests customer support emails, analyzes their sentiment and urgency, queries internal knowledge base policies using semantic vector search (RAG), and decides on the best next action (e.g. drafting a reply, escalation, or support ticket creation).

---

## 🚀 Key Features

* **⚡ Dual-Layer Ingestion & Triage**:
  * **Heuristic pre-filters** run synchronously in **under 10ms** to catch obvious spam, security threats (ransomware), compliance risks, and legal threats before any heavy LLM operations are triggered.
  * **LangGraph state machine** handles processing in the background, routing the email through specialized decision and action paths.
* **🧠 Context-Aware Semantic RAG**:
  * Chunks corporate policy documents (refunds, pricing, SLAs, API documentation) using a recursive character text splitter.
  * Generates 384-dimensional dense vectors using a local CPU-bound `sentence-transformers/all-MiniLM-L6-v2` model.
  * Performs cosine similarity matching in a persistent `ChromaDB` vector database, feeding relevant context directly into the LLM's prompt.
* **🔒 Automatic Safety Isolation**:
  * Outright flags and escalates **Cease & Desist** letters or **Ransomware** threats to Legal and SecOps desks, bypassing auto-reply nodes completely to prevent legal liabilities.
  * Detects **GDPR Article 17/20** compliance requests and creates a data exportation ticket for the Data Protection Officer (DPO) with a statutory 30-day notice draft.
* **🛡️ Rule-Based LLM Fallback (Zero Downtime)**:
  * Restructures the HuggingFace endpoint provider to bypass newer library routing bugs that cause "Novita API" authorization errors.
  * Dynamically drops back to a robust, deterministic rule-based keyword classifier if the HuggingFace API is rate-limited, offline, or times out.
* **📊 Interactive Dark-Mode Dashboard**:
  * **Mission Control (Inbox)**: Real-time list of all emails, categorized by urgency, status, and sentiment with automatic WebSocket-driven refresh.
  * **Thread Workspace**: A three-column review panel containing full email histories, detected entities, editable AI drafts with source citations, and collapsible agent reasoning traces.
  * **Analytics Panel**: Renders global summaries, public brand reputation (G2/Trustpilot reviews), category breakdowns, and a dual-axis line graph overlaying daily average sentiment with email volume.

---

## 🛠️ Technical Stack & Justifications

The CRM Intelligence Platform is built on a decoupled architecture designed for local execution, low latency, and clear separation of concerns:

### ⚙️ Backend & Database
* **FastAPI**: Provides a high-performance web framework. Its native `BackgroundTasks` queue runs heavy LangGraph AI processes asynchronously, letting the API respond to ingestion requests in under 100ms.
* **SQLAlchemy & SQLite**: SQLite serves as a lightweight, zero-setup relational database. SQLAlchemy ORM manages transactional sessions and models (emails, threads, contacts, drafts) with clean, parameter-protected query execution.
* **Pydantic**: Enforces strict runtime data validation and schema serialization at all API boundaries.

### 🧠 AI & Agent Orchestration
* **LangGraph**: Enables stateful, multi-actor workflows. It models the agent as a cyclic graph, letting us execute complex conditional routing logic (e.g. bypassing auto-replies for legal/security threats and routing compliance issues to a DPO).
* **LangSmith**: Used for LLM observability and evaluation. It captures full run execution traces, latency metrics, input/output prompt payloads, and tool execution logs for all node runs in our agent pipeline. This provides transparent debugging, prompt tracing, and performance evaluation, which is vital for production agent systems.
* **ChromaDB**: An embedded vector store that runs entirely in-process. It stores and queries document metadata and vectors with local persistence and zero setup.
* **Model Choices**:
  * **mistralai/Mistral-7B-Instruct-v0.3**: Hand-picked for robust instruction-following and reliable JSON extraction.
  * **sentence-transformers/all-MiniLM-L6-v2**: A lightweight (~90MB) local model that generates 384-dimensional embeddings on the CPU in milliseconds, avoiding external API latency and costs.

### 🎨 Frontend UI
* **React & Vite**: React provides a modular component-driven architecture for rendering real-time dashboard data. Vite acts as the build system, providing instant hot-reloading.
* **Recharts & Lucide React**: Recharts powers our clean SVG line charts and category volume graphs, and Lucide React supplies modern dashboard iconography.

---

## 🏗️ System Architecture

```text
       [Inbound Email]
              │
              ▼
    Heuristic Pre-Filter (sub-10ms) ────────► (Spam/Threat detected?) ──► YES ──► Write to DB (Exit)
              │                                                                 (LLM Bypassed)
              ▼ NO
    ======================================
    LANGGRAPH STATE MACHINE (Asynchronous)
    ======================================
    1. Preprocess State
    2. Load Prior Thread History
    3. Retrieve RAG Policy Context (ChromaDB)
    4. Classify Email Urgency/Sentiment (Mistral-7B / Local Fallback)
    5. Evaluate Business & Churn Risk
    6. Execute Decision Routing Matrix
              │
              ├─► "draft_reply"       ──► 7. Generate Reply Draft (Cites policies)
              ├─► "escalate_human"    ──► 8. Prepare Review Brief for Agent
              ├─► "flag_legal"        ──► 9. Route to Legal Desk (Bypass auto-reply)
              ├─► "flag_security"     ──► 10. Route to Security Desk (Bypass auto-reply)
              ├─► "gdpr_compliance"   ──► 11. Create Ticket + Draft Ack (30-day notice)
              └─► "create_ticket"     ──► 12. Create Support/Bug Ticket
              │
              ▼
    13. Persist Node ──► Write database records ──► Broadcast via WebSockets
```

---

## 🛠️ Recent Improvements & Fixes

1. **Dynamic Analytics Anchoring**:
   * *The Problem*: Because the seeded test dataset contains timestamps from late 2023 / early 2024 and the current time is 2026, relative filters like `since = datetime.utcnow() - timedelta(days=30)` returned blank graphs.
   * *The Fix*: The backend analytics queries now scan the database for the latest email timestamp. If that timestamp is in the past, it dynamically anchors the query window to the database's date range, displaying the seeded email graphs correctly.
2. **Recharts Volume Overlay Chart**:
   * *The Problem*: The frontend sentiment graph was look-up mismatched on database keys (`count` vs `email_count`) and used secondary Y-axes without mapping a right-aligned `<YAxis>` component, causing chart rendering errors.
   * *The Fix*: Updated the React graphing library to align keys and added a right-oriented Y-axis to overlay daily sentiment averages with total email volume.
3. **Novita AI / HuggingFace Provider Patch**:
   * *The Problem*: Recent updates to `langchain-huggingface` routed free inference requests to novita.ai by default, returning validation errors.
   * *The Fix*: Reconfigured the backend classifier to use `provider="hf-inference"` and added an exception handler to fallback to local keyword classifications if credentials or connection issues occur.

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python 3.10+** (with pip)
* **Node.js 18+** (with npm)
* **HuggingFace Access Token** (`hf_...`) — [Get one here](https://huggingface.co/settings/tokens)

### 1. Setup Environment
Copy the env template inside the project root and fill in your keys:
```bash
cp .env.example .env

# Edit .env and paste your HuggingFace key:
# HUGGINGFACE_API_KEY=hf_your_key_here
```

### 2. Install Python Dependencies
Open your terminal inside the `backend/` directory:
```bash
cd backend
pip install -r requirements.txt
```
*(Note: First run downloads the embedding model `sentence-transformers/all-MiniLM-L6-v2` (~90MB) to your local cache).*

### 3. Seed Vector Database
Initialize your ChromaDB collection by loading the policy documents:
```bash
python -m scripts.seed_rag
```
Expected output:
```text
Loading knowledge base documents...
Loaded 6 documents, 6 chunks before splitting
Splitting into smaller chunks...
Created 287 chunks
Embedding and storing in ChromaDB...
SUCCESS: 287 chunks stored in ChromaDB
Test queries passed ✓
```

### 4. Run Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger docs will be hosted at: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 5. Install & Run Frontend Dashboard
Open a new terminal session in the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```
Open your browser to: [http://localhost:3000](http://localhost:3000)

### 6. Ingest Test Dataset
With your backend server running, seed the support inbox:
```bash
cd backend
# Batch upload (fastest)
python -m scripts.replay_emails --batch

# OR stream mode (1 email per second)
python -m scripts.replay_emails --speed 1.0
```
*Tip: Go to the **Analytics Dashboard** and select **Last 180 days** or **Last 365 days** from the dropdown to view the full analytics of the imported emails.*

---

## 📁 Repository Structure

```text
crm-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI core config and WS handlers
│   │   ├── config.py            # Pydantic Settings validations
│   │   ├── database.py          # SQLite DB engine
│   │   ├── models/              # SQLAlchemy model definitions (10 tables)
│   │   ├── api/                 # FastAPI routes (emails, drafts, analytics, etc.)
│   │   ├── agent/               # LangGraph workflow loops and ReAct state
│   │   ├── rag/                 # ChromaDB query utilities and MiniLM loader
│   │   └── services/            # Sentiment tracking & pre-filter engines
│   ├── knowledge_base/          # Markdown corporate policy rules
│   └── scripts/
│       ├── seed_rag.py          # Vector database loader
│       └── replay_emails.py     # Email ingest replayer
└── frontend/
    └── src/
        ├── pages/
        │   ├── InboxPage.jsx    # Filterable message list
        │   ├── ThreadPage.jsx   # 3-column workspace workspace
        │   └── AnalyticsPage.jsx # Recharts dashboard
        └── lib/api.js           # HTTP Axios client
```

---

## 🔑 Key Configurations (`.env`)

| Key | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `HUGGINGFACE_API_KEY` | Yes | - | API Token for HuggingFace model calls |
| `LANGCHAIN_API_KEY` | No | - | LangSmith API token (for pipeline tracing) |
| `LANGCHAIN_TRACING_V2` | No | `false` | Set to `true` to enable LangSmith tracking |
| `DATABASE_URL` | Yes | `sqlite:///./crm_intelligence.db` | Local SQLite database file path |
| `CHROMA_PERSIST_DIR` | Yes | `chroma_db/` | Directory where ChromaDB embeds are saved |
| `HF_LLM_MODEL` | No | `mistralai/Mistral-7B-Instruct-v0.3` | HuggingFace text-generation target model |

---

## 📊 Observability with LangSmith
If `LANGCHAIN_TRACING_V2=true` is enabled, all agent thought patterns, RAG searches, tool executions, and LLM prompts will be trace-logged. View execution tracks in your project dashboard at: [https://smith.langchain.com](https://smith.langchain.com).
