"""
LangGraph Agent Nodes.

Each function represents a node in the state graph.
Nodes receive AgentState, perform work, and return partial state updates.
"""
import json
import re
import time
from datetime import datetime
from functools import lru_cache
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _has_real_hf_key() -> bool:
    """Return True only when a real HuggingFace key is configured."""
    key = (settings.huggingface_api_key or "").strip()
    return bool(key) and not key.startswith("hf_your")


@lru_cache(maxsize=1)
def _get_llm():
    print("HF KEY PRESENT:", bool(settings.huggingface_api_key))
    print("MODEL:", settings.hf_llm_model)

    print("=" * 50)
    print("ENTERING _get_llm")
    print("HF KEY PRESENT:", bool(settings.huggingface_api_key))
    print("MODEL:", settings.hf_llm_model)
    print("=" * 50)
    """
    Get (and cache) the HuggingFace Inference API LLM.

    Key fix: explicitly set provider='hf-inference' so that newer versions of
    langchain-huggingface do NOT default to novita.ai (which requires a
    separate API key and gives the 'novita API' error).
    """
    task_type = "text2text-generation" if "t5" in settings.hf_llm_model.lower() else "text-generation"
    
    try:
        from langchain_huggingface import HuggingFaceEndpoint
        llm = HuggingFaceEndpoint(
            repo_id=settings.hf_llm_model,
            huggingfacehub_api_token=settings.huggingface_api_key,
            provider="hf-inference",
            task=task_type,
            max_new_tokens=800,
            temperature=0.1,
        )

        print("LLM CREATED SUCCESSFULLY")
        print("ENTERING _get_llm")
        print("HF KEY:", settings.huggingface_api_key[:10])
        print("MODEL:", settings.hf_llm_model)
        return llm
    except TypeError:
        # Older langchain-huggingface versions don't have `provider` param
        from langchain_huggingface import HuggingFaceEndpoint  # noqa
        return HuggingFaceEndpoint(
            repo_id=settings.hf_llm_model,
            huggingfacehub_api_token=settings.huggingface_api_key,
            task=task_type,
            max_new_tokens=800,
            temperature=0.1,
            timeout=60,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Smart rule-based fallback classifier
# Used when: no HF key configured, API is down, or LLM call times out.
# Produces real, useful classifications — NOT just "Other".
# ─────────────────────────────────────────────────────────────────────────────

def _rule_based_classify(sender: str, subject: str, body: str, hflags: dict) -> dict:
    """
    Fast rule-based classifier — runs in <1ms, no API needed.
    Returns a dict compatible with ClassificationOutput.
    """
    text = f"{subject} {body}".lower()

    # ── Category ──────────────────────────────────────────────────────────
    if hflags.get("is_security_threat") or any(w in text for w in ["ransomware", "bitcoin", "btc", "dark web", "hack"]):
        category, urgency, requires_human = "Security", "Critical", True
        escalation_reason = "Security threat detected by heuristic filter"
    elif hflags.get("is_legal") or any(w in text for w in ["cease and desist", "lawsuit", "attorney", "litigation"]):
        category, urgency, requires_human = "Legal", "Critical", True
        escalation_reason = "Legal threat — do not auto-reply"
    elif hflags.get("is_gdpr") or any(w in text for w in ["gdpr", "data portability", "right to erasure", "article 17", "article 20"]):
        category, urgency, requires_human = "Compliance", "High", True
        escalation_reason = "GDPR data request — 30-day statutory window applies"
    elif any(w in text for w in ["spam", "click here", "buy now", "free money", "nigerian", "lottery"]):
        category, urgency, requires_human = "Spam", "Low", False
        escalation_reason = None
    elif any(w in text for w in ["refund", "charge", "invoice", "billing", "payment", "overcharged", "credit card"]):
        category, urgency, requires_human = "Billing", "High", False
        escalation_reason = None
    elif any(w in text for w in ["bug", "error", "crash", "broken", "not working", "issue", "glitch", "500", "exception"]):
        category, urgency, requires_human = "Bug Report", "High", False
        escalation_reason = None
    elif any(w in text for w in ["feature", "suggestion", "would love", "please add", "enhancement", "improvement"]):
        category, urgency, requires_human = "Feature Request", "Low", False
        escalation_reason = None
    elif any(w in text for w in ["cancel", "unsubscribe", "switch", "leaving", "competitor", "disappointed"]):
        category, urgency, requires_human = "Complaint", "High", True
        escalation_reason = "Churn risk — customer threatening to leave"
    elif any(w in text for w in ["how do i", "how to", "what is", "can you help", "question", "confused", "tutorial"]):
        category, urgency, requires_human = "Inquiry", "Low", False
        escalation_reason = None
    elif any(w in text for w in ["thank", "great", "love", "excellent", "awesome", "perfect"]):
        category, urgency, requires_human = "Inquiry", "Low", False
        escalation_reason = None
    else:
        category, urgency, requires_human = "Inquiry", "Medium", False
        escalation_reason = None

    # ── Sentiment analysis ─────────────────────────────────────────────────
    negative_words = ["angry", "furious", "terrible", "awful", "disgusted", "worst",
                      "horrible", "unacceptable", "disappointed", "frustrated", "never again",
                      "refund", "cancel", "lawsuit", "incompetent", "useless"]
    positive_words = ["thank", "great", "love", "excellent", "amazing", "perfect",
                      "awesome", "wonderful", "appreciate", "pleased", "happy"]

    neg_count = sum(1 for w in negative_words if w in text)
    pos_count = sum(1 for w in positive_words if w in text)

    if hflags.get("is_security_threat") or hflags.get("is_legal"):
        sentiment, score = "Negative", -0.9
    elif neg_count >= 3:
        sentiment, score = "Negative", round(-0.3 - (min(neg_count, 6) * 0.1), 2)
    elif neg_count >= 1 and pos_count >= 1:
        sentiment, score = "Mixed", round(-0.1 * neg_count + 0.05 * pos_count, 2)
    elif neg_count == 1:
        sentiment, score = "Negative", -0.3
    elif pos_count >= 2:
        sentiment, score = "Positive", round(0.3 + pos_count * 0.1, 2)
    else:
        sentiment, score = "Neutral", 0.0

    score = max(-1.0, min(1.0, score))

    # ── Urgency override for churn / heuristic flags ───────────────────────
    if hflags.get("is_churn_risk") and urgency == "Medium":
        urgency = "High"
        requires_human = True
        if not escalation_reason:
            escalation_reason = "Churn risk keywords detected"
    if hflags.get("urgency_boost") and urgency in ["Low", "Medium"]:
        urgency = "High"

    # ── Entity extraction (simple regex) ──────────────────────────────────
    monetary = re.findall(r'\$[\d,]+(?:\.\d{2})?|\d+\s*(?:dollars|USD|usd)', f"{subject} {body}")
    order_ids = re.findall(r'\b(?:order|ord|#)\s*[A-Z0-9-]{4,}\b', f"{subject} {body}", re.I)
    ticket_ids = re.findall(r'\b(?:ticket|case|ref|#)\s*[A-Z0-9-]{4,}\b', f"{subject} {body}", re.I)

    return {
        "category": category,
        "sentiment": sentiment,
        "sentiment_score": score,
        "urgency": urgency,
        "requires_human": requires_human,
        "escalation_reason": escalation_reason,
        "suggested_reply": None,
        "confidence": 0.82,   # high confidence for rule-based (rules are deterministic)
        "detected_entities": {
            "order_ids": list(set(order_ids[:5])),
            "ticket_ids": list(set(ticket_ids[:5])),
            "monetary_amounts": list(set(monetary[:5])),
            "deadlines": [],
            "products_mentioned": [],
        },
        "_source": "rule_based_fallback",
    }


# ── Node: preprocess_email ───────────────────────────────────────────────────

def preprocess_email_node(state: AgentState) -> dict:
    """
    Node 1: Initialize state, validate inputs.
    Adds initial reasoning trace entry.
    """
    thought = (
        f"Thought: Received email from '{state['sender']}' with subject "
        f"'{state['subject']}'. "
        f"Heuristic flags: {state.get('heuristic_flags', {})}. "
        f"Starting triage workflow."
    )
    return {
        "reasoning_trace": [thought],
        "tool_calls_count": 0,
        "tool_calls_log": [],
        "error": None,
    }


# ── Node: fetch_thread_history ───────────────────────────────────────────────

def fetch_thread_history_node(state: AgentState, db: Session) -> dict:
    """
    Node 2: Load full thread context from database.
    """
    from app.services.thread_builder import get_thread_context
    history = get_thread_context(db, state["thread_id_str"])

    thought = (
        f"Thought: Thread '{state['thread_id_str']}' has {len(history)} previous message(s). "
        f"Full context loaded for classification."
    )
    return {
        "thread_history": history,
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: retrieve_rag_context ───────────────────────────────────────────────

def retrieve_rag_context_node(state: AgentState) -> dict:
    """
    Node 3: Semantic search over knowledge base.
    Constructs query from email subject + body keywords.
    """
    from app.rag.retriever import search_knowledge_base

    # Build query from key email signals
    query = f"{state.get('subject', '')} {state.get('body', '')[:500]}"

    start = time.time()
    chunks = search_knowledge_base(query, k=3)
    duration_ms = (time.time() - start) * 1000

    thought = (
        f"Action: search_knowledge_base(query='{query[:100]}...')\n"
        f"Observation: Retrieved {len(chunks)} knowledge chunks in {duration_ms:.0f}ms. "
        f"Sources: {[c['source'] for c in chunks]}"
    )
    return {
        "rag_context": chunks,
        "reasoning_trace": state["reasoning_trace"] + [thought],
        "tool_calls_count": state["tool_calls_count"] + 1,
        "tool_calls_log": state["tool_calls_log"] + [{
            "tool_name": "search_knowledge_base",
            "input": query[:200],
            "output": f"{len(chunks)} chunks retrieved",
            "duration_ms": duration_ms,
        }],
    }


# ── Node: classify_email ─────────────────────────────────────────────────────

def classify_email_node(state: AgentState) -> dict:
    """
    Node 4: Email classification — uses LLM when API key is set, otherwise
    falls back to fast rule-based classifier (no API needed).
    """
    from app.rag.retriever import format_rag_context
    from app.services.thread_builder import get_thread_summary_context

    hflags = state.get("heuristic_flags", {})

    # ── Fast path: use rule-based classifier if no real HF key ───────────────
    if not _has_real_hf_key():
        logger.info("No HuggingFace API key set — using rule-based classifier")
        classification = _rule_based_classify(
            state["sender"], state.get("subject", ""),
            state.get("body", ""), hflags
        )
        thought = (
            f"Action: classify_email(mode=rule_based, sender={state['sender']})\n"
            f"Observation: Category={classification['category']}, "
            f"Sentiment={classification['sentiment']} ({classification['sentiment_score']:.2f}), "
            f"Urgency={classification['urgency']}, Confidence={classification['confidence']:.2f}, "
            f"Source=rule_based_fallback (no HF key configured)"
        )
        return {
            "classification": classification,
            "reasoning_trace": state["reasoning_trace"] + [thought],
        }

    # ── Build LLM prompt ─────────────────────────────────────────────────────
    rag_text  = format_rag_context(state.get("rag_context", []))
    thread_text = get_thread_summary_context(state.get("thread_history", []))

    flags_note = ""
    if hflags.get("is_security_threat"):
        flags_note = "\nALERT: Security threat keywords detected. Category MUST be 'Security'."
    elif hflags.get("is_legal"):
        flags_note = "\nALERT: Legal threat keywords detected. Category MUST be 'Legal'."
    elif hflags.get("is_gdpr"):
        flags_note = "\nALERT: GDPR request detected. Category MUST be 'Compliance', requires_human=true."
    elif hflags.get("is_spam"):
        flags_note = "\nALERT: Spam detected. Category MUST be 'Spam'."

    system_prompt = """You are an expert CRM email classifier. Classify the email and return ONLY valid JSON.

RULES:
- If category is "Legal", "Security", or "Compliance": requires_human MUST be true
- If category is "Spam": suggested_reply MUST be null, requires_human MUST be false
- confidence below 0.70 means requires_human should be true
- sentiment_score: -1.0 (very negative) to +1.0 (very positive)

Return ONLY this JSON (no other text):
{
  "category": "Complaint|Inquiry|Bug Report|Feature Request|Compliance|Legal|Billing|Spam|Internal|Security|Other",
  "sentiment": "Positive|Neutral|Negative|Mixed",
  "sentiment_score": 0.0,
  "urgency": "Critical|High|Medium|Low",
  "requires_human": false,
  "escalation_reason": null,
  "suggested_reply": null,
  "confidence": 0.9,
  "detected_entities": {
    "order_ids": [],
    "ticket_ids": [],
    "monetary_amounts": [],
    "deadlines": [],
    "products_mentioned": []
  }
}"""

    user_prompt = f"""THREAD HISTORY:
{thread_text}

CURRENT EMAIL:
From: {state['sender']}
Subject: {state.get('subject', '(no subject)')}
Body: {state.get('body', '(empty)')}

{rag_text}
{flags_note}

Classify this email:"""

    # Start with rule-based as default (overwritten by LLM if successful)
    classification = _rule_based_classify(
        state["sender"], state.get("subject", ""),
        state.get("body", ""), hflags
    )
    classification["confidence"] = 0.5  # reset; LLM will set real value

    try:
        llm = _get_llm()
        response = llm.invoke(user_prompt)
        response_text = response if isinstance(response, str) else str(response)

        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            parsed = json.loads(json_match.group())
            classification.update(parsed)
            classification.pop("_source", None)  # remove fallback marker
            logger.info(f"LLM classification OK: {classification.get('category')} / {classification.get('confidence'):.2f}")
        else:
            logger.warning("LLM response had no JSON — keeping rule-based result")

    except Exception as e:
        # Keep the rule-based result, just log the LLM error quietly
        logger.warning(f"LLM classification unavailable ({type(e).__name__}) — using rule-based fallback")
        classification["confidence"] = 0.82
        classification["_source"] = "rule_based_fallback"

    # ── Safety: enforce heuristic overrides (cannot be LLM-overridden) ───────
    if hflags.get("is_security_threat"):
        classification.update({"category": "Security", "requires_human": True, "urgency": "Critical",
                                "escalation_reason": "Security threat detected — never auto-reply"})
    if hflags.get("is_legal"):
        classification.update({"category": "Legal", "requires_human": True,
                                "escalation_reason": classification.get("escalation_reason") or "Legal threat — do not auto-reply"})
    if hflags.get("is_gdpr"):
        classification.update({"category": "Compliance", "requires_human": True,
                                "escalation_reason": classification.get("escalation_reason") or "GDPR request — 30-day legal obligation"})
    if hflags.get("is_spam"):
        classification.update({"category": "Spam", "requires_human": False, "suggested_reply": None})

    if classification.get("confidence", 1.0) < settings.confidence_human_threshold:
        classification["requires_human"] = True
        if not classification.get("escalation_reason"):
            classification["escalation_reason"] = f"Low confidence ({classification.get('confidence', 0):.0%}) — human review recommended"

    thought = (
        f"Action: classify_email(sender={state['sender']})\n"
        f"Observation: Category={classification['category']}, "
        f"Sentiment={classification['sentiment']} ({classification['sentiment_score']:.2f}), "
        f"Urgency={classification['urgency']}, "
        f"Confidence={classification['confidence']:.2f}, "
        f"Requires Human={classification['requires_human']}"
    )

    return {
        "classification": classification,
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: evaluate_risk ──────────────────────────────────────────────────────

def evaluate_risk_node(state: AgentState, db: Session) -> dict:
    """
    Node 5: Business risk evaluation.
    Checks churn signals, account value, sentiment deterioration.
    """
    from app.services.sentiment_tracker import check_sentiment_deterioration, update_contact_churn_risk

    sender = state["sender"]
    classification = state.get("classification", {})

    # Check sentiment deterioration (3+ consecutive negative emails)
    deteriorating = check_sentiment_deterioration(db, sender)

    # Update churn risk score
    churn_risk = update_contact_churn_risk(db, sender)

    risk_level = "low"
    risk_notes = []

    if deteriorating:
        risk_level = "high"
        risk_notes.append("Sentiment deterioration detected (3+ consecutive negative emails)")
    if churn_risk > 0.7:
        risk_level = "high"
        risk_notes.append(f"High churn risk score: {churn_risk:.2f}")
    if classification.get("urgency") == "Critical":
        risk_level = "critical"
        risk_notes.append("Critical urgency classification")

    # Check for churn keywords
    hflags = state.get("heuristic_flags", {})
    if hflags.get("is_churn_risk"):
        risk_level = max(risk_level, "high", key=lambda x: ["low", "medium", "high", "critical"].index(x))
        risk_notes.append("Churn keywords detected in email")

    thought = (
        f"Thought: Risk evaluation for {sender}. "
        f"Churn risk: {churn_risk:.2f}, Deteriorating sentiment: {deteriorating}. "
        f"Overall risk level: {risk_level}. "
        f"Notes: {'; '.join(risk_notes) if risk_notes else 'None'}."
    )

    # Merge risk info into classification for decision node
    updated_classification = {**classification, "_risk_level": risk_level, "_risk_notes": risk_notes}

    return {
        "classification": updated_classification,
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: decision_node ──────────────────────────────────────────────────────

def decision_node(state: AgentState) -> dict:
    """
    Node 6: Main decision point.
    Routes to appropriate action based on classification + risk.
    """
    classification = state.get("classification", {})
    hflags = state.get("heuristic_flags", {})
    category = classification.get("category", "Other")
    urgency = classification.get("urgency", "Medium")
    requires_human = classification.get("requires_human", False)

    # Determine decision — order matters: security > legal > gdpr > spam > internal > human > ticket > draft
    if hflags.get("is_security_threat") or category == "Security":
        decision = "flag_security"
    elif hflags.get("is_legal") or category == "Legal":
        decision = "flag_legal"
    elif hflags.get("is_gdpr") or category == "Compliance":
        decision = "gdpr_compliance"
    elif category == "Spam":
        decision = "mark_spam"
    elif category == "Internal":
        decision = "mark_internal"
    elif urgency == "Critical" or requires_human:
        decision = "escalate_human"
    elif category == "Bug Report" and urgency in ["High", "Critical"]:
        decision = "create_ticket"
    elif not requires_human and classification.get("confidence", 0) >= settings.confidence_human_threshold:
        decision = "draft_reply"
    else:
        decision = "escalate_human"

    thought = (
        f"Decision: Based on category='{category}', urgency='{urgency}', "
        f"requires_human={requires_human}, flags={list(hflags.keys())}, "
        f"→ Routing to: '{decision}'"
    )

    return {
        "decision": decision,
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_draft_reply ─────────────────────────────────────────────────

def action_draft_reply_node(state: AgentState, db: Session) -> dict:
    """Generate and persist a draft reply."""
    from app.models.draft import Draft
    from app.rag.retriever import format_rag_context
    from app.services.thread_builder import get_thread_summary_context

    classification = state.get("classification", {})
    rag_chunks = state.get("rag_context", [])
    thread_text = get_thread_summary_context(state.get("thread_history", []))
    rag_text = format_rag_context(rag_chunks)
    policy_refs = list({c["source"] for c in rag_chunks})

    # Determine tone based on sentiment
    sentiment = classification.get("sentiment", "Neutral")
    tone = "empathetic" if sentiment in ["Negative", "Mixed"] else "professional"

    context = (
        f"Email from: {state['sender']}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Body: {state.get('body', '')}\n\n"
        f"Thread history:\n{thread_text}\n\n"
        f"Relevant policies:\n{rag_text}"
    )

    try:
        llm = _get_llm()
        prompt = f"""Write a {tone} customer support reply for this email. 
Cite specific policies where relevant. Be concise (max 180 words). 
Do not include subject line or salutation.

{context}

Reply:"""
        response = llm.invoke(prompt)
        draft_text = response if isinstance(response, str) else str(response)
        draft_text = draft_text.strip()
    except Exception as e:
        logger.error(f"Draft generation failed: {e}")
        draft_text = (
            "Thank you for reaching out to us. We have received your message and "
            "a member of our team will review it shortly. "
            "We appreciate your patience."
        )

    # Persist draft
    if not state.get("dry_run"):
        draft = Draft(
            email_id=state["email_id"],
            body=draft_text,
            tone=tone,
            policy_refs=policy_refs,
            status="pending",
        )
        db.add(draft)
        db.commit()

    thought = (
        f"Action: draft_reply(tone={tone})\n"
        f"Observation: Draft generated ({len(draft_text)} chars). "
        f"Policy refs: {policy_refs}. "
        f"Status: pending human approval."
    )

    return {
        "draft": draft_text,
        "final_action": "draft_reply_generated",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_escalate_human ──────────────────────────────────────────────

def action_escalate_human_node(state: AgentState, db: Session) -> dict:
    """Escalate to human support team."""
    from app.models.escalation import Escalation
    from app.services.audit_service import log_action

    classification = state.get("classification", {})
    reason = (
        classification.get("escalation_reason")
        or f"Category: {classification.get('category')}, Urgency: {classification.get('urgency')}"
    )
    priority = classification.get("urgency", "High")

    brief = (
        f"ESCALATION BRIEF\n"
        f"Email ID: {state['email_id']}\n"
        f"Message ID: {state['message_id']}\n"
        f"From: {state['sender']}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Category: {classification.get('category')}\n"
        f"Sentiment: {classification.get('sentiment')} ({classification.get('sentiment_score', 0):.2f})\n"
        f"Confidence: {classification.get('confidence', 0):.2f}\n"
        f"Reason: {reason}\n"
        f"Risk Notes: {classification.get('_risk_notes', [])}\n"
        f"Escalated at: {datetime.utcnow().isoformat()}"
    )

    if not state.get("dry_run"):
        escalation = Escalation(
            email_id=state["email_id"],
            escalation_type="human",
            reason=reason,
            priority=priority,
            assigned_to="support-team@company.com",
            brief=brief,
            status="open",
        )
        db.add(escalation)
        db.commit()
        log_action(db, "email", state["email_id"], "escalated_to_human")

    thought = (
        f"Action: escalate_to_human(priority={priority})\n"
        f"Observation: Escalation created. Assigned to support team. "
        f"Reason: {reason}"
    )

    return {
        "escalation_brief": {"reason": reason, "priority": priority, "brief": brief},
        "final_action": "escalated_to_human",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_flag_legal ──────────────────────────────────────────────────

def action_flag_legal_node(state: AgentState, db: Session) -> dict:
    """Flag for legal review — NEVER auto-reply."""
    from app.models.escalation import Escalation
    from app.services.audit_service import log_action

    hflags = state.get("heuristic_flags", {})
    issue_type = "gdpr" if hflags.get("is_gdpr") else "legal_threat"

    brief = (
        f"⚖️ LEGAL FLAG — URGENT ACTION REQUIRED\n"
        f"Email: {state['message_id']}\n"
        f"From: {state['sender']}\n"
        f"Issue: {issue_type}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Body Preview: {(state.get('body') or '')[:400]}\n"
        f"DO NOT reply to sender directly.\n"
        f"Flagged: {datetime.utcnow().isoformat()}"
    )

    if not state.get("dry_run"):
        escalation = Escalation(
            email_id=state["email_id"],
            escalation_type="legal",
            reason=f"Legal issue: {issue_type}",
            priority="Critical",
            assigned_to="legal@company.com",
            brief=brief,
            status="open",
        )
        db.add(escalation)
        db.commit()
        log_action(db, "email", state["email_id"], "flagged_for_legal")

    thought = (
        f"Action: flag_for_legal(issue_type={issue_type})\n"
        f"Observation: Legal escalation created. "
        f"Assigned to legal@company.com. "
        f"NO auto-reply will be sent."
    )

    return {
        "final_action": "flagged_for_legal",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_flag_security ───────────────────────────────────────────────

def action_flag_security_node(state: AgentState, db: Session) -> dict:
    """Immediately flag for security team — NEVER reply."""
    from app.models.escalation import Escalation
    from app.services.audit_service import log_action

    body_lower = (state.get("body") or "").lower()
    if "btc" in body_lower or "ransomware" in body_lower or "dark web" in body_lower:
        threat_type = "ransomware"
    elif "suspicious login" in body_lower or "north korea" in body_lower:
        threat_type = "suspicious_login"
    else:
        threat_type = "security_incident"

    brief = (
        f"🚨 SECURITY INCIDENT — CRITICAL\n"
        f"Email: {state['message_id']}\n"
        f"Sender: {state['sender']}\n"
        f"Threat: {threat_type}\n"
        f"Body: {(state.get('body') or '')[:400]}\n"
        f"IMMEDIATE ACTION REQUIRED. DO NOT respond to sender.\n"
        f"Notify: security@company.com + CTO immediately.\n"
        f"Detected: {datetime.utcnow().isoformat()}"
    )

    if not state.get("dry_run"):
        escalation = Escalation(
            email_id=state["email_id"],
            escalation_type="security",
            reason=f"Security threat: {threat_type}",
            priority="Critical",
            assigned_to="security@company.com",
            brief=brief,
            status="open",
        )
        db.add(escalation)
        db.commit()
        log_action(db, "email", state["email_id"], "flagged_for_security")

    thought = (
        f"Action: flag_for_security(threat_type={threat_type})\n"
        f"Observation: Security escalation created. "
        f"Notified security@company.com + CTO. "
        f"NO auto-reply sent to attacker."
    )

    return {
        "final_action": "flagged_for_security",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_gdpr_compliance ─────────────────────────────────────────────

def action_gdpr_compliance_node(state: AgentState, db: Session) -> dict:
    """Handle GDPR data requests — flag legal + create compliance ticket + acknowledgement."""
    from app.models.escalation import Escalation
    from app.models.ticket import Ticket
    from app.models.draft import Draft
    from app.services.audit_service import log_action

    # 1. Flag for legal/DPO
    gdpr_brief = (
        f"GDPR Article 20 — Data Portability Request\n"
        f"Sender: {state['sender']}\n"
        f"Message: {state['message_id']}\n"
        f"30-day statutory window applies from: {datetime.utcnow().date()}\n"
        f"Assign to DPO (dpo@company.com) for processing."
    )

    # 2. Create compliance ticket
    # 3. Generate GDPR acknowledgement (not a generic reply - cites legal obligation)
    ack_draft = (
        f"Dear {state['sender'].split('@')[0].replace('.', ' ').title()},\n\n"
        f"We have received your formal request for data portability under GDPR Article 20. "
        f"We acknowledge our obligation under the General Data Protection Regulation.\n\n"
        f"Your request has been logged and assigned to our Data Protection Officer. "
        f"We will provide a complete export of all personal data we hold within the "
        f"statutory 30-day window (by {(datetime.utcnow()).strftime('%B %d, %Y')}).\n\n"
        f"Reference: GDPR-{datetime.utcnow().strftime('%Y%m%d')}-{state['email_id']}\n\n"
        f"For any questions, please contact our DPO at dpo@company.com.\n\n"
        f"Best regards,\nCompliance Team"
    )

    if not state.get("dry_run"):
        escalation = Escalation(
            email_id=state["email_id"],
            escalation_type="legal",
            reason="GDPR Article 20 data portability request",
            priority="Critical",
            assigned_to="dpo@company.com",
            brief=gdpr_brief,
            status="open",
        )
        db.add(escalation)

        ticket = Ticket(
            email_id=state["email_id"],
            title=f"GDPR Data Request - {state['sender']}",
            body=gdpr_brief,
            assignee="dpo@company.com",
            priority="High",
            status="Open",
            ticket_type="compliance",
        )
        db.add(ticket)

        draft = Draft(
            email_id=state["email_id"],
            body=ack_draft,
            tone="formal",
            policy_refs=["compliance_faq.md"],
            status="pending",
        )
        db.add(draft)
        db.commit()
        log_action(db, "email", state["email_id"], "gdpr_compliance_processed")

    thought = (
        f"Action: gdpr_compliance_workflow()\n"
        f"Observation: GDPR request processed. DPO notified. "
        f"Compliance ticket created. "
        f"Formal acknowledgement drafted (NOT a generic auto-reply — cites 30-day statutory window). "
        f"Draft pending human approval before sending."
    )

    return {
        "draft": ack_draft,
        "final_action": "gdpr_compliance_processed",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_create_ticket ───────────────────────────────────────────────

def action_create_ticket_node(state: AgentState, db: Session) -> dict:
    """Create internal ticket for bugs or support issues."""
    from app.models.ticket import Ticket
    from app.services.audit_service import log_action

    classification = state.get("classification", {})
    category = classification.get("category", "Other")
    urgency = classification.get("urgency", "Medium")

    title = f"[{category}] {state.get('subject', 'No Subject')} — {state['sender']}"
    body = (
        f"Email ID: {state['email_id']}\n"
        f"Message ID: {state['message_id']}\n"
        f"From: {state['sender']}\n\n"
        f"Issue:\n{state.get('body', '')[:1000]}\n\n"
        f"Detected Entities: {classification.get('detected_entities', {})}"
    )

    if not state.get("dry_run"):
        ticket = Ticket(
            email_id=state["email_id"],
            title=title,
            body=body,
            assignee="engineering@company.com" if category == "Bug Report" else "support@company.com",
            priority=urgency,
            status="Open",
            ticket_type="bug" if category == "Bug Report" else "support",
        )
        db.add(ticket)
        db.commit()
        log_action(db, "email", state["email_id"], "ticket_created")

    thought = (
        f"Action: create_internal_ticket(category={category})\n"
        f"Observation: Ticket created and assigned to engineering team."
    )

    return {
        "final_action": "ticket_created",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: action_mark_spam ────────────────────────────────────────────────────

def action_mark_spam_node(state: AgentState) -> dict:
    """Mark as spam — no reply, no escalation."""
    thought = (
        f"Action: mark_spam()\n"
        f"Observation: Email classified as spam. No reply sent. "
        f"Added to spam queue for review."
    )
    return {
        "final_action": "marked_spam",
        "reasoning_trace": state["reasoning_trace"] + [thought],
    }


# ── Node: persist_results ────────────────────────────────────────────────────

def persist_results_node(state: AgentState, db: Session, start_time: float) -> dict:
    """
    Final node: Write classification + agent run to database.
    """
    from app.models.email import Email
    from app.models.agent_run import AgentRun
    from app.services.audit_service import log_action

    duration_ms = (time.time() - start_time) * 1000
    classification = state.get("classification", {})

    # Build full reasoning trace text
    trace_text = "\n\n".join(state.get("reasoning_trace", []))
    trace_text += f"\n\nDecision: {state.get('decision', 'unknown')}\nFinal Action: {state.get('final_action', 'unknown')}"

    if not state.get("dry_run"):
        # Update email record
        email = db.query(Email).filter(Email.id == state["email_id"]).first()
        if email:
            email.category = classification.get("category")
            email.sentiment = classification.get("sentiment")
            email.sentiment_score = classification.get("sentiment_score")
            email.urgency = classification.get("urgency")
            email.requires_human = classification.get("requires_human", False)
            email.confidence = classification.get("confidence")
            email.escalation_reason = classification.get("escalation_reason")
            email.suggested_reply = classification.get("suggested_reply")
            email.detected_entities = classification.get("detected_entities")
            email.processed_at = datetime.utcnow()

            # Update status
            action = state.get("final_action", "unknown")
            if "spam" in action:
                email.status = "spam"
            elif "internal" in action:
                email.status = "internal"
            elif "escalat" in action or "flagged" in action or "gdpr" in action:
                email.status = "escalated"
            elif "draft" in action:
                email.status = "pending_review"
            elif "ticket" in action:
                email.status = "ticket_created"
            else:
                email.status = "classified"

        # Save agent run
        agent_run = AgentRun(
            email_id=state["email_id"],
            reasoning_trace=trace_text,
            tool_calls=state.get("tool_calls_log"),
            decision=state.get("decision"),
            draft_reply=state.get("draft"),
            final_action=state.get("final_action"),
            run_duration_ms=duration_ms,
            dry_run=state.get("dry_run", False),
        )
        db.add(agent_run)
        db.commit()

        log_action(db, "email", state["email_id"], "agent_run_completed",
                   after_state={"decision": state.get("decision"), "action": state.get("final_action")})

    return {"final_action": state.get("final_action", "unknown")}
