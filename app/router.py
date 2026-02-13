def route_ticket(category: str, priority: str):
    if category == "Bug Report" and priority in ["High", "Critical"]:
        return "Engineering"
    elif category == "Billing":
        return "Finance"
    elif category == "Feature Request":
        return "Product"
    return "General Support"
