"""
Document Loader and Chunker for the RAG Knowledge Base.

Chunks all .md files using RecursiveCharacterTextSplitter with:
- Chunk size: 1500 chars (~400 tokens / ~300 words)
- Overlap: 300 chars (~80 tokens)
- Metadata: source_doc, section_title, chunk_index, total_chunks, file_path

Design Notes:
- Uses character-based splitting (not token-based) for deterministic, library-free chunking.
- Separators ordered from coarse to fine so that paragraph > line > sentence > word splits
  are preferred over mid-word breaks.
- All metadata is propagated from the source document into every derived chunk so that
  downstream retrieval can always trace a chunk back to its origin file.
"""

import os
from pathlib import Path

# LangChain 0.3+ moved text splitters to a separate package
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[no-redef]

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Resolve knowledge_base/ relative to this file's location:
#   backend/app/rag/loader.py  →  backend/knowledge_base/
KB_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_documents() -> list[dict]:
    """
    Load all Markdown (.md) files from the knowledge_base directory.

    Each document is returned as a plain dict rather than a LangChain Document
    so that the rest of the pipeline stays decoupled from the LangChain object
    hierarchy.

    Returns:
        list[dict]: Each item has the shape::

            {
                "content": "<full markdown text>",
                "metadata": {
                    "source":     "pricing_policy.md",   # filename
                    "source_doc": "pricing_policy",      # stem (no extension)
                    "file_path":  "/abs/path/to/file.md",
                }
            }

    Notes:
        - Files are sorted alphabetically for deterministic ordering across runs.
        - If KB_DIR does not exist, a warning is logged and an empty list is returned.
    """
    docs: list[dict] = []

    if not KB_DIR.exists():
        logger.warning(f"Knowledge base directory not found: {KB_DIR}")
        return docs

    md_files = sorted(KB_DIR.glob("*.md"))
    if not md_files:
        logger.warning(f"No .md files found in {KB_DIR}")
        return docs

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error(f"Failed to read {md_file}: {exc}")
            continue

        docs.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "source_doc": md_file.stem,
                    "file_path": str(md_file),
                },
            }
        )
        logger.info(f"Loaded: {md_file.name} ({len(content):,} chars)")

    logger.info(f"Total documents loaded: {len(docs)} from {KB_DIR}")
    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    """
    Split a list of documents into overlapping text chunks suitable for embedding.

    Uses LangChain's RecursiveCharacterTextSplitter which tries each separator
    in order (paragraph → line → sentence → word → character), minimising
    mid-sentence breaks.

    Chunk parameters:
        - chunk_size   = 1500 chars  (~400 tokens, ~300 words)
        - chunk_overlap = 300 chars  (~80 tokens)

    Each chunk dict carries all parent document metadata plus:
        - chunk_index   : 0-based index of this chunk within the source document
        - total_chunks  : total number of chunks produced from the source document
        - section_title : first non-empty line of the chunk (up to 100 chars), used
                          as a human-readable label in retrieval results

    Args:
        docs: List of document dicts as returned by :func:`load_documents`.

    Returns:
        list[dict]: Flat list of chunk dicts with shape::

            {
                "content": "<chunk text>",
                "metadata": {
                    "source":        "pricing_policy.md",
                    "source_doc":    "pricing_policy",
                    "file_path":     "/abs/path/...",
                    "chunk_index":   0,
                    "total_chunks":  12,
                    "section_title": "# Pricing Policy — CRM Intelligence ...",
                }
            }
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,        # ~400 tokens / ~300 words
        chunk_overlap=300,      # ~80 tokens overlap for context continuity
        separators=[
            "\n\n",   # Double newline — paragraph break (preferred)
            "\n",     # Single newline — line break
            ". ",     # Sentence boundary
            " ",      # Word boundary
            "",       # Character boundary (last resort)
        ],
        length_function=len,
        is_separator_regex=False,
    )

    all_chunks: list[dict] = []

    for doc in docs:
        raw_chunks: list[str] = splitter.split_text(doc["content"])

        for i, chunk_text in enumerate(raw_chunks):
            # Use the first non-empty line as a human-readable section label.
            first_line = next(
                (line.strip() for line in chunk_text.splitlines() if line.strip()),
                "",
            )[:100]

            all_chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **doc["metadata"],               # propagate source metadata
                        "chunk_index": i,
                        "total_chunks": len(raw_chunks),
                        "section_title": first_line,
                    },
                }
            )

        logger.debug(
            f"Chunked '{doc['metadata']['source']}' → {len(raw_chunks)} chunks"
        )

    logger.info(
        f"Chunking complete: {len(all_chunks)} chunks from {len(docs)} documents"
    )
    return all_chunks


def load_and_chunk() -> list[dict]:
    """
    Convenience function: load all documents and chunk them in one call.

    Returns:
        list[dict]: Flat list of chunk dicts ready for embedding and indexing.
    """
    docs = load_documents()
    if not docs:
        logger.warning("No documents to chunk — returning empty list.")
        return []
    return chunk_documents(docs)
