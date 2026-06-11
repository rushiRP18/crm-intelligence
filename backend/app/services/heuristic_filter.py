"""
Heuristic Pre-filter — sub-10ms synchronous email triage.

Runs before any LLM call to immediately route:
- Spam → spam queue
- Internal → internal inbox
- Security threats → security alert queue
- Critical urgency → priority boost
"""
import re
from dataclasses import dataclass, field


# ── Keyword lists ─────────────────────────────────────────────────────────────

SPAM_KEYWORDS = [
    "boost your seo", "click here to claim", "limited offer", "front page of google",
    "prince", "inheritance", "processing fee", "bank account details", "$50,000,000",
    "100k followers", "pure win-win", "dm me", "collab", "quick question for the right person",
    "software purchasing decisions",
]

SPAM_SENDER_PATTERNS = [
    r"@marketing-guru\.io$",
    r"@wealth-transfer\.com$",
    r"@spammy-outreach\.com$",
    r"@coldoutreach\.com$",
    r"@review-scraper\.io$",
    r"newsletter@",
    r"noreply@",
]

INTERNAL_DOMAINS = ["@internal.com", "@mycompany.com"]

SECURITY_KEYWORDS = [
    "ransomware", "btc", "bitcoin", "dark web", "exfiltrated", "pay now",
    "suspicious login", "unknown location", "pyongyang", "north korea",
    "send 2 btc", "publish the data", "hacker", "we have your data",
]

LEGAL_KEYWORDS = [
    "cease and desist", "registered trademark", "legal action", "lawyer",
    "attorney", "lawsuit", "litigation", "formal correspondence", "legal team",
]

GDPR_KEYWORDS = [
    "gdpr", "article 20", "right to portability", "data portability",
    "personal data", "right to erasure", "right to be forgotten",
]

URGENT_KEYWORDS = [
    "urgent", "p0", "critical", "immediately", "emergency", "production down",
    "losing $", "losing money", "server down", "outage", "not responding",
]

CHURN_KEYWORDS = [
    "cancel", "cancelling", "cancellation", "delete my account",
    "negative review", "g2", "trustpilot", "twitter", "capterra",
    "post publicly", "worst experience", "never use again",
]

COMPLIANCE_KEYWORDS = ["hipaa", "baa", "soc 2", "iso 27001", "compliance", "gdpr dpa"]


@dataclass
class HeuristicResult:
    is_spam: bool = False
    is_internal: bool = False
    is_security_threat: bool = False
    is_legal: bool = False
    is_gdpr: bool = False
    is_churn_risk: bool = False
    is_compliance: bool = False
    urgency_boost: bool = False
    priority_score: int = 50  # 0-100; higher = more urgent
    flags: list[str] = field(default_factory=list)
    initial_category: str | None = None


def run_heuristic_filter(sender: str, subject: str | None, body: str | None) -> HeuristicResult:
    """
    Run all heuristic checks on an incoming email.
    Should complete in < 10ms (pure Python string matching).
    """
    result = HeuristicResult()
    sender_lower = sender.lower()
    subject_lower = (subject or "").lower()
    body_lower = (body or "").lower()
    combined = f"{subject_lower} {body_lower}"

    # ── Internal check (highest priority) ────────────────────
    if any(domain in sender_lower for domain in INTERNAL_DOMAINS):
        result.is_internal = True
        result.initial_category = "Internal"
        result.flags.append("internal_sender")
        result.priority_score = 10
        return result  # No further checks needed

    # ── Security threat check ─────────────────────────────────
    if any(kw in combined for kw in SECURITY_KEYWORDS):
        result.is_security_threat = True
        result.initial_category = "Security"
        result.flags.append("security_threat")
        result.priority_score = 100

    # ── Legal threat check ────────────────────────────────────
    if any(kw in combined for kw in LEGAL_KEYWORDS):
        result.is_legal = True
        result.flags.append("legal_threat")
        result.priority_score = max(result.priority_score, 95)
        if not result.initial_category:
            result.initial_category = "Legal"

    # ── GDPR check ────────────────────────────────────────────
    if any(kw in combined for kw in GDPR_KEYWORDS):
        result.is_gdpr = True
        result.flags.append("gdpr_request")
        result.priority_score = max(result.priority_score, 90)
        if not result.initial_category:
            result.initial_category = "Compliance"

    # ── Compliance check ──────────────────────────────────────
    if any(kw in combined for kw in COMPLIANCE_KEYWORDS):
        result.is_compliance = True
        result.flags.append("compliance")
        result.priority_score = max(result.priority_score, 80)

    # ── Spam domain pattern check ─────────────────────────────
    is_spam_domain = any(
        re.search(pattern, sender_lower) for pattern in SPAM_SENDER_PATTERNS
    )
    # ── Spam content check ────────────────────────────────────
    spam_keyword_hits = sum(1 for kw in SPAM_KEYWORDS if kw in combined)
    if is_spam_domain or spam_keyword_hits >= 2:
        result.is_spam = True
        result.initial_category = "Spam"
        result.flags.append("spam_detected")
        result.priority_score = 0
        return result

    # ── Churn risk check ─────────────────────────────────────
    if any(kw in combined for kw in CHURN_KEYWORDS):
        result.is_churn_risk = True
        result.flags.append("churn_risk")
        result.priority_score = max(result.priority_score, 85)

    # ── Urgency boost ─────────────────────────────────────────
    if any(kw in combined for kw in URGENT_KEYWORDS):
        result.urgency_boost = True
        result.flags.append("urgent_keywords")
        result.priority_score = max(result.priority_score, 88)

    return result
