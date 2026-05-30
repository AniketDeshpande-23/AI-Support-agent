"""
app/pipeline.py — Single LLM call that replaces the old 3-call pipeline.

Previously: classify_ticket() + detect_sentiment() + generate_reply() = 3 LLM calls.
Now:        analyze_ticket()                                            = 1 LLM call.

~3x faster, more coherent output (model sees the full picture at once).
"""

import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)


# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT = """You are an expert AI customer support analyst.

Analyze the support ticket below using the provided documentation. In a single pass:

1. Classify into ONE category:
   Account | Billing | Order | Shipping | Technical Support | Feedback | Other

2. Assess urgency: Low | Medium | High | Critical

3. Write a professional, empathetic response based ONLY on the documentation.
   If the documentation does not cover the issue, say so and offer to escalate.

4. Rate confidence in your response (1-10):
   - 8-10: fully covered by docs
   - 5-7:  partially covered
   - 1-4:  not covered / uncertain

5. Set grounded=true only if the response is fully supported by the documentation.

Return ONLY valid JSON — no markdown fences, no extra text:

{{
  "category": "Account",
  "priority": "High",
  "reply": "Dear customer, ...",
  "confidence": 8,
  "grounded": true
}}

Support Ticket:
{ticket}

Relevant Documentation:
{context}
"""

# ── Validation constants ───────────────────────────────────────────────────────

_VALID_CATEGORIES = {
    "Account", "Billing", "Order", "Shipping",
    "Technical Support", "Feedback", "Other",
}
_VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}

_FALLBACK = {
    "category": "Other",
    "priority": "Medium",
    "reply": "Thank you for reaching out. A support specialist will review your request shortly.",
    "confidence": 3,
    "grounded": False,
}


# ── JSON extraction ───────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Robustly extract JSON from LLM output, handling markdown fences and prose."""
    # 1. Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences (```json ... ```)
    stripped = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. Extract outermost {...} block (greedy — first { to last })
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    logger.warning("JSON extraction failed — using fallback values")
    return _FALLBACK.copy()


def _validate(data: dict) -> dict:
    """Sanitize and clamp all fields to valid ranges."""
    try:
        conf = int(data.get("confidence", 5))
        conf = max(1, min(10, conf))
    except (TypeError, ValueError):
        conf = 5

    return {
        "category": data["category"] if data.get("category") in _VALID_CATEGORIES else "Other",
        "priority": data["priority"] if data.get("priority") in _VALID_PRIORITIES else "Medium",
        "reply": str(data.get("reply") or _FALLBACK["reply"]).strip(),
        "confidence": conf,
        "grounded": bool(data.get("grounded", False)),
    }


# ── Main entry point ──────────────────────────────────────────────────────────

async def analyze_ticket(ticket: str, context: str, llm) -> dict:
    """
    Run a single LLM call to classify, prioritize, and draft a reply.

    Works with both:
      - BaseLLM  (OllamaLLM)   → returns str
      - BaseChatModel (ChatOpenAI) → returns AIMessage with .content
    """
    prompt = _PROMPT.format(ticket=ticket, context=context)

    try:
        # Try async first; fall back to sync-in-thread for models that don't support ainvoke
        try:
            response = await llm.ainvoke(prompt)
        except (AttributeError, NotImplementedError):
            response = await asyncio.to_thread(llm.invoke, prompt)

        # Normalise response to string
        text = response.content if hasattr(response, "content") else str(response)
        data = _extract_json(text)
        return _validate(data)

    except Exception as exc:
        logger.error(f"LLM pipeline error: {exc}", exc_info=True)
        return _FALLBACK.copy()
