# app/classifier.py

from app.config import llm
import json
import re

CATEGORIES = ["Billing", "Login Issue", "Bug Report", "Feature Request", "Other"]


def extract_json(text: str):
    try:
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {"category": "Other"}


def classify_ticket(text: str):
    prompt = f"""
Classify this support ticket into ONE category:

Billing, Login Issue, Bug Report, Feature Request, Other

Return ONLY JSON like:
{{"category":"Billing"}}

Ticket:
{text}
"""

    response = llm.invoke(prompt)
    return extract_json(response)
