"""
Embedding model wrapper for the RAG Knowledge Base.

Uses the ``sentence-transformers/all-MiniLM-L6-v2`` model via
``langchain-community``'s HuggingFaceEmbeddings adapter so that the model
can be swapped for any HuggingFace-compatible model by changing a single
config value.

Model characteristics:
    - Dimensionality  : 384
    - Inference speed : Very fast on CPU (~14,000 sentences/second on 4-core CPU)
    - Model size      : ~90 MB (downloaded automatically on first use from HuggingFace Hub)
    - Licence         : Apache 2.0
    - Best suited for : Semantic similarity, clustering, information retrieval

Design decisions:
    - ``@lru_cache(maxsize=1)`` ensures the heavy model weights are loaded only
      once per process, regardless of how many times ``get_embeddings()`` is called.
    - Embeddings are L2-normalised (``normalize_embeddings=True``) so that cosine
      similarity and dot-product similarity give identical results — ChromaDB uses
      cosine similarity by default, so this is the correct setting.
    - The model is pinned to CPU to avoid optional CUDA dependencies; if a GPU is
      available it can be enabled by changing ``device`` to ``"cuda"`` in config.
"""

from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Load the sentence-transformer embedding model and cache it for the process lifetime.

    The model is loaded from the HuggingFace Hub on first call and cached locally
    at ``~/.cache/huggingface/``. Subsequent calls return the cached in-memory object
    without re-loading weights, making this safe to call in hot paths.

    Settings consumed (from ``app.config.Settings``):
        - ``embedding_model`` : HuggingFace model name or local path.
          Default: ``"sentence-transformers/all-MiniLM-L6-v2"``

    Returns:
        HuggingFaceEmbeddings: Ready-to-use LangChain embedding object whose
        ``.embed_documents()`` and ``.embed_query()`` methods accept plain strings
        and return lists of floats.

    Raises:
        OSError: If the model cannot be downloaded or loaded (e.g., no internet,
                 corrupted cache).

    Example::

        embeddings = get_embeddings()
        vector = embeddings.embed_query("What is the refund policy?")
        # vector is a list of 384 floats
    """
    settings = get_settings()
    model_name: str = settings.embedding_model

    logger.info(f"Loading embedding model: '{model_name}' on CPU …")

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={
            "device": "cpu",   # Change to "cuda" if GPU is available and desired
        },
        encode_kwargs={
            # L2-normalise all output vectors so that cosine similarity ≡ dot product.
            # This is required for consistent score interpretation in ChromaDB.
            "normalize_embeddings": True,
            # Process in batches of 32 for memory efficiency.
            "batch_size": 32,
        },
    )

    # Eagerly embed a test string to confirm the model loaded without errors.
    # This surfaces download or incompatibility errors at startup rather than
    # at query time.
    try:
        _ = embeddings.embed_query("health check")
        logger.info(
            f"Embedding model '{model_name}' loaded and verified successfully."
        )
    except Exception as exc:
        logger.error(f"Embedding model health check failed: {exc}")
        raise

    return embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using the cached embedding model.

    This is a convenience wrapper around ``get_embeddings().embed_documents()``
    that handles logging and error propagation.

    Args:
        texts: List of text strings to embed. Each string should be a single
               sentence or short paragraph (max ~512 tokens for MiniLM-L6-v2).

    Returns:
        list[list[float]]: One 384-dimensional vector per input text.

    Raises:
        ValueError: If ``texts`` is empty.
        RuntimeError: If embedding fails for any reason.

    Example::

        vectors = embed_texts(["Hello world", "Goodbye world"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 384
    """
    if not texts:
        raise ValueError("embed_texts() received an empty list — nothing to embed.")

    embeddings = get_embeddings()
    logger.debug(f"Embedding {len(texts)} text(s) …")

    try:
        vectors = embeddings.embed_documents(texts)
    except Exception as exc:
        logger.error(f"Failed to embed {len(texts)} texts: {exc}")
        raise RuntimeError(f"Embedding failed: {exc}") from exc

    logger.debug(f"Embedding complete: {len(vectors)} vector(s) of dim {len(vectors[0])}")
    return vectors


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string for similarity search.

    Functionally equivalent to ``embed_texts([query])[0]`` but uses the model's
    dedicated query-embedding path (which may apply a query prefix in some models).

    Args:
        query: The search query string.

    Returns:
        list[float]: A 384-dimensional embedding vector.

    Example::

        vec = embed_query("What is the SLA credit calculation?")
        assert len(vec) == 384
    """
    if not query or not query.strip():
        raise ValueError("embed_query() received an empty query string.")

    embeddings = get_embeddings()
    return embeddings.embed_query(query)
