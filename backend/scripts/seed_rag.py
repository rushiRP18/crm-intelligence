"""
Seed the RAG Knowledge Base into ChromaDB.

Run this once before starting the application:
    python -m scripts.seed_rag

This script:
1. Loads all .md files from knowledge_base/
2. Chunks them with RecursiveCharacterTextSplitter (400 tokens, 80 token overlap)
3. Embeds using sentence-transformers/all-MiniLM-L6-v2 (local, no API key needed)
4. Stores in ChromaDB (persistent)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings, configure_langsmith
from app.rag.loader import load_documents, chunk_documents
from app.rag.retriever import add_chunks_to_store, get_vector_store
from app.utils.logging import get_logger

logger = get_logger("seed_rag")


def main():
    settings = get_settings()
    configure_langsmith(settings)

    logger.info("=" * 60)
    logger.info("RAG Knowledge Base Seeding")
    logger.info("=" * 60)

    # Step 1: Clear existing collection if re-seeding
    logger.info("Checking existing ChromaDB collection...")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        try:
            client.delete_collection("crm_knowledge_base")
            logger.info("Cleared existing collection")
        except Exception:
            logger.info("No existing collection found, creating fresh")
    except Exception as e:
        logger.warning(f"Could not clear collection: {e}")

    # Step 2: Load documents
    logger.info("Loading knowledge base documents...")
    docs = load_documents()
    if not docs:
        logger.error("No documents found! Check that knowledge_base/ directory exists with .md files")
        sys.exit(1)
    logger.info(f"Loaded {len(docs)} documents")

    # Step 3: Chunk
    logger.info("Chunking documents...")
    chunks = chunk_documents(docs)
    logger.info(f"Created {len(chunks)} chunks")

    # Step 4: Embed and store
    logger.info(f"Embedding with {settings.embedding_model} (downloading if needed)...")
    count = add_chunks_to_store(chunks)
    logger.info(f"Successfully stored {count} chunks in ChromaDB at {settings.chroma_persist_dir}")

    # Step 5: Verify with a test query
    logger.info("Verifying with test queries...")
    from app.rag.retriever import search_knowledge_base
    tests = [
        ("non-profit discount pricing", "pricing_policy"),
        ("SLA breach credit calculation", "sla_policy"),
        ("GDPR data portability request", "compliance_faq"),
        ("ransomware escalation", "escalation_matrix"),
    ]
    for query, expected_source in tests:
        results = search_knowledge_base(query, k=1)
        if results:
            top = results[0]
            logger.info(f"  Query: '{query}' → Source: {top['source']} (score: {top['score']:.3f})")
        else:
            logger.warning(f"  Query: '{query}' → No results found")

    logger.info("=" * 60)
    logger.info("RAG seeding complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
