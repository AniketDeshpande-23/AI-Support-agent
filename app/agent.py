from app.classifier import classify_ticket
from app.sentiment import detect_sentiment
from app.retriever import build_vector_store, retrieve_solution
from app.responder import generate_reply
from app.router import route_ticket
from app.database import save_ticket

vectorstore = build_vector_store()


def run_agent(ticket_text: str):
    classification = classify_ticket(ticket_text)
    sentiment = detect_sentiment(ticket_text)

    category = classification.get("category", "Other")
    priority = sentiment.get("priority", "Medium")

    solution = retrieve_solution(vectorstore, ticket_text)

    reply_data = generate_reply(ticket_text, solution)

    reply_text = reply_data.get("reply", "")
    confidence = reply_data.get("confidence", 5)
    grounded = reply_data.get("grounded", False)

    # Auto-escalation logic
    if priority == "Critical":
        route = "Senior Support"
    elif confidence < 6:
        route = "Human Review"
    elif not grounded:
        route = "Human Review"
    else:
        route = route_ticket(category, priority)

    # Save record
    record = {
        "ticket_text": ticket_text,
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "grounded": grounded,
        "route_to": route,
        "reply": reply_text
    }

    save_ticket(record)

    return {
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "grounded": grounded,
        "route_to": route,
        "reply_draft": reply_text
    }
