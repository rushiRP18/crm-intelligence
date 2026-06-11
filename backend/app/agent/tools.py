"""
LangChain Tool Definitions for the CRM Triage Agent.

All tools are decorated with @tool and return structured dicts.
These are injected into the LangGraph agent nodes.
"""
import time
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.tools import tool
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ── Tool: search_knowledge_base ──────────────────────────────────────────────

def make_search_knowledge_base_tool(db: Session):
    """Factory returning a tool with db session bound via closure."""

    def search_knowledge_base(query: str) -> dict:
        """
        Search the internal knowledge base using semantic similarity.
        Returns top-3 relevant policy chunks with similarity scores.
        Use this to ground replies in company policy (pricing, SLA, refund, etc).
        """
        from app.rag.retriever import search_knowledge_base as rag_search
        try:
            chunks = rag_search(query, k=3)
            return {
                "query": query,
                "chunks": chunks,
                "count": len(chunks),
            }
        except Exception as e:
            logger.error(f"search_knowledge_base failed: {e}")
            return {"query": query, "chunks": [], "count": 0, "error": str(e)}

    return search_knowledge_base


# ── Tool: get_thread_history ─────────────────────────────────────────────────

def make_get_thread_history_tool(db: Session):
    def get_thread_history(sender_email: str) -> dict:
        """
        Retrieve all emails from a specific sender, ordered by time.
        Use this to understand the full conversation context before deciding.
        """
        from app.services.thread_builder import get_sender_history
        history = get_sender_history(db, sender_email)
        return {
            "sender": sender_email,
            "total_emails": len(history),
            "history": history,
        }
    return get_thread_history


# ── Tool: get_contact_profile ────────────────────────────────────────────────

def make_get_contact_profile_tool(db: Session):
    def get_contact_profile(email: str) -> dict:
        """
        Fetch CRM profile for a contact: VIP status, account value, churn risk.
        Use this to determine the business impact of this email.
        """
        from app.models.contact import Contact
        contact = db.query(Contact).filter(Contact.email == email.lower()).first()
        if not contact:
            return {"email": email, "found": False, "status": "Unknown", "account_value": 0, "churn_risk_score": 0}
        return {
            "email": contact.email,
            "found": True,
            "name": contact.name,
            "company": contact.company,
            "status": contact.status,
            "account_value": contact.account_value,
            "churn_risk_score": contact.churn_risk_score,
            "last_contact_at": contact.last_contact_at.isoformat() if contact.last_contact_at else None,
        }
    return get_contact_profile


# ── Tool: check_account_status ───────────────────────────────────────────────

def make_check_account_status_tool(db: Session):
    def check_account_status(email: str) -> dict:
        """
        Check billing/subscription status for a contact.
        Returns subscription tier, payment status, and any overdue invoices.
        Use before making pricing or SLA decisions.
        """
        from app.models.contact import Contact
        contact = db.query(Contact).filter(Contact.email == email.lower()).first()
        # Mock billing data based on contact info
        tier_map = {
            "bob.jones@enterprise.net": {"tier": "Enterprise", "status": "Active", "renewal_hold": True, "mrr": 2400},
            "alice.smith@greenlight-npo.org": {"tier": "Standard", "status": "Active", "renewal_hold": False, "mrr": 99},
            "karen.w@retail-co.com": {"tier": "Pro", "status": "Active", "renewal_hold": False, "mrr": 299},
        }
        billing = tier_map.get(email.lower(), {"tier": "Standard", "status": "Active", "renewal_hold": False, "mrr": 99})
        if contact:
            billing["account_value"] = contact.account_value
        return billing
    return check_account_status


# ── Tool: draft_reply ────────────────────────────────────────────────────────

def make_draft_reply_tool(llm):
    def draft_reply(context: str, tone: str = "professional", policy_refs: list[str] | None = None) -> dict:
        """
        Generate a contextual reply draft citing specific policies.
        tone options: professional | empathetic | formal
        Only call this for non-critical, non-legal, non-security emails.
        """
        from langchain_core.messages import HumanMessage
        refs_text = ", ".join(policy_refs) if policy_refs else "general knowledge"
        prompt = f"""You are a professional customer support agent. Write a helpful, {tone} reply to the following email context.
Reference these policies: {refs_text}

Context:
{context}

Write ONLY the reply text, no subject line, no 'Dear' prefix. Keep it under 200 words. Be specific and cite policies."""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            reply_text = response.content if hasattr(response, "content") else str(response)
            return {"draft": reply_text.strip(), "tone": tone, "policy_refs": policy_refs or []}
        except Exception as e:
            return {"draft": f"Thank you for reaching out. We will respond shortly. [Draft generation failed: {e}]", "tone": tone, "policy_refs": []}
    return draft_reply


# ── Tool: escalate_to_human ──────────────────────────────────────────────────

def make_escalate_to_human_tool(db: Session):
    def escalate_to_human(email_id: int, reason: str, priority: str = "High") -> dict:
        """
        Route email to human review queue with a pre-filled context brief.
        Use when: requires_human=True, confidence < 0.70, or complex situation.
        priority options: Critical | High | Medium
        """
        from app.models.escalation import Escalation
        from app.models.email import Email
        from app.services.audit_service import log_action

        email = db.query(Email).filter(Email.id == email_id).first()
        brief = f"ESCALATION BRIEF\nEmail: {email.message_id if email else email_id}\nSender: {email.sender if email else 'unknown'}\nReason: {reason}\nPriority: {priority}\nTimestamp: {datetime.utcnow().isoformat()}"

        escalation = Escalation(
            email_id=email_id,
            escalation_type="human",
            reason=reason,
            priority=priority,
            assigned_to="support-team@company.com",
            brief=brief,
            status="open",
        )
        db.add(escalation)
        db.commit()

        log_action(db, "email", email_id, "escalated_to_human", after_state={"reason": reason, "priority": priority})
        return {"escalated": True, "escalation_type": "human", "priority": priority, "reason": reason}
    return escalate_to_human


# ── Tool: create_internal_ticket ─────────────────────────────────────────────

def make_create_ticket_tool(db: Session):
    def create_internal_ticket(email_id: int, title: str, body: str, assignee: str = "support@company.com", ticket_type: str = "support") -> dict:
        """
        Create an internal support or engineering ticket.
        Use for bug reports, compliance tasks, or follow-up action items.
        ticket_type options: bug | compliance | legal | support
        """
        from app.models.ticket import Ticket
        from app.services.audit_service import log_action

        ticket = Ticket(
            email_id=email_id,
            title=title,
            body=body,
            assignee=assignee,
            priority="High",
            status="Open",
            ticket_type=ticket_type,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        log_action(db, "ticket", ticket.id, "created", after_state={"title": title, "type": ticket_type})
        return {"ticket_created": True, "ticket_id": ticket.id, "title": title, "assignee": assignee}
    return create_internal_ticket


# ── Tool: flag_for_legal ─────────────────────────────────────────────────────

def make_flag_for_legal_tool(db: Session):
    def flag_for_legal(email_id: int, issue_type: str) -> dict:
        """
        Flag email for immediate legal team review.
        MUST be called for: cease & desist, trademark threats, GDPR requests, legal correspondence.
        NEVER auto-reply after calling this tool.
        issue_type: cease_desist | trademark | gdpr | litigation | compliance
        """
        from app.models.escalation import Escalation
        from app.models.email import Email
        from app.services.audit_service import log_action

        email = db.query(Email).filter(Email.id == email_id).first()
        brief = (
            f"LEGAL FLAG — URGENT\n"
            f"Email: {email.message_id if email else email_id}\n"
            f"Sender: {email.sender if email else 'unknown'}\n"
            f"Issue Type: {issue_type}\n"
            f"DO NOT respond to sender directly.\n"
            f"Flagged at: {datetime.utcnow().isoformat()}\n"
            f"Body Preview: {(email.body or '')[:300] if email else 'unavailable'}"
        )

        escalation = Escalation(
            email_id=email_id,
            escalation_type="legal",
            reason=f"Legal issue: {issue_type}",
            priority="Critical",
            assigned_to="legal@company.com",
            brief=brief,
            status="open",
        )
        db.add(escalation)
        db.commit()

        log_action(db, "email", email_id, "flagged_for_legal", after_state={"issue_type": issue_type})
        logger.warning(f"LEGAL FLAG: email_id={email_id} issue={issue_type}")
        return {"flagged": True, "escalation_type": "legal", "issue_type": issue_type, "assigned_to": "legal@company.com"}
    return flag_for_legal


# ── Tool: flag_for_security ──────────────────────────────────────────────────

def make_flag_for_security_tool(db: Session):
    def flag_for_security(email_id: int, threat_type: str) -> dict:
        """
        Immediately escalate to security team.
        MUST be called for: ransomware threats, suspicious logins, data breach claims.
        NEVER auto-reply to security threats.
        threat_type: ransomware | suspicious_login | data_breach | phishing
        """
        from app.models.escalation import Escalation
        from app.models.email import Email
        from app.services.audit_service import log_action

        email = db.query(Email).filter(Email.id == email_id).first()
        brief = (
            f"⚠️ SECURITY INCIDENT — CRITICAL\n"
            f"Email: {email.message_id if email else email_id}\n"
            f"Sender: {email.sender if email else 'unknown'}\n"
            f"Threat Type: {threat_type}\n"
            f"IMMEDIATE ACTION REQUIRED. DO NOT reply to sender.\n"
            f"Notify: security@company.com + CTO\n"
            f"Detected at: {datetime.utcnow().isoformat()}"
        )

        escalation = Escalation(
            email_id=email_id,
            escalation_type="security",
            reason=f"Security threat: {threat_type}",
            priority="Critical",
            assigned_to="security@company.com",
            brief=brief,
            status="open",
        )
        db.add(escalation)
        db.commit()

        log_action(db, "email", email_id, "flagged_for_security", after_state={"threat_type": threat_type})
        logger.critical(f"SECURITY THREAT: email_id={email_id} type={threat_type}")
        return {"flagged": True, "escalation_type": "security", "threat_type": threat_type, "notify": ["security@company.com", "cto@company.com"]}
    return flag_for_security


# ── Tool: send_auto_reply ────────────────────────────────────────────────────

def make_send_auto_reply_tool(db: Session):
    def send_auto_reply(email_id: int, draft_id: int) -> dict:
        """
        Approve and send an auto-reply.
        ONLY call for non-critical, non-legal, non-security emails.
        NEVER call for: spam, ransomware, legal threats, GDPR requests, Critical urgency.
        """
        from app.models.draft import Draft
        from app.models.email import Email
        from app.services.audit_service import log_action

        draft = db.query(Draft).filter(Draft.id == draft_id).first()
        if not draft:
            return {"sent": False, "error": "Draft not found"}

        draft.status = "sent"
        draft.approved_at = datetime.utcnow()
        draft.approved_by = "system"

        email = db.query(Email).filter(Email.id == email_id).first()
        if email:
            email.status = "resolved"

        db.commit()
        log_action(db, "draft", draft_id, "auto_sent")
        return {"sent": True, "draft_id": draft_id, "email_id": email_id}
    return send_auto_reply
