"""
app/main.py — FastAPI application.

Endpoints:
  POST /analyze              — analyse a ticket (rate-limited)
  POST /analyze/stream       — SSE streaming analysis with progress events
  GET  /health               — liveness + model info
  GET  /tickets              — paginated history (optional ?route= filter)
  GET  /tickets/thread/{id}  — thread history
  GET  /metrics              — aggregate stats
  POST /tickets/{id}/feedback — approve / correct a ticket
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agent import run_agent, warm_up
from app.config import get_settings
from app.database import (
    cleanup_old_tickets, get_metrics, get_ticket_by_id,
    get_thread_tickets, get_tickets, init_db, save_feedback,
)

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Support Agent",
    description="Classifies, prioritises, drafts replies, and routes tickets automatically.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth middleware (disabled when API_KEY is empty) ──────────────────────────

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if settings.API_KEY and request.url.path not in (
        "/health", "/docs", "/redoc", "/openapi.json"
    ):
        if request.headers.get("X-API-Key", "") != settings.API_KEY:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
    return await call_next(request)


# ── Request logging ───────────────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start    = time.perf_counter()
    response = await call_next(request)
    elapsed  = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({elapsed:.0f}ms)"
    )
    return response


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    deleted = cleanup_old_tickets(settings.RETENTION_DAYS)
    if deleted:
        logger.info(f"Retention: removed {deleted} tickets older than {settings.RETENTION_DAYS}d")
    asyncio.create_task(warm_up())
    logger.info(
        f"AI Support Agent v3.0 started | "
        f"provider={settings.LLM_PROVIDER} | "
        f"auth={'enabled' if settings.API_KEY else 'disabled'}"
    )


# ── Pydantic models ───────────────────────────────────────────────────────────

class TicketRequest(BaseModel):
    text:        str = Field(..., min_length=10, max_length=2000)
    customer_id: str = Field("", max_length=100)
    thread_id:   str = Field("", max_length=100)


class TicketResponse(BaseModel):
    ticket_id:   int
    category:    str
    priority:    str
    confidence:  int
    grounded:    bool
    route_to:    str
    reply_draft: str


class FeedbackRequest(BaseModel):
    approved:           bool
    corrected_category: str | None = None
    corrected_reply:    str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {
        "status":   "ok",
        "version":  "3.0.0",
        "provider": settings.LLM_PROVIDER,
        "model": (
            settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai"
            else settings.OLLAMA_MODEL
        ),
        "auth": bool(settings.API_KEY),
    }


@app.post("/analyze", response_model=TicketResponse, tags=["Agent"])
@limiter.limit("10/minute")
async def analyze(request: Request, ticket: TicketRequest):
    """Analyse a support ticket and persist the result."""
    try:
        result = await run_agent(
            ticket.text,
            customer_id=ticket.customer_id,
            thread_id=ticket.thread_id,
        )
        return TicketResponse(
            ticket_id=result["ticket_id"],
            category=result["category"],
            priority=result["priority"],
            confidence=result["confidence"],
            grounded=result["grounded"],
            route_to=result["route_to"],
            reply_draft=result["reply"],
        )
    except Exception as exc:
        logger.error(f"/analyze error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process ticket")


@app.post("/analyze/stream", tags=["Agent"])
@limiter.limit("10/minute")
async def analyze_stream(request: Request, ticket: TicketRequest):
    """
    SSE streaming analysis.

    Events emitted: start | result | error | done
    Each event: data: {event: string, ...payload}\n\n
    """
    async def _stream() -> AsyncIterator[str]:
        def sse(event: str, payload: dict) -> str:
            return f"data: {json.dumps({'event': event, **payload})}\n\n"

        yield sse("start", {"message": "Analysing ticket..."})
        try:
            t0     = time.perf_counter()
            result = await run_agent(
                ticket.text,
                customer_id=ticket.customer_id,
                thread_id=ticket.thread_id,
            )
            elapsed = round(time.perf_counter() - t0, 1)
            yield sse("result", {
                "ticket_id":   result["ticket_id"],
                "category":    result["category"],
                "priority":    result["priority"],
                "confidence":  result["confidence"],
                "grounded":    result["grounded"],
                "route_to":    result["route_to"],
                "reply_draft": result["reply"],
                "elapsed_s":   elapsed,
            })
        except Exception as exc:
            logger.error(f"/analyze/stream error: {exc}", exc_info=True)
            yield sse("error", {"message": "Failed to process ticket"})
        yield sse("done", {})

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/tickets/{ticket_id}/feedback", tags=["Feedback"])
async def submit_feedback(ticket_id: int, body: FeedbackRequest):
    """Approve or reject a ticket; optionally supply corrected category / reply."""
    if not get_ticket_by_id(ticket_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    fid = save_feedback(
        ticket_id, body.approved,
        body.corrected_category, body.corrected_reply,
    )
    return {"feedback_id": fid, "ticket_id": ticket_id, "approved": body.approved}


@app.get("/tickets", tags=["History"])
async def list_tickets(limit: int = 20, offset: int = 0, route: str | None = None):
    """Paginated ticket history. Filter with ?route=Human+Review."""
    if limit > 200:
        raise HTTPException(status_code=400, detail="limit must be <= 200")
    return get_tickets(limit=limit, offset=offset, route_filter=route)


@app.get("/tickets/thread/{thread_id}", tags=["History"])
async def thread_history(thread_id: str, limit: int = 10):
    """All tickets for a thread, oldest first."""
    return get_thread_tickets(thread_id, limit=limit)


@app.get("/metrics", tags=["History"])
async def metrics():
    """Aggregate stats: totals, grounding rate, category/priority breakdown."""
    return get_metrics()
