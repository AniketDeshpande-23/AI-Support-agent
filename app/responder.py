from app.config import llm
import json
import re


def extract_json(text: str):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {
        "reply": text.strip(),
        "confidence": 5,
        "grounded": False
    }


def generate_reply(ticket: str, solution_context: str):
    prompt = f"""
You are a professional customer support agent.

Generate a reply based ONLY on the provided documentation.

Then evaluate:
1. Confidence (1-10)
2. Whether the reply is grounded ONLY in provided documentation (true/false)

Return ONLY JSON:

{{
  "reply": "final message to customer",
  "confidence": 1-10,
  "grounded": true/false
}}

Customer Issue:
{ticket}

Documentation:
{solution_context}
"""

    response = llm.invoke(prompt)
    return extract_json(response)
