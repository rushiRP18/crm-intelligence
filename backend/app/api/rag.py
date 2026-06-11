"""RAG debug API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.rag_retrieval import RagRetrieval

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.get("/search")
def rag_search(
    q: str = Query(..., description="Search query to run against the knowledge base"),
    k: int = Query(3, ge=1, le=10, description="Number of top chunks to return"),
    db: Session = Depends(get_db),
):
    """
    Debug endpoint: query the ChromaDB knowledge base and return
    matching chunks with similarity scores. Useful for validating
    RAG retrieval quality without running the full agent pipeline.
    """
    from app.rag.retriever import search_knowledge_base
    try:
        chunks = search_knowledge_base(q, k=k)
        return {
            "query": q,
            "k": k,
            "results": chunks,
            "count": len(chunks),
        }
    except Exception as e:
        return {
            "query": q,
            "error": str(e),
            "results": [],
            "count": 0,
        }


@router.get("/stats")
def rag_stats(db: Session = Depends(get_db)):
    """
    Return basic stats about the RAG retrieval history:
    total retrievals performed and average chunk count returned.
    """
    from sqlalchemy import func

    total_retrievals = db.query(RagRetrieval).count()
    avg_chunks = (
        db.query(func.avg(func.json_array_length(RagRetrieval.chunks)))
        .scalar()
    )
    return {
        "total_retrievals": total_retrievals,
        "avg_chunks_per_retrieval": round(float(avg_chunks or 0), 2),
    }
