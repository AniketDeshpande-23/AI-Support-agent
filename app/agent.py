"""
app/agent.py — Orchestrates the full ticket-processing pipeline.

Flow:
  1. Retrieve relevant docs from FAISS (async via thread)
  2. Optional: prepend prior thread context
  3. Single LLM call -> category + priority + reply + confidence + grounded
  4. Apply escalation routing rules
  5. Persist to SQLite (async via thread)
"""

import asyncio
import logging

from app.config import get_llm, get_embeddings
from app.database import save_ticket, get_thread_tickets
from app.pipeline import analyze_ticket
from app.retriever import get_vectorstore, retrieve_solution
from app.router import route_ticket

logger = logging.getLogger(__name__)

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
        _vectorstore = await asyncio.to_thread(get_vectorstore, _get_embeddings())
    return _vectorstore


async def warm_up() -> None:
    """Pre-build FAISS index and load LLM at startup to avoid cold-start delay."""
    logger.info("Warming up vectorstore and LLM...")
    await _get_vectorstore()
    _get_llm()
    logger.info("Warm-up complete.")


async def run_agent(
    ticket_text: str,
    customer_id: str = "",
    thread_id: str = "",
) -> dict:
    """
    Process a support ticket end-to-end.

    Returns: category, priority, confidence, grounded, route_to, reply, ticket_id.
    """
    logger.info(f"Processing ticket ({len(ticket_text)} chars) "
                f"customer={customer_id!r} thread={thread_id!r}")

    # 1. Retrieve context from knowledge base
    vs = await _get_vectorstore()
    context = await asyncio.to_thread(retrieve_solution, vs, ticket_text)

    # 2. Prepend prior thread exchanges so the model has conversation history
    if thread_id:
        prior = await asyncio.to_thread(get_thread_tickets, thread_id, 3)
        if prior:
            history = "\n\n".join(
                f"Previous ticket: {t['ticket_text']}\nAgent reply: {t['reply']}"
                for t in prior
            )
            context = f"--- Thread history ---\n{history}\n\n--- Knowledge base ---\n{context}"

    # 3. Single LLM call
    result = await analyze_ticket(ticket_text, context, _get_llm())

    # 4. Routing
    if result["priority"] == "Critical":
        route = "Senior Support"
    elif result["confidence"] < 6:
        route = "Human Review"
    elif not result["grounded"]:
        route = "Human Review"
    else:
        route = route_ticket(result["category"], result["priority"])

    result["route_to"] = route

    # 5. Persist
    ticket_id = await asyncio.to_thread(
        save_ticket,
        {**result, "ticket_text": ticket_text,
         "customer_id": customer_id, "thread_id": thread_id},
    )
    result["ticket_id"] = ticket_id

    logger.info(
        f"Ticket {ticket_id} done | category={result['category']} "
        f"priority={result['priority']} confidence={result['confidence']} route={route}"
    )
    return result
