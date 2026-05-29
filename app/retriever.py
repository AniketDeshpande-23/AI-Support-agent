"""
app/retriever.py — FAISS vector store management.

Loads from disk if the index exists; builds from knowledge_base.txt otherwise.
The vectorstore is a module-level singleton initialised lazily via get_vectorstore().
"""

import logging
import os

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

VECTOR_PATH = "data/faiss_index"
KB_PATH = "data/knowledge_base.txt"

_vectorstore = None


def get_vectorstore(embeddings):
    """Return (or build) the FAISS vector store. Idempotent — safe to call many times."""
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    if os.path.exists(VECTOR_PATH):
        logger.info("Loading FAISS index from disk")
        _vectorstore = FAISS.load_local(
            VECTOR_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        return _vectorstore

    logger.info("Building FAISS index from knowledge base")
    if not os.path.exists(KB_PATH):
        raise FileNotFoundError(
            f"Knowledge base not found at '{KB_PATH}'. "
            "Create 'data/knowledge_base.txt' before starting the server."
        )

    with open(KB_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.create_documents([text])

    _vectorstore = FAISS.from_documents(docs, embeddings)
    _vectorstore.save_local(VECTOR_PATH)
    logger.info(f"FAISS index built and saved ({len(docs)} chunks)")

    return _vectorstore


def retrieve_solution(vectorstore, query: str, k: int = 3) -> str:
    """Return the top-k relevant knowledge base passages for a query."""
    try:
        docs = vectorstore.similarity_search(query, k=k)
        return "\n\n".join(d.page_content for d in docs)
    except Exception as exc:
        logger.error(f"Retrieval error: {exc}")
        return "No relevant documentation found."
