#  AI Support Ticket Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Generative AI](https://img.shields.io/badge/AI-Generative%20AI-purple)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%2F%20OpenAI-orange)
![RAG](https://img.shields.io/badge/RAG-FAISS%20Retrieval-blueviolet)
![FastAPI](https://img.shields.io/badge/FastAPI-v2.0-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-ff4b4b?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Dataset](https://img.shields.io/badge/Dataset-Bitext%2026k%20rows-9cf)
![Automation](https://img.shields.io/badge/Automation-n8n%20Ready-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

An AI-powered support automation system that classifies customer tickets, retrieves grounded answers from a real knowledge base (26,872 rows from the Bitext dataset), drafts professional replies, and routes issues to the right team — all running locally with Ollama or in the cloud via OpenAI.

---

##  What It Does

```
Customer ticket
      │
      ▼
FAISS vector search ──► top-3 passages from knowledge base (26k-row Bitext corpus)
      │
      ▼
Single LLM call (Mistral / GPT-4o-mini)
  ├─ Classify: Account | Billing | Order | Shipping | Technical Support | Feedback | Other
  ├─ Priority: Low | Medium | High | Critical
  ├─ Draft reply grounded in documentation
  ├─ Confidence score (1–10)
  └─ Grounded flag (true / false)
      │
      ▼
Routing rules
  ├─ Critical            → Senior Support
  ├─ Confidence < 6      → Human Review
  ├─ Not grounded        → Human Review
  ├─ Billing + High      → Finance — Urgent
  ├─ Order + High        → Order Management — Urgent
  ├─ Technical + High    → Engineering — Urgent
  └─ Default by category → see routing table
      │
      ▼
SQLite log + JSON response
```

---

##  Key Features

| Feature | Detail |
|---|---|
| **Real knowledge base** | Built from [Bitext dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset) — 26,872 Q&A pairs, 27 intents, 6 categories |
| **Single LLM call** | ~3x faster than chained classify→sentiment→reply pipelines |
| **Multi-provider** | Toggle Ollama (local/private) ↔ OpenAI (cloud) via `.env` |
| **7 categories** | Account, Billing, Order, Shipping, Technical Support, Feedback, Other |
| **Confidence scoring** | 1–10 per response; low-confidence auto-escalates to Human Review |
| **Hallucination guard** | `grounded` flag — ungrounded replies never go to customers |
| **Priority routing** | High-priority billing/order/tech issues get urgent-queue routes |
| **Rate limiting** | 10 req/min per IP (configurable) |
| **Ticket history** | `GET /tickets` (paginated) + `GET /metrics` (aggregate stats) |
| **Offline evaluation** | `evaluation/evaluation.py` — accuracy, confidence, grounding, latency |
| **Docker ready** | `docker-compose up --build` runs both services |

---

##  Dataset

Knowledge base built from:

> **[Bitext Customer Support LLM Chatbot Training Dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset)**
> 26,872 rows | 11 raw categories | 27 intents | ground-truth Q&A pairs

| Dataset Category | Rows | System Category |
|---|---|---|
| ACCOUNT | 6,985 | Account |
| REFUND + INVOICE + PAYMENT | 6,989 | Billing |
| ORDER + CANCEL | 4,938 | Order |
| DELIVERY + SHIPPING | 3,964 | Shipping |
| CONTACT | 1,999 | Technical Support |
| FEEDBACK | 1,997 | Feedback |

The dataset is processed by `scripts/build_knowledge_base.py` into:
- `data/knowledge_base.txt` — structured RAG corpus (135 curated snippets)
- `data/eval_samples.json` — 200 labelled samples for evaluation

---

##  Project Structure

```
ai-support-agent/
│
├── app/
│   ├── main.py             # FastAPI app — routes, middleware, rate limiting
│   ├── agent.py            # Pipeline orchestrator
│   ├── pipeline.py         # Single LLM call (classify + reply + score)
│   ├── retriever.py        # FAISS vector store + similarity search
│   ├── router.py           # Routing rules (7 categories, priority overrides)
│   ├── config.py           # Settings + LLM/embeddings factory (Ollama/OpenAI)
│   └── database.py         # SQLite helpers
│
├── data/
│   ├── knowledge_base.txt  # RAG corpus — rebuilt from Bitext dataset
│   ├── eval_samples.json   # 200 labelled eval samples
│   ├── faiss_index/        # Auto-generated FAISS index (delete to rebuild)
│   └── kaggle_tickets.csv  # Legacy sample data
│
├── scripts/
│   └── build_knowledge_base.py  # Downloads Bitext dataset, builds KB + eval set
│
├── ui/
│   └── app.py              # Streamlit frontend
│
├── evaluation/
│   └── evaluation.py       # Offline eval: accuracy, confidence, grounding, latency
│
├── Dockerfile              # Backend container
├── Dockerfile.ui           # Streamlit container
├── docker-compose.yml      # Runs backend + UI together
├── .env.example            # Copy to .env and configure
└── requirements.txt
```

---

##  API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Analyze a support ticket |
| `GET` | `/health` | Liveness check + model info |
| `GET` | `/tickets` | Paginated ticket history |
| `GET` | `/metrics` | Aggregate stats (counts, avg confidence) |
| `GET` | `/docs` | Interactive Swagger UI |

---

##  Installation

### 1. Clone

```bash
git clone https://github.com/AniketDeshpande-23/AI-Support-agent.git
cd ai-support-agent
```

### 2. Virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# "ollama" for local inference | "openai" for cloud
LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_EMBED_MODEL=nomic-embed-text

# Only needed when LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
```

### 5. Build the knowledge base (first time only)

```bash
python scripts/build_knowledge_base.py
```

This downloads the Bitext dataset from HuggingFace (~10 MB), builds
`data/knowledge_base.txt` and `data/eval_samples.json`, and deletes any
stale FAISS index so it's rebuilt on next startup.

### 6. Install Ollama (local inference)

Download from https://ollama.com and pull:

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

---

## ▶ Running

### Option A — Manual (two terminals)

```bash
# Terminal 1 — backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — frontend
streamlit run ui/app.py
```

| Service | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI backend | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

### Option B — Docker Compose

```bash
docker-compose up --build
```

---

##  Example API Call

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice for my last order and need a refund."}'
```

```json
{
  "category": "Billing",
  "priority": "High",
  "confidence": 8,
  "grounded": true,
  "route_to": "Finance — Urgent",
  "reply_draft": "Dear customer, we're sorry to hear you were charged twice..."
}
```

---

##  Routing Logic

| Condition | Route |
|---|---|
| Priority = Critical | Senior Support |
| Confidence < 6 OR grounded = false | Human Review |
| Billing + High priority | Finance — Urgent |
| Order + High/Critical | Order Management — Urgent |
| Technical Support + High/Critical | Engineering — Urgent |
| Account | Account Support |
| Shipping | Logistics |
| Feedback | Product |
| Everything else | General Support |

---

##  Offline Evaluation

```bash
# Run 50 samples (fast, ~5 min on Mistral 7B)
python evaluation/evaluation.py --samples 50

# Run full 200-sample eval and save results
python evaluation/evaluation.py --samples 200 --output results.json
```

Sample output:
```
  Samples evaluated  : 50
  Category accuracy  : 78%
  Avg confidence     : 7.4 / 10
  Grounding rate     : 85%
  Human-review rate  : 12%
  Avg latency        : 3200 ms
```

---

##  Updating the Knowledge Base

To refresh after editing `data/knowledge_base.txt`, or to re-download the dataset:

```bash
python scripts/build_knowledge_base.py
# Then restart the backend (FAISS index is deleted + rebuilt automatically)
```

---

##  Ticket Logging

Every ticket is stored in `support_logs.db` and accessible via:

```bash
GET /tickets          # last 20 tickets (paginated)
GET /metrics          # totals, category/priority breakdown, avg confidence
```

---

##  Future Improvements

- [ ] Human-review UI — let agents approve / correct low-confidence replies
- [ ] Feedback loop — log corrections and retrain/fine-tune
- [ ] Multi-turn conversation (ticket thread context)
- [ ] Webhook push — send results to Slack / email / CRM on completion
- [ ] Authentication (API keys / OAuth)
- [ ] Cloud deployment guide (Railway, Render, AWS)

---

##  Why This Project

- Real RAG pipeline backed by a public, citable dataset (not toy data)
- Production FastAPI patterns: rate limiting, CORS, request logging, Pydantic v2
- Safety-first design: confidence scoring + grounding guard prevent bad AI replies
- Multi-provider LLM config: swap local ↔ cloud with one env var
- Offline evaluation harness for measuring accuracy and latency
- Automation-ready JSON output for n8n, Zapier, Slack, CRM integrations
