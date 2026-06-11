"""
LangGraph Workflow Graph.

Assembles all nodes into a stateful directed graph with conditional routing.
This is the core of the autonomous triage agent.
"""
import time
from functools import partial
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END
from langsmith import traceable

from app.agent.state import AgentState
from app.agent.nodes import (
    preprocess_email_node,
    fetch_thread_history_node,
    retrieve_rag_context_node,
    classify_email_node,
    evaluate_risk_node,
    decision_node,
    action_draft_reply_node,
    action_escalate_human_node,
    action_flag_legal_node,
    action_flag_security_node,
    action_gdpr_compliance_node,
    action_create_ticket_node,
    action_mark_spam_node,
    persist_results_node,
)
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def route_decision(state: AgentState) -> str:
    """Conditional edge: route from decision_node to the correct action node."""
    decision = state.get("decision", "escalate_human")
    routes = {
        "draft_reply": "action_draft_reply",
        "escalate_human": "action_escalate_human",
        "flag_legal": "action_flag_legal",
        "flag_security": "action_flag_security",
        "gdpr_compliance": "action_gdpr_compliance",
        "create_ticket": "action_create_ticket",
        "mark_spam": "action_mark_spam",
        "mark_internal": "action_mark_spam",  # handled same as spam for routing
    }
    return routes.get(decision, "action_escalate_human")


def build_graph(db: Session) -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    Returns a compiled graph ready to invoke.
    """
    builder = StateGraph(AgentState)

    # ── Add nodes ──────────────────────────────────────────────────────────
    builder.add_node("preprocess", preprocess_email_node)
    builder.add_node("fetch_thread", partial(fetch_thread_history_node, db=db))
    builder.add_node("retrieve_rag", retrieve_rag_context_node)
    builder.add_node("classify", classify_email_node)
    builder.add_node("evaluate_risk", partial(evaluate_risk_node, db=db))
    builder.add_node("decide", decision_node)

    # Action nodes
    builder.add_node("action_draft_reply", partial(action_draft_reply_node, db=db))
    builder.add_node("action_escalate_human", partial(action_escalate_human_node, db=db))
    builder.add_node("action_flag_legal", partial(action_flag_legal_node, db=db))
    builder.add_node("action_flag_security", partial(action_flag_security_node, db=db))
    builder.add_node("action_gdpr_compliance", partial(action_gdpr_compliance_node, db=db))
    builder.add_node("action_create_ticket", partial(action_create_ticket_node, db=db))
    builder.add_node("action_mark_spam", action_mark_spam_node)

    # ── Set entry point ────────────────────────────────────────────────────
    builder.set_entry_point("preprocess")

    # ── Add edges (linear flow) ────────────────────────────────────────────
    builder.add_edge("preprocess", "fetch_thread")
    builder.add_edge("fetch_thread", "retrieve_rag")
    builder.add_edge("retrieve_rag", "classify")
    builder.add_edge("classify", "evaluate_risk")
    builder.add_edge("evaluate_risk", "decide")

    # ── Conditional routing from decision node ─────────────────────────────
    builder.add_conditional_edges(
        "decide",
        route_decision,
        {
            "action_draft_reply": "action_draft_reply",
            "action_escalate_human": "action_escalate_human",
            "action_flag_legal": "action_flag_legal",
            "action_flag_security": "action_flag_security",
            "action_gdpr_compliance": "action_gdpr_compliance",
            "action_create_ticket": "action_create_ticket",
            "action_mark_spam": "action_mark_spam",
        },
    )

    # ── All action nodes lead to END ───────────────────────────────────────
    for action_node in [
        "action_draft_reply", "action_escalate_human", "action_flag_legal",
        "action_flag_security", "action_gdpr_compliance", "action_create_ticket",
        "action_mark_spam",
    ]:
        builder.add_edge(action_node, END)

    return builder.compile()


@traceable(name="crm/agent/run", tags=["agent"])
def run_agent(
    db: Session,
    email_id: int,
    message_id: str,
    sender: str,
    subject: str | None,
    body: str | None,
    thread_id_str: str,
    heuristic_flags: dict,
    dry_run: bool = False,
) -> dict:
    """
    Execute the full LangGraph triage workflow for a single email.
    Tagged for LangSmith tracing.

    Returns the final agent state dict.
    """
    start_time = time.time()

    initial_state: AgentState = {
        "email_id": email_id,
        "message_id": message_id,
        "sender": sender,
        "subject": subject or "",
        "body": body or "",
        "thread_id_str": thread_id_str,
        "thread_history": [],
        "rag_context": [],
        "web_intel": None,
        "heuristic_flags": heuristic_flags,
        "classification": {},
        "reasoning_trace": [],
        "tool_calls_count": 0,
        "tool_calls_log": [],
        "max_tool_calls": settings.max_agent_tool_calls,
        "decision": "",
        "draft": None,
        "escalation_brief": None,
        "final_action": "",
        "dry_run": dry_run,
        "error": None,
    }

    try:
        graph = build_graph(db)
        final_state = graph.invoke(initial_state)

        # Persist results
        persist_results_node(final_state, db, start_time)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Agent completed: email={message_id} "
            f"decision={final_state.get('decision')} "
            f"action={final_state.get('final_action')} "
            f"duration={duration_ms:.0f}ms"
        )
        return final_state

    except Exception as e:
        logger.error(f"Agent run failed for email {message_id}: {e}")
        # Persist failure with human escalation
        from app.models.email import Email
        from app.models.agent_run import AgentRun
        email = db.query(Email).filter(Email.id == email_id).first()
        if email and not dry_run:
            email.status = "escalated"
            email.requires_human = True
            email.escalation_reason = f"Agent error: {str(e)[:200]}"
            run = AgentRun(
                email_id=email_id,
                reasoning_trace=f"Agent failed with error: {e}",
                decision="escalate_human",
                final_action="agent_error_escalated",
                dry_run=dry_run,
                error=str(e),
            )
            db.add(run)
            db.commit()
        raise
