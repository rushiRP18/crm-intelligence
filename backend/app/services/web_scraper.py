"""
Web Intelligence Service — Mock Scraper with Realistic Data.

Simulates G2/Trustpilot/Capterra scraping with 6-hour caching.
In production, this would make real HTTP requests with robots.txt compliance.
For demo/evaluation: returns realistic mock data that varies by domain.
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.web_intel import WebIntelCache
from app.config import get_settings

settings = get_settings()

# Mock data pool — realistic G2/Trustpilot style data
MOCK_REVIEW_DATA = {
    "g2.com": {
        "platform": "G2",
        "rating": 4.2,
        "total_reviews": 847,
        "recent_reviews": [
            {"stars": 1, "text": "Slow support response, took 5 days to get a reply.", "date": "2023-10-15"},
            {"stars": 2, "text": "Dashboard performance has degraded significantly.", "date": "2023-10-12"},
            {"stars": 5, "text": "Best CRM tool we've used. The analytics are incredible.", "date": "2023-10-10"},
            {"stars": 3, "text": "Good features but the mobile experience needs work.", "date": "2023-10-08"},
            {"stars": 1, "text": "Missed SLAs multiple times. Very disappointed.", "date": "2023-10-06"},
        ],
        "complaint_themes": ["slow support", "performance issues", "missing mobile app"],
        "praise_themes": ["analytics", "easy setup", "good integrations"],
        "trend": "declining",  # rating dropped from 4.7 to 4.2 recently
    },
    "trustpilot.com": {
        "platform": "Trustpilot",
        "rating": 3.8,
        "total_reviews": 234,
        "recent_reviews": [
            {"stars": 1, "text": "3 emails sent with zero human response. Appalling.", "date": "2023-10-14"},
            {"stars": 4, "text": "Generally great, had a bumpy patch but resolved.", "date": "2023-10-11"},
            {"stars": 2, "text": "SLA breach not properly addressed by support team.", "date": "2023-10-09"},
        ],
        "complaint_themes": ["unresponsive support", "SLA breaches", "billing issues"],
        "praise_themes": ["feature-rich", "good onboarding"],
        "trend": "stable",
    },
    "capterra.com": {
        "platform": "Capterra",
        "rating": 4.5,
        "total_reviews": 512,
        "recent_reviews": [
            {"stars": 5, "text": "Excellent tool for our team, highly recommend.", "date": "2023-10-16"},
            {"stars": 4, "text": "Good value, some minor UX rough edges.", "date": "2023-10-13"},
        ],
        "complaint_themes": ["UX could be improved", "pricing"],
        "praise_themes": ["value for money", "feature depth", "customer success"],
        "trend": "improving",
    },
}

DEFAULT_INTEL = {
    "platform": "Aggregated",
    "rating": 4.1,
    "total_reviews": 0,
    "recent_reviews": [],
    "complaint_themes": ["unknown"],
    "praise_themes": ["unknown"],
    "trend": "unknown",
    "note": "Mock data — no live scraping target matched",
}


def check_robots_txt(domain: str) -> bool:
    """Mock robots.txt compliance check. Always returns True for demo."""
    # In production: fetch and parse /robots.txt
    blocked_domains: list[str] = []  # None blocked in mock
    return domain not in blocked_domains


def should_scrape(
    sender_email: str,
    body: str | None,
    sentiment_score: float | None,
    category: str | None,
) -> bool:
    """
    Determine if web intelligence scraping should be triggered for this email.
    Trigger conditions per assessment spec.
    """
    body_lower = (body or "").lower()
    review_triggers = ["review", "trustpilot", "g2", "twitter", "post publicly", "capterra"]

    if any(kw in body_lower for kw in review_triggers):
        return True
    if sentiment_score is not None and sentiment_score < -0.6:
        return True
    if category == "Complaint":
        return True
    if category in ["Press", "Investor"]:
        return True
    return False


def get_cached_intel(db: Session, domain: str) -> dict | None:
    """Return cached web intel if still fresh (< 6 hours old)."""
    cached = db.query(WebIntelCache).filter(WebIntelCache.domain == domain).first()
    if cached and cached.expires_at and cached.expires_at > datetime.utcnow():
        return cached.scraped_data
    return None


def scrape_and_cache(db: Session, domain: str = "g2.com") -> dict:
    """
    Run mock scrape and cache the result for 6 hours.
    Falls back gracefully if domain is unknown.
    """
    if not check_robots_txt(domain):
        return {"error": f"robots.txt disallows scraping of {domain}"}

    # Check cache first
    cached = get_cached_intel(db, domain)
    if cached:
        return {**cached, "cache_hit": True}

    # Mock scrape — add slight randomness to simulate real data variation
    base_data = MOCK_REVIEW_DATA.get(domain, DEFAULT_INTEL).copy()
    base_data["rating"] = round(base_data["rating"] + random.uniform(-0.1, 0.1), 1)
    base_data["scraped_at"] = datetime.utcnow().isoformat()
    base_data["cache_hit"] = False
    base_data["mock"] = True

    # Upsert cache
    cached_entry = db.query(WebIntelCache).filter(WebIntelCache.domain == domain).first()
    expires = datetime.utcnow() + timedelta(hours=settings.web_intel_cache_hours)
    if cached_entry:
        cached_entry.scraped_data = base_data
        cached_entry.scraped_at = datetime.utcnow()
        cached_entry.expires_at = expires
    else:
        db.add(WebIntelCache(domain=domain, scraped_data=base_data, expires_at=expires))
    db.commit()

    return base_data


def get_public_reputation_summary(db: Session) -> dict:
    """Aggregate reputation across all cached sources for the /intelligence/reputation endpoint."""
    sources = ["g2.com", "trustpilot.com", "capterra.com"]
    result = {}
    for domain in sources:
        cached = get_cached_intel(db, domain)
        if not cached:
            cached = scrape_and_cache(db, domain)
        result[domain] = {
            "rating": cached.get("rating"),
            "total_reviews": cached.get("total_reviews"),
            "trend": cached.get("trend"),
            "top_complaints": cached.get("complaint_themes", [])[:3],
        }
    return result
