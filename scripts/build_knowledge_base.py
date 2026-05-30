"""
scripts/build_knowledge_base.py

Downloads the Bitext customer-support dataset from HuggingFace and:
  1. Builds data/knowledge_base.txt  — rich, structured support docs (26k rows)
  2. Builds data/eval_samples.json   — 200 labelled samples for offline eval
  3. Prints category/intent stats

Dataset: bitext/Bitext-customer-support-llm-chatbot-training-dataset
  26,872 rows | 11 categories | 27 intents

Run:
    python scripts/build_knowledge_base.py
"""

import json
import os
import random
import shutil
import sys
import textwrap
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datasets import load_dataset

# ── Config ────────────────────────────────────────────────────────────────────

DATASET_ID           = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
KB_PATH              = "data/knowledge_base.txt"
EVAL_PATH            = "data/eval_samples.json"
FAISS_PATH           = "data/faiss_index"
RESPONSES_PER_INTENT = 5    # best unique responses to keep per intent
EVAL_SAMPLES         = 200  # labelled samples for evaluation

random.seed(42)

# ── Category mapping: dataset category -> our system category ─────────────────
# Dataset uses: ACCOUNT, ORDER, REFUND, INVOICE, CONTACT, PAYMENT,
#               FEEDBACK, DELIVERY, SHIPPING, SUBSCRIPTION, CANCEL

DATASET_TO_SYSTEM = {
    "ACCOUNT":      "Account",
    "ORDER":        "Order",
    "REFUND":       "Billing",
    "INVOICE":      "Billing",
    "PAYMENT":      "Billing",
    "CANCEL":       "Order",
    "DELIVERY":     "Shipping",
    "SHIPPING":     "Shipping",
    "CONTACT":      "Technical Support",
    "FEEDBACK":     "Feedback",
    "SUBSCRIPTION": "Account",
}


def build_knowledge_base(dataset) -> None:
    """
    Group unique responses by (system_category, intent), keep the best N,
    and write a structured plain-text knowledge base.
    """
    grouped: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for row in dataset:
        raw_cat  = row.get("category", "").strip().upper()
        intent   = row.get("intent", "").strip()
        response = row.get("response", "").strip()
        category = DATASET_TO_SYSTEM.get(raw_cat, "General Support")

        if response and intent:
            grouped[category][intent].append(response)

    lines = [
        "# AI Support Agent — Knowledge Base",
        "# Source: Bitext Customer Support LLM Chatbot Training Dataset (HuggingFace)",
        "# Dataset: bitext/Bitext-customer-support-llm-chatbot-training-dataset",
        "# 26,872 rows | 11 raw categories | 27 intents",
        "#",
        "# This file is used as the RAG knowledge base.",
        "# The FAISS vector index is built from this file on first startup.",
        "# To refresh: delete data/faiss_index/ and restart the backend.",
        "",
    ]

    total_intents   = 0
    total_responses = 0

    for category in sorted(grouped):
        lines.append(f"\n{'='*72}")
        lines.append(f"CATEGORY: {category}")
        lines.append(f"{'='*72}\n")

        for intent in sorted(grouped[category]):
            responses = grouped[category][intent]
            # Keep longest (most informative) unique responses
            seen    = set()
            unique  = []
            for r in sorted(responses, key=len, reverse=True):
                if r not in seen:
                    seen.add(r)
                    unique.append(r)
                if len(unique) >= RESPONSES_PER_INTENT:
                    break

            label = intent.replace("_", " ").title()
            lines.append(f"--- {label} ---")
            for resp in unique:
                lines.append(textwrap.fill(resp, width=100))
            lines.append("")

            total_intents   += 1
            total_responses += len(unique)

    os.makedirs("data", exist_ok=True)
    with open(KB_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Knowledge base: {len(grouped)} categories | "
          f"{total_intents} intents | {total_responses} snippets -> {KB_PATH}")


def build_eval_samples(dataset) -> None:
    """
    Sample EVAL_SAMPLES rows (stratified by category) and write
    data/eval_samples.json for use by evaluation/evaluation.py.
    """
    # Group by category first for stratified sampling
    by_cat: dict[str, list] = defaultdict(list)
    for row in dataset:
        raw_cat = row.get("category", "").strip().upper()
        cat     = DATASET_TO_SYSTEM.get(raw_cat, "Other")
        q       = row.get("instruction", "").strip()
        r       = row.get("response", "").strip()
        intent  = row.get("intent", "").strip()
        if q and r:
            by_cat[cat].append({
                "ticket":            q,
                "expected_category": cat,
                "expected_intent":   intent,
                "reference_reply":   r,
                "source":            "bitext",
            })

    # Take proportional samples from each category
    samples  = []
    per_cat  = max(1, EVAL_SAMPLES // len(by_cat))
    for rows in by_cat.values():
        random.shuffle(rows)
        samples.extend(rows[:per_cat])

    # Fill to EVAL_SAMPLES if needed
    remaining = [r for rows in by_cat.values() for r in rows[per_cat:]]
    random.shuffle(remaining)
    samples.extend(remaining[:max(0, EVAL_SAMPLES - len(samples))])
    samples = samples[:EVAL_SAMPLES]

    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    print(f"  Eval samples:   {len(samples)} labelled rows -> {EVAL_PATH}")


def print_stats(dataset) -> None:
    from collections import Counter
    cats    = Counter(DATASET_TO_SYSTEM.get(r["category"].upper(), "Other") for r in dataset)
    intents = Counter(r["intent"] for r in dataset)
    print("\n  System categories (after mapping):")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<25} {count:>5} rows")
    print(f"\n  Total intents: {len(intents)}")
    for intent, count in intents.most_common(5):
        print(f"    {intent:<35} {count:>5} rows")
    print("    ...")


def main():
    print(f"\nDownloading '{DATASET_ID}' from HuggingFace ...")
    ds = load_dataset(DATASET_ID, split="train")
    print(f"  Downloaded {len(ds):,} rows")

    print_stats(ds)

    print("\nBuilding knowledge base ...")
    build_knowledge_base(ds)

    print("\nBuilding evaluation samples ...")
    build_eval_samples(ds)

    if os.path.exists(FAISS_PATH):
        shutil.rmtree(FAISS_PATH)
        print(f"\n  Deleted stale FAISS index -> will rebuild on next startup")

    print("\nDone!")
    print("  1. Restart backend:    uvicorn app.main:app --reload")
    print("  2. Run evaluation:     python evaluation/evaluation.py")


if __name__ == "__main__":
    main()
