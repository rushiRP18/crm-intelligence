"""Web Intelligence API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.web_scraper import get_public_reputation_summary, scrape_and_cache

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/reputation")
def get_reputation(db: Session = Depends(get_db)):
    """
    Return the current public sentiment summary aggregated across
    G2, Trustpilot, and Capterra review sources.
    Results are cached in the database and refreshed by the background scraper.
    """
    return get_public_reputation_summary(db)


@router.post("/scrape")
def trigger_scrape(domain: str = "g2.com", db: Session = Depends(get_db)):
    """
    Manually trigger a web intelligence scrape for a specific review domain.
    Supported domains: g2.com, trustpilot.com, capterra.com
    Results are cached and returned immediately.
    """
    result = scrape_and_cache(db, domain)
    return {"domain": domain, "result": result}
