"""
app/main.py — FastAPI application: routes, middleware, startup.

Endpoints:
  POST /analyze        — analyse a support ticket (rate-limited)
  GET  /health         — liveness / model info
  GET  /tickets        — paginated ticket history
  GET  /metrics        — aggregate stats (counts, avg confidence)
"""

import logging
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agent import run_agent
from app.config import get_settings
from app.database import get_metrics, get_tickets, init_db

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT],
)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Support Agent",
    description=(
        "AI-powered customer support ticket analysis. "
        "Classifies, prioritises, drafts replies, and routes tickets automatically."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production (e.g. your frontend domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.0f}ms)"
    )
    return response


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    logger.info(
        f"AI Support Agent v2.0 started | "
        f"provider={settings.LLM_PROVIDER} | "
        f"rate_limit={settings.RATE_LIMIT}"
    )


# ── Pydantic models ───────────────────────────────────────────────────────────

class TicketRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Customer support ticket text",
    )


class TicketResponse(BaseModel):
    category: str
    priority: str
    confidence: int
    grounded: bool
    route_to: str
    reply_draft: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """Liveness check — also returns current model info."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "provider": settings.LLM_PROVIDER,
        "model": (
            settings.OPENAI_MODEL
            if settings.LLM_PROVIDER == "openai"
            else settings.OLLAMA_MODEL
        ),
    }


@app.post("/analyze", response_model=TicketResponse, tags=["Agent"])
@limiter.limit("10/minute")
async def analyze(request: Request, ticket: TicketRequest):
    """
    Analyse a support ticket.

    Returns category, priority, confidence score, grounding check,
    routing destination, and a draft customer reply.
    """
    try:
        result = await run_agent(ticket.text)
        return TicketResponse(
            category=result["category"],
            priority=result["priority"],
            confidence=result["confidence"],
            grounded=result["grounded"],
            route_to=result["route_to"],
            reply_draft=result["reply"],
        )
    except Exception as exc:
        logger.error(f"Unhandled error in /analyze: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process ticket")


@app.get("/tickets", tags=["History"])
async def list_tickets(limit: int = 20, offset: int = 0):
    """Paginated list of processed tickets (newest first)."""
    if limit > 200:
        raise HTTPException(status_code=400, detail="limit must be ≤ 200")
    return get_tickets(limit=limit, offset=offset)


@app.get("/metrics", tags=["History"])
async def metrics():
    """Aggregate stats: totals, counts by category/priority, average confidence."""
    return get_metrics()
