"""
ChromaDB Vector Store and Retriever for the RAG Knowledge Base.

This module is the query-time core of the RAG pipeline.  It wraps
ChromaDB via the LangChain ``Chroma`` adapter and provides:

    1. ``get_vector_store()``       – singleton access to the persistent vector store
    2. ``add_chunks_to_store()``    – ingest chunked documents (run once / on update)
    3. ``get_collection_stats()``   – introspect the current collection
    4. ``search_knowledge_base()``  – semantic search returning ranked, scored chunks
    5. ``format_rag_context()``     – format retrieved chunks for LLM prompt injection
    6. ``clear_collection()``       – wipe and re-create the collection (used by ingest)

Score interpretation:
    ChromaDB with cosine distance returns values in [0, 2] where 0 = identical
    and 2 = diametrically opposite.  Because our embeddings are L2-normalised
    (see embedder.py) the relationship simplifies to:

        cosine_similarity = 1 − (chroma_distance / 2) × 2  →  1 − chroma_distance

    We cap the result at [0.0, 1.0] before thresholding.

Design decisions:
    - The vector store is accessed through a module-level singleton (``_vector_store``)
      that is initialised on first use to avoid repeated disk I/O.
    - ``add_chunks_to_store`` uses explicit string IDs derived from source document
      name and chunk index so that re-indexing is idempotent: adding the same chunks
      twice with the same IDs is a no-op in ChromaDB (upsert semantics).
    - ``format_rag_context`` produces a clearly delimited block that the LLM prompt
      templates can reliably parse or strip.
"""

from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma

from app.config import get_settings
from app.rag.embedder import get_embeddings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLLECTION_NAME = "crm_knowledge_base"

# Module-level singleton; populated on first call to get_vector_store()
_vector_store: Chroma | None = None


# ---------------------------------------------------------------------------
# Vector store lifecycle
# ---------------------------------------------------------------------------

def get_vector_store() -> Chroma:
    """
    Return the singleton ChromaDB vector store, creating it on first call.

    The store is persisted to disk at the path specified by
    ``settings.chroma_persist_dir`` so that embeddings survive process restarts.
    On subsequent calls the in-memory singleton is returned directly (no disk I/O).

    Returns:
        Chroma: A LangChain Chroma wrapper backed by a persistent ChromaDB client.

    Raises:
        RuntimeError: If the ChromaDB client cannot be initialised (e.g., disk full,
                      permission error on persist directory).
    """
    global _vector_store

    if _vector_store is not None:
        return _vector_store

    settings = get_settings()
    embeddings = get_embeddings()

    logger.info(
        f"Initialising ChromaDB vector store at: '{settings.chroma_persist_dir}' "
        f"(collection: '{COLLECTION_NAME}')"
    )

    try:
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=settings.chroma_persist_dir,
            collection_metadata={
                # Cosine similarity is the correct metric for L2-normalised embeddings.
                "hnsw:space": "cosine",
            },
        )
    except Exception as exc:
        logger.error(f"Failed to initialise ChromaDB: {exc}")
        raise RuntimeError(f"ChromaDB init failed: {exc}") from exc

    logger.info("ChromaDB vector store ready.")
    return _vector_store


def reset_vector_store_singleton() -> None:
    """
    Reset the module-level singleton so the next call to ``get_vector_store()``
    re-initialises from disk.

    This is primarily useful in tests that need a fresh store between test cases.
    """
    global _vector_store
    _vector_store = None


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def add_chunks_to_store(chunks: list[dict]) -> int:
    """
    Upsert document chunks into the ChromaDB vector store.

    Chunk IDs are derived deterministically from ``source_doc`` and
    ``chunk_index`` metadata fields, making this operation idempotent:
    re-indexing the same documents will overwrite existing embeddings
    rather than creating duplicates.

    Args:
        chunks: List of chunk dicts as produced by :func:`app.rag.loader.chunk_documents`.
                Each dict must contain ``"content"`` (str) and ``"metadata"`` (dict)
                with at least ``source_doc`` and ``chunk_index`` keys.

    Returns:
        int: Number of chunks successfully added/updated.

    Raises:
        ValueError: If ``chunks`` is empty.
        RuntimeError: If ChromaDB write fails.

    Example::

        from app.rag.loader import load_and_chunk
        from app.rag.retriever import add_chunks_to_store

        chunks = load_and_chunk()
        count = add_chunks_to_store(chunks)
        print(f"Indexed {count} chunks.")
    """
    if not chunks:
        raise ValueError("add_chunks_to_store() received an empty chunk list.")

    vector_store = get_vector_store()

    texts: list[str] = [c["content"] for c in chunks]
    metadatas: list[dict] = [c["metadata"] for c in chunks]
    ids: list[str] = [
        f"{c['metadata']['source_doc']}_chunk_{c['metadata']['chunk_index']}"
        for c in chunks
    ]

    logger.info(f"Upserting {len(chunks)} chunks into ChromaDB …")
    try:
        vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    except Exception as exc:
        logger.error(f"ChromaDB upsert failed: {exc}")
        raise RuntimeError(f"Failed to add chunks: {exc}") from exc

    logger.info(f"Successfully upserted {len(chunks)} chunks into '{COLLECTION_NAME}'.")
    return len(chunks)


def get_collection_stats() -> dict:
    """
    Return basic statistics about the current ChromaDB collection.

    Useful for health checks, admin endpoints, and debugging.

    Returns:
        dict: With keys:
            - ``collection_name`` (str)
            - ``document_count``  (int) – number of embedded chunks
            - ``persist_dir``     (str) – on-disk path

    Example::

        stats = get_collection_stats()
        # {"collection_name": "crm_knowledge_base", "document_count": 87, ...}
    """
    settings = get_settings()
    vector_store = get_vector_store()

    try:
        count = vector_store._collection.count()  # internal Chroma API
    except Exception:
        count = -1  # Gracefully degrade; don't break health checks

    return {
        "collection_name": COLLECTION_NAME,
        "document_count": count,
        "persist_dir": settings.chroma_persist_dir,
    }


def clear_collection() -> None:
    """
    Delete all documents from the collection and reset the singleton.

    Used by the ingest CLI / admin endpoint when a full re-index is required
    (e.g., after knowledge-base content changes).

    .. warning::
        This operation is **irreversible** within the running process.
        Embeddings on disk are deleted.  Re-run the ingest script to rebuild.
    """
    global _vector_store

    settings = get_settings()
    logger.warning(f"Clearing collection '{COLLECTION_NAME}' …")

    try:
        client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Collection '{COLLECTION_NAME}' deleted from disk.")
    except Exception as exc:
        logger.error(f"Failed to clear collection: {exc}")
        raise RuntimeError(f"clear_collection failed: {exc}") from exc
    finally:
        _vector_store = None  # Force re-init on next access


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def search_knowledge_base(
    query: str,
    k: int | None = None,
    min_score: float | None = None,
) -> list[dict]:
    """
    Retrieve the top-k most semantically relevant chunks for a given query.

    The query is embedded with the same model used during indexing and compared
    against all stored embeddings using cosine similarity.  Results are filtered
    by ``min_score`` and returned sorted by descending relevance.

    Score conversion:
        ChromaDB returns a cosine *distance* in [0, 2] for L2-normalised vectors.
        We convert to *similarity* in [0, 1] via::

            similarity = max(0.0, 1.0 − chroma_distance)

        A score of 1.0 means the chunk is semantically identical to the query;
        0.0 means completely unrelated.

    Args:
        query:     Natural-language search query string.
        k:         Maximum number of chunks to return.
                   Defaults to ``settings.rag_top_k`` (typically 5).
        min_score: Minimum cosine similarity threshold in [0, 1].
                   Chunks with a lower score are discarded.
                   Defaults to ``settings.rag_min_score`` (typically 0.3).

    Returns:
        list[dict]: Sorted by score descending.  Each item::

            {
                "content":       "<chunk text>",
                "source":        "pricing_policy.md",
                "source_doc":    "pricing_policy",
                "section_title": "## 4. Discount Programs",
                "score":         0.8721,
                "chunk_index":   3,
            }

        Returns an empty list if the collection is empty, the query yields no
        results above ``min_score``, or if ChromaDB raises an exception.

    Raises:
        ValueError: If ``query`` is empty.

    Example::

        results = search_knowledge_base("What is the non-profit discount?", k=3)
        for r in results:
            print(f"[{r['score']:.2f}] {r['source']} — {r['section_title']}")
    """
    if not query or not query.strip():
        raise ValueError("search_knowledge_base() received an empty query.")

    settings = get_settings()
    k = k if k is not None else settings.rag_top_k
    min_score = min_score if min_score is not None else settings.rag_min_score

    vector_store = get_vector_store()

    # Guard against searching an empty collection
    try:
        collection_count = vector_store._collection.count()
    except Exception:
        collection_count = -1

    if collection_count == 0:
        logger.warning(
            "search_knowledge_base() called on an empty collection. "
            "Run the ingest script first."
        )
        return []

    logger.debug(f"RAG search | query='{query[:80]}…' k={k} min_score={min_score}")

    try:
        # similarity_search_with_score returns List[Tuple[Document, float]]
        # where the float is the cosine *distance* (lower = more similar).
        raw_results = vector_store.similarity_search_with_score(
            query=query,
            k=k * 2,  # Fetch extra results to allow for min_score filtering
        )
    except Exception as exc:
        logger.error(f"ChromaDB similarity search failed: {exc}")
        return []

    chunks: list[dict] = []
    for doc, distance in raw_results:
        # Convert cosine distance → similarity score in [0.0, 1.0]
        similarity = round(max(0.0, 1.0 - float(distance)), 4)

        if similarity < min_score:
            logger.debug(
                f"  Filtered (score {similarity:.4f} < min {min_score}): "
                f"{doc.metadata.get('source', '?')} chunk {doc.metadata.get('chunk_index', '?')}"
            )
            continue

        chunks.append(
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "source_doc": doc.metadata.get("source_doc", "unknown"),
                "section_title": doc.metadata.get("section_title", ""),
                "score": similarity,
                "chunk_index": doc.metadata.get("chunk_index", 0),
            }
        )

    # Sort descending by similarity and cap at k
    chunks.sort(key=lambda x: x["score"], reverse=True)
    chunks = chunks[:k]

    logger.info(
        f"RAG search returned {len(chunks)} chunk(s) "
        f"(filtered from {len(raw_results)} candidates) "
        f"for query: '{query[:60]}…'"
    )
    return chunks


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------

def format_rag_context(chunks: list[dict]) -> str:
    """
    Format a list of retrieved chunks into a structured string for LLM consumption.

    The output uses clear delimiters so that the LLM system prompt can
    unambiguously identify the injected knowledge-base context.

    Args:
        chunks: List of chunk dicts as returned by :func:`search_knowledge_base`.

    Returns:
        str: A multi-line formatted context block.  When ``chunks`` is empty,
             returns a message indicating no context was found (the LLM should
             answer from its general knowledge in this case).

    Example output::

        === RELEVANT KNOWLEDGE BASE CONTEXT ===

        [Source 1: pricing_policy.md | Section: ## 4. Discount Programs | Relevance: 0.87]
        Non-profit organizations are eligible for a 30% discount on Standard and Pro plans.
        ...

        [Source 2: compliance_faq.md | Section: ### Q: Is the platform HIPAA compliant? | Relevance: 0.72]
        Yes. HIPAA-compliant deployments are available for Enterprise customers with a BAA.
        ...

        === END CONTEXT ===
    """
    if not chunks:
        return (
            "=== KNOWLEDGE BASE CONTEXT ===\n"
            "No relevant context found in the knowledge base for this query.\n"
            "=== END CONTEXT ==="
        )

    lines: list[str] = ["=== RELEVANT KNOWLEDGE BASE CONTEXT ==="]

    for i, chunk in enumerate(chunks, start=1):
        header = (
            f"\n[Source {i}: {chunk['source']} "
            f"| Section: {chunk['section_title']} "
            f"| Relevance: {chunk['score']:.2f}]"
        )
        lines.append(header)
        lines.append(chunk["content"])

    lines.append("\n=== END CONTEXT ===")
    return "\n".join(lines)


def retrieve_and_format(
    query: str,
    k: int | None = None,
    min_score: float | None = None,
) -> tuple[str, list[dict]]:
    """
    Convenience function: search and format in one call.

    Returns both the formatted context string (for prompt injection) and the raw
    chunk list (for citation / source attribution in the API response).

    Args:
        query:     Natural-language search query.
        k:         Max chunks to retrieve (default from settings).
        min_score: Minimum similarity threshold (default from settings).

    Returns:
        tuple[str, list[dict]]:
            - ``context_str`` : formatted string ready for LLM prompt injection
            - ``chunks``      : raw list of chunk dicts for source attribution

    Example::

        context_str, sources = retrieve_and_format(
            "What is the refund window for annual plans?", k=4
        )
        # Inject context_str into the LLM system prompt
        # Return sources to the API caller for transparency
    """
    chunks = search_knowledge_base(query, k=k, min_score=min_score)
    context_str = format_rag_context(chunks)
    return context_str, chunks
