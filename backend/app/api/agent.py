"""Agent API routes including dry-run."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email
from app.models.thread import Thread
from app.models.agent_run import AgentRun
from app.agent.graph import run_agent
from app.utils.exceptions import EmailNotFound

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/dry-run/{email_id}")
def agent_dry_run(email_id: int, db: Session = Depends(get_db)):
    """
    Run the LangGraph agent in dry-run / planning mode.
    Returns the full reasoning trace, classification, RAG context,
    and draft preview WITHOUT executing any side effects (no DB writes,
    no emails sent, no tickets created).
    Useful for validating agent behaviour on historical emails.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise EmailNotFound(email_id)

    thread = db.query(Thread).filter(Thread.id == email.thread_id).first()
    final_state = run_agent(
        db=db,
        email_id=email.id,
        message_id=email.message_id,
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        thread_id_str=thread.thread_id if thread else "",
        heuristic_flags=email.heuristic_flags or {},
        dry_run=True,
    )
    return {
        "email_id": email_id,
        "dry_run": True,
        "decision": final_state.get("decision"),
        "final_action": final_state.get("final_action"),
        "reasoning_trace": "\n\n".join(final_state.get("reasoning_trace", [])),
        "rag_context": final_state.get("rag_context", []),
        "classification": final_state.get("classification", {}),
        "draft_preview": final_state.get("draft"),
    }


@router.get("/runs/{email_id}")
def get_agent_run(email_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the stored agent run record for a given email.
    Includes the full reasoning trace, all tool calls, and timing.
    """
    run = db.query(AgentRun).filter(AgentRun.email_id == email_id).first()
    if not run:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "AGENT_RUN_NOT_FOUND",
                "message": f"No agent run found for email {email_id}",
            },
        )
    return {
        "id": run.id,
        "email_id": run.email_id,
        "reasoning_trace": run.reasoning_trace,
        "tool_calls": run.tool_calls,
        "decision": run.decision,
        "draft_reply": run.draft_reply,
        "final_action": run.final_action,
        "run_duration_ms": run.run_duration_ms,
        "dry_run": run.dry_run,
        "created_at": run.created_at,
    }
