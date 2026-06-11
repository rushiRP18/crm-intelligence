"""
CRM Intelligence Platform — FastAPI Application Entry Point.

Configures:
- CORS middleware
- Global exception handlers
- All API routers (emails, threads, contacts, drafts, analytics, rag,
                   intelligence, agent, audit, tickets)
- WebSocket endpoint for real-time dashboard updates
- LangSmith tracing setup
- Database table initialisation on startup
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, configure_langsmith
from app.database import init_db
from app.utils.exceptions import CRMException, crm_exception_handler, generic_exception_handler
from app.utils.logging import get_logger, silence_sqlalchemy_logs


logger = get_logger(__name__)
settings = get_settings()

print("HF SETTING =", repr(settings.huggingface_api_key))
print("MODEL =", settings.hf_llm_model)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle handler.
    Runs once on boot: configures LangSmith tracing and initialises DB tables.
    """
    configure_langsmith(settings)
    import os

    print("HF_TOKEN =", os.getenv("HF_TOKEN"))
    print("HUGGINGFACEHUB_API_TOKEN =", os.getenv("HUGGINGFACEHUB_API_TOKEN"))
    silence_sqlalchemy_logs()   # suppress per-query SQL noise
    init_db()

    logger.info("[STARTED] CRM Intelligence Platform")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  LLM Model   : {settings.hf_llm_model}")
    logger.info(f"  Embedding   : {settings.embedding_model}")
    logger.info(f"  LangSmith   : {'enabled' if settings.langchain_api_key else 'disabled'}")

    yield  # ← application runs here

    logger.info("CRM Intelligence Platform shutting down")


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="CRM Intelligence Platform",
    description=(
        "AI-powered CRM with LangGraph agents, RAG knowledge base, "
        "real-time email triage, and human-in-the-loop draft approval."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handlers ─────────────────────────────────────────────────
app.add_exception_handler(CRMException, crm_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ── API Routers ───────────────────────────────────────────────────────────────
from app.api.emails import router as emails_router          # noqa: E402
from app.api.threads import router as threads_router        # noqa: E402
from app.api.contacts import router as contacts_router      # noqa: E402
from app.api.drafts import router as drafts_router          # noqa: E402
from app.api.analytics import router as analytics_router    # noqa: E402
from app.api.rag import router as rag_router                # noqa: E402
from app.api.intelligence import router as intel_router     # noqa: E402
from app.api.agent import router as agent_router            # noqa: E402
from app.api.audit import router as audit_router            # noqa: E402
from app.api.tickets import router as tickets_router        # noqa: E402

PREFIX = "/api"

app.include_router(emails_router,    prefix=PREFIX)
app.include_router(threads_router,   prefix=PREFIX)
app.include_router(contacts_router,  prefix=PREFIX)
app.include_router(drafts_router,    prefix=PREFIX)
app.include_router(analytics_router, prefix=PREFIX)
app.include_router(rag_router,       prefix=PREFIX)
app.include_router(intel_router,     prefix=PREFIX)
app.include_router(agent_router,     prefix=PREFIX)
app.include_router(audit_router,     prefix=PREFIX)
app.include_router(tickets_router,   prefix=PREFIX)


# ── WebSocket — real-time dashboard updates ───────────────────────────────────
class ConnectionManager:
    """
    Manages a pool of active WebSocket connections.
    The agent and ingestion layer can call `manager.broadcast(payload)` to push
    live events (new emails, status changes, escalations) to all connected clients.
    """

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"WS connected — total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug(f"WS disconnected — total={len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Serialise and send a JSON message to every connected client."""
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        # Clean up closed connections
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time CRM dashboard updates.
    Clients connect here and receive JSON push notifications whenever
    an email is ingested, processed, escalated, or resolved.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive by draining incoming pings/messages.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Health & root ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health_check():
    """Liveness probe — returns 200 when the application is running."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "env": settings.app_env,
    }


@app.get("/", tags=["Root"])
def root():
    """Root endpoint — returns API name and docs URL."""
    return {
        "message": "CRM Intelligence Platform API",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
    }
