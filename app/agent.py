"""
app/agent.py — Orchestrates the full ticket-processing pipeline.

Flow:
  1. Retrieve relevant docs from FAISS (async via thread)
  2. Single LLM call → category + priority + reply + confidence + grounded
  3. Apply escalation routing rules
  4. Persist to SQLite (async via thread)
"""

import asyncio
import logging

from app.config import get_llm, get_embeddings
from app.database import save_ticket
from app.pipeline import analyze_ticket
from app.retriever import get_vectorstore, retrieve_solution
from app.router import route_ticket

logger = logging.getLogger(__name__)

# ── Module-level lazy singletons ──────────────────────────────────────────────
# Initialised on first request so the import doesn't block at startup.

_llm = None
_embeddings = None
_vectorstore = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = get_embeddings()
    return _embeddings


async def _get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        # FAISS build is CPU-bound — run in thread pool to avoid blocking the event loop
        _vectorstore = await asyncio.to_thread(get_vectorstore, _get_embeddings())
    return _vectorstore


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_agent(ticket_text: str) -> dict:
    """
    Process a support ticket end-to-end.

    Returns a dict with: category, priority, confidence, grounded, route_to, reply.
    """
    logger.info(f"Processing ticket ({len(ticket_text)} chars)")

    # 1. Retrieve context from knowledge base
    vs = await _get_vectorstore()
    context = await asyncio.to_thread(retrieve_solution, vs, ticket_text)

    # 2. Single LLM call — replaces the old 3-call pipeline
    result = await analyze_ticket(ticket_text, context, _get_llm())

    # 3. Escalation routing
    if result["priority"] == "Critical":
        route = "Senior Support"
    elif result["confidence"] < 6:
        route = "Human Review"
    elif not result["grounded"]:
        route = "Human Review"
    else:
        route = route_ticket(result["category"], result["priority"])

    result["route_to"] = route

    # 4. Persist (non-blocking)
    await asyncio.to_thread(
        save_ticket,
        {**result, "ticket_text": ticket_text},
    )

    logger.info(
        f"Ticket done | category={result['category']} "
        f"priority={result['priority']} confidence={result['confidence']} "
        f"route={route}"
    )
    return result
