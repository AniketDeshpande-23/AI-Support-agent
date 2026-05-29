"""
app/router.py — Business routing rules.

Note: Critical priority and low-confidence cases are escalated in agent.py
before this function is reached.
"""


def route_ticket(category: str, priority: str) -> str:
    if category == "Bug Report" and priority in ("High", "Critical"):
        return "Engineering"
    if category == "Billing":
        return "Finance"
    if category == "Feature Request":
        return "Product"
    return "General Support"
