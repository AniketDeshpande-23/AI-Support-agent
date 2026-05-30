"""
evaluation/evaluation.py

Offline evaluation using labelled samples built from the Bitext dataset.

Usage:
    python evaluation/evaluation.py [--samples N] [--output results.json]

Requirements:
    - Backend must NOT be running (we call run_agent() directly)
    - data/eval_samples.json must exist (run scripts/build_knowledge_base.py first)
    - .env must be configured

Metrics reported:
    - Category accuracy
    - Routing correctness
    - Average confidence
    - Grounding rate
    - Human-review escalation rate
"""

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter, defaultdict

# Run from project root so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import run_agent


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_samples(path: str, limit: int) -> list[dict]:
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        print("Run:  python scripts/build_knowledge_base.py")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        samples = json.load(f)
    return samples[:limit]


def print_header(n: int) -> None:
    print(f"\n{'='*60}")
    print(f"  AI Support Agent — Offline Evaluation ({n} samples)")
    print(f"{'='*60}\n")


def print_results(metrics: dict) -> None:
    print(f"\n{'='*60}")
    print("  RESULTS")
    print(f"{'='*60}")
    print(f"  Samples evaluated  : {metrics['total']}")
    print(f"  Category accuracy  : {metrics['cat_accuracy']:.1%}")
    print(f"  Avg confidence     : {metrics['avg_confidence']:.1f} / 10")
    print(f"  Grounding rate     : {metrics['grounding_rate']:.1%}")
    print(f"  Human-review rate  : {metrics['human_review_rate']:.1%}")
    print(f"  Avg latency        : {metrics['avg_latency_ms']:.0f} ms")
    print(f"\n  Category breakdown:")
    for cat, stats in sorted(metrics["by_category"].items()):
        acc = stats["correct"] / stats["total"] if stats["total"] else 0
        print(f"    {cat:<25} {stats['total']:>3} samples | acc {acc:.0%} | "
              f"avg conf {stats['avg_conf']:.1f}")
    print()


# ── Main evaluation loop ──────────────────────────────────────────────────────

async def evaluate(samples: list[dict]) -> dict:
    total       = len(samples)
    correct_cat = 0
    confidences = []
    grounded    = []
    human_rev   = []
    latencies   = []

    by_category: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0, "confs": []})

    for i, sample in enumerate(samples, 1):
        ticket   = sample["ticket"]
        expected = sample["expected_category"]

        t0     = time.perf_counter()
        result = await run_agent(ticket)
        ms     = (time.perf_counter() - t0) * 1000

        predicted = result.get("category", "Other")
        conf      = result.get("confidence", 0)
        is_ground = result.get("grounded", False)
        route     = result.get("route_to", "")

        match = (predicted == expected)
        correct_cat     += int(match)
        confidences.append(conf)
        grounded.append(is_ground)
        human_rev.append("Human Review" in route)
        latencies.append(ms)

        by_category[expected]["total"]   += 1
        by_category[expected]["correct"] += int(match)
        by_category[expected]["confs"].append(conf)

        status = "OK " if match else "ERR"
        print(f"  [{i:>3}/{total}] {status} | expected={expected:<20} got={predicted:<20} "
              f"conf={conf} grounded={is_ground} route={route}")

    # Aggregate by-category averages
    cat_stats = {}
    for cat, s in by_category.items():
        cat_stats[cat] = {
            "total":    s["total"],
            "correct":  s["correct"],
            "avg_conf": sum(s["confs"]) / len(s["confs"]) if s["confs"] else 0,
        }

    return {
        "total":             total,
        "cat_accuracy":      correct_cat / total if total else 0,
        "avg_confidence":    sum(confidences) / total if total else 0,
        "grounding_rate":    sum(grounded) / total if total else 0,
        "human_review_rate": sum(human_rev) / total if total else 0,
        "avg_latency_ms":    sum(latencies) / total if total else 0,
        "by_category":       cat_stats,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate AI Support Agent")
    parser.add_argument("--samples", type=int, default=50,
                        help="Number of eval samples to run (default: 50)")
    parser.add_argument("--output", type=str, default=None,
                        help="Optional path to save JSON results")
    args = parser.parse_args()

    samples = load_samples("data/eval_samples.json", args.samples)
    print_header(len(samples))

    metrics = asyncio.run(evaluate(samples))
    print_results(metrics)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"  Results saved to: {args.output}\n")


if __name__ == "__main__":
    main()
