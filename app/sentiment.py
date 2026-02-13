# app/sentiment.py

from app.config import llm
import json
import re


def extract_json(text: str):
    try:
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {"priority": "Medium"}


def detect_sentiment(text: str):
    prompt = f"""
Classify urgency level of this support ticket.

Return ONLY JSON:
{{"priority":"Low | Medium | High | Critical"}}

Ticket:
{text}
"""

    response = llm.invoke(prompt)
    return extract_json(response)
