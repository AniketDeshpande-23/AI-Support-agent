# AI Support Ticket Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%2F%20OpenAI-orange)
![RAG](https://img.shields.io/badge/RAG-FAISS-blueviolet)
![FastAPI](https://img.shields.io/badge/FastAPI-v3.0-green)
![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)
![Dataset](https://img.shields.io/badge/Dataset-Bitext%2026k-9cf)
![CI](https://github.com/AniketDeshpande-23/AI-Support-agent/actions/workflows/ci.yml/badge.svg)

Processes customer support tickets end-to-end — classifies, retrieves grounded answers from a real knowledge base, drafts a reply, scores confidence, and routes to the right team. Runs fully locally via Ollama or in the cloud via OpenAI.

---

## How It Works

```
Customer ticket  +  optional customer_id / thread_id
      │
      ▼
Thread history lookup (if thread_id supplied — multi-turn context)
      │
      ▼
FAISS vector search → top-3 passages from knowledge base (Bitext 26k corpus)
      │
      ▼
Single LLM call (qwen3.5:9b / GPT-4o-mini)
  ├─ Category  : Account | Billing | Order | Shipping | Technical Support | Feedback | Other
  ├─ Priority  : Low | Medium | High | Critical
  ├─ Reply     : grounded in retrieved documentation
  ├─ Confidence: 1–10
  └─ Grounded  : true / false
      │
      ▼
Routing
  ├─ Critical              → Senior Support
  ├─ Confidence < 6        → Human Review
  ├─ Not grounded          → Human Review
  ├─ Billing + High        → Finance — Urgent
  ├─ Order + High          → Order Management — Urgent
  ├─ Technical + High      → Engineering — Urgent
  └─ By category default   → Account Support | Logistics | Finance | Engineering | Product
      │
      ▼
JSON response  +  SQLite log  +  SSE stream (optional)
```

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 3.0, Pydantic v2, slowapi |
| LLM | Ollama (`qwen3.5:9b`) or OpenAI (`gpt-4o-mini`) |
| Embeddings | `nomic-embed-text` (Ollama) or `text-embedding-3-small` (OpenAI) |
| Vector store | FAISS (LangChain) |
| Knowledge base | [Bitext Customer Support Dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset) — 26,872 Q&A pairs |
| Database | SQLite with 90-day retention |
| React UI | Vite + TypeScript (strict) + Tailwind v4 + Recharts + Lucide |
| Streamlit UI | Python fallback (no Node required) |
| Containers | Docker + docker-compose (backend + React + Streamlit) |
| CI | GitHub Actions — backend import/lint + React typecheck/build |

---

## Project Structure

```
ai-support-agent/
├── app/
│   ├── main.py          # FastAPI — routes, auth middleware, SSE, rate limiting
│   ├── agent.py         # Pipeline orchestrator — warm-up, thread context
│   ├── pipeline.py      # Single LLM call: classify + reply + confidence + grounded
│   ├── retriever.py     # FAISS vector store
│   ├── router.py        # Routing rules
│   ├── config.py        # Settings (API_KEY, RETENTION_DAYS, provider toggle)
│   └── database.py      # SQLite — tickets, feedback table, retention, thread queries
├── data/
│   ├── knowledge_base.txt   # RAG corpus (Bitext + hand-written SOPs)
│   ├── eval_samples.json    # 200 labelled eval samples
│   └── faiss_index/         # Auto-generated
├── ui-react/            # React + Vite frontend (port 5173)
│   └── src/
│       ├── views/       # AnalyzeView, DashboardView, LiveFeedView, ReviewView
│       ├── components/  # ConfidenceArc, Badge, KpiCard, Sidebar
│       └── hooks/       # useAnalyze, useMetrics, useLiveFeed, useHealth, useReviewQueue
├── ui/
│   └── app.py           # Streamlit frontend (port 8501)
├── scripts/
│   ├── build_knowledge_base.py   # Download Bitext, build KB + eval set
│   ├── clean_knowledge_base.py   # Replace template placeholders in KB
│   └── benchmark_models.py       # Compare Ollama models on quality + speed
├── evaluation/
│   └── evaluation.py    # Offline eval — accuracy, grounding, confidence, latency
├── .github/
│   └── workflows/ci.yml # CI: backend import/lint + React typecheck/build
├── Dockerfile            # Backend
├── Dockerfile.ui         # Streamlit
├── Dockerfile.react      # React (multi-stage nginx)
├── docker-compose.yml    # All services
├── nginx.conf            # React production server config
└── .env.example
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/AniketDeshpande-23/AI-Support-agent.git
cd ai-support-agent
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Optional: enable API key auth (leave empty to disable)
API_KEY=

# Delete tickets older than N days
RETENTION_DAYS=90
```

Switch to OpenAI: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.

### 3. Pull Ollama models

```bash
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

### 4. Build the knowledge base

```bash
python scripts/build_knowledge_base.py
```

Downloads Bitext dataset (~10 MB), writes `data/knowledge_base.txt` and `data/eval_samples.json`.

---

## Running

### Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FAISS index and LLM warm up in background on first start — no cold-start delay on first request.

### React UI

```bash
cd ui-react && npm install && npm run dev   # http://localhost:5173
```

### Streamlit UI (no Node required)

```bash
streamlit run ui/app.py                     # http://localhost:8501
```

### Docker (all services)

```bash
docker-compose up --build
# With local Ollama:
docker-compose --profile ollama up --build
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Analyse a ticket — returns category, priority, reply, confidence, route, ticket_id |
| `POST` | `/analyze/stream` | SSE streaming — emits `start → result → done` events |
| `POST` | `/tickets/{id}/feedback` | Approve / reject a ticket; optionally supply corrected category + reply |
| `GET` | `/tickets` | Paginated history (`?limit=&offset=&route=Human+Review`) |
| `GET` | `/tickets/thread/{id}` | All tickets in a conversation thread |
| `GET` | `/metrics` | Totals, grounding rate, category/priority breakdown |
| `GET` | `/health` | Backend status, model, auth state |
| `GET` | `/docs` | Swagger UI |

**Auth** — when `API_KEY` is set in `.env`, all endpoints except `/health` and `/docs` require header `X-API-Key: <key>`.

**Request**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice for my last order.", "customer_id": "u123", "thread_id": "t456"}'
```

**Response**

```json
{
  "ticket_id":   42,
  "category":    "Billing",
  "priority":    "High",
  "confidence":  8,
  "grounded":    true,
  "route_to":    "Finance — Urgent",
  "reply_draft": "We'll investigate the duplicate charge and process a refund within 3–5 business days..."
}
```

---

## React UI — Triage

| View | Features |
|---|---|
| **Analyze** | Sample picker, textarea, animated confidence arc, streaming reply, category/priority/route badges |
| **Dashboard** | KPI cards (total, avg confidence, human-review count, grounding rate), 4 Recharts charts |
| **Live Feed** | Auto-polls every 5 s, priority-bordered cards, pause/resume, detail drawer |
| **Review Queue** | Human Review tickets with approve/reject + optional reply correction |

---

## Evaluation

```bash
python evaluation/evaluation.py --samples 50
python evaluation/evaluation.py --samples 200 --output results.json
```

Reports category accuracy, grounding rate, avg confidence, human-review rate, avg latency.
