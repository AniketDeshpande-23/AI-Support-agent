import asyncio, os
os.chdir(r"F:\project\AI Projects\ai-support-agent")

async def test():
    from app import config as cfg
    cfg.get_settings.cache_clear()
    from app.config import get_llm, get_embeddings
    from app.retriever import get_vectorstore, retrieve_solution
    from app.pipeline import analyze_ticket

    emb = get_embeddings()
    vs  = get_vectorstore(emb)
    llm = get_llm()

    tickets = [
        "I cannot login to my account. I keep getting invalid password error even though I just reset it 5 minutes ago.",
        "I was charged twice for my last order and need a refund.",
        "My package was marked delivered but I never received it.",
    ]

    for t in tickets:
        ctx    = retrieve_solution(vs, t, k=3)
        result = await analyze_ticket(t, ctx, llm)
        print(f"Ticket  : {t[:65]}")
        print(f"  cat={result['category']}  pri={result['priority']}  conf={result['confidence']}  grounded={result['grounded']}")
        print(f"  reply : {result['reply'][:130]}")
        print()

asyncio.run(test())
