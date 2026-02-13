from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import run_agent
from app.database import init_db

app = FastAPI()

init_db()


class Ticket(BaseModel):
    text: str


@app.post("/analyze")
async def analyze(ticket: Ticket):
    try:
        return run_agent(ticket.text)
    except Exception as e:
        return {"error": str(e)}
