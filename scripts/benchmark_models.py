"""
scripts/benchmark_models.py  —  Compare Ollama models: quality + speed.

Tests 4 tickets across candidate models.
Qwen3 models are tested with think=False to suppress reasoning chains.

Usage:  python scripts/benchmark_models.py
"""
import asyncio, os, sys, time
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from langchain_ollama import ChatOllama
from app.config import get_embeddings
from app.retriever import get_vectorstore, retrieve_solution
from app.pipeline import analyze_ticket

# (model_name, think_mode)  — Qwen3 supports think=False for no chain-of-thought
CANDIDATES = [
    ("qwen3.5:9b",  False),   # thinking OFF — fast mode
    ("qwen3.5:9b",  True),    # thinking ON  — slower but potentially better
    ("gemma4:31b",  None),    # not a thinking model
]

TICKETS = [
    {"text": "I cannot login. Invalid password error after resetting my password.", "expected": "Account"},
    {"text": "I was charged twice for order #12345. Need a refund immediately.",    "expected": "Billing"},
    {"text": "My package shows delivered but never arrived. Order #99201.",         "expected": "Shipping"},
    {"text": "I want to cancel my order placed 5 minutes ago — wrong size.",       "expected": "Order"},
]


async def bench(model: str, think, vs, results: list) -> None:
    tag   = "" if think is None else (" +think" if think else " -think")
    label = f"{model}{tag}"
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    kwargs: dict = {"model": model, "temperature": 0.2, "num_predict": 1500}
    if think is not None:
        kwargs["think"] = think          # Ollama Qwen3 think flag
    llm = ChatOllama(**kwargs)

    times, corrects, groundeds, confs = [], [], [], []

    for t in TICKETS:
        ctx = retrieve_solution(vs, t["text"], k=3)
        t0  = time.perf_counter()
        try:
            r   = await analyze_ticket(t["text"], ctx, llm)
            ms  = (time.perf_counter() - t0) * 1000
            ok  = r["category"] == t["expected"]
            times.append(ms); corrects.append(ok)
            groundeds.append(r["grounded"]); confs.append(r["confidence"])
            print(f"  {'OK' if ok else '!!'} {t['expected']:<20} -> {r['category']:<20} "
                  f"conf={r['confidence']:2d}  gnd={r['grounded']}  {ms/1000:.1f}s")
        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            times.append(ms); corrects.append(False); groundeds.append(False); confs.append(0)
            print(f"  !! {t['expected']:<20} ERROR: {str(e)[:40]}  {ms/1000:.1f}s")

    n       = len(TICKETS)
    acc     = sum(corrects)  / n
    gnd     = sum(groundeds) / n
    avg_c   = sum(confs)     / n
    avg_s   = sum(times)     / len(times) / 1000
    score   = acc * 0.4 + gnd * 0.3 + (avg_c / 10) * 0.2 + max(0, 1 - avg_s / 120) * 0.1

    print(f"\n  Accuracy={acc:.0%}  Grounding={gnd:.0%}  Conf={avg_c:.1f}/10  "
          f"Speed={avg_s:.1f}s/ticket  Score={score:.2f}")

    results.append({"label": label, "acc": acc, "gnd": gnd,
                    "avg_c": avg_c, "avg_s": avg_s, "score": score})


async def main():
    print("Loading FAISS index...")
    vs = get_vectorstore(get_embeddings())
    print("Ready.")

    results = []
    for model, think in CANDIDATES:
        await bench(model, think, vs, results)

    print(f"\n{'='*60}")
    print(f"  RANKING  (40% acc + 30% grounding + 20% conf + 10% speed)")
    print(f"{'='*60}")
    print(f"  {'Model':<32} {'Acc':>5} {'Gnd':>5} {'Conf':>5} {'Time':>7} {'Score':>7}")
    print(f"  {'-'*58}")
    for r in sorted(results, key=lambda x: -x["score"]):
        print(f"  {r['label']:<32} {r['acc']:>4.0%} {r['gnd']:>4.0%} "
              f"{r['avg_c']:>5.1f} {r['avg_s']:>6.1f}s {r['score']:>6.2f}")

    best = max(results, key=lambda x: x["score"])
    print(f"\n  Winner: {best['label']}")

asyncio.run(main())
