"""
app/router.py — Business routing rules.

Maps (category, priority) to a support team.

Note: Critical priority and low-confidence/ungrounded cases are escalated
in agent.py before this function is reached.

Categories align with the Bitext dataset:
  Account | Billing | Order | Shipping | Technical Support | Feedback | Other
"""

# Routing table: category -> team
_CATEGORY_ROUTES: dict[str, str] = {
    "Account":           "Account Support",
    "Billing":           "Finance",
    "Order":             "Order Management",
    "Shipping":          "Logistics",
    "Technical Support": "Engineering",
    "Feedback":          "Product",
    "Other":             "General Support",
    # Legacy categories (kept for backward compatibility)
    "Login Issue":       "Account Support",
    "Bug Report":        "Engineering",
    "Feature Request":   "Product",
}


def route_ticket(category: str, priority: str) -> str:
    """
    Return the team name this ticket should be routed to.

    Priority overrides happen in agent.py before this is called:
      - Critical          -> Senior Support
      - confidence < 6    -> Human Review
      - grounded = false  -> Human Review

    Here we apply category + priority business rules.
    """
    # High-priority technical / order issues get a faster queue
    if category == "Technical Support" and priority in ("High", "Critical"):
        return "Engineering — Urgent"

    if category == "Order" and priority in ("High", "Critical"):
        return "Order Management — Urgent"

    if category == "Billing" and priority == "High":
        return "Finance — Urgent"

    return _CATEGORY_ROUTES.get(category, "General Support")
