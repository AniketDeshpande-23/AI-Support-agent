# AI Support Ticket Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%2F%20OpenAI-orange)
![RAG](https://img.shields.io/badge/RAG-FAISS-blueviolet)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-green)
![React](https://img.shields.io/badge/React-frontend-61dafb?logo=react&logoColor=white)
![Dataset](https://img.shields.io/badge/Dataset-Bitext%2026k-9cf)

Processes customer support tickets end-to-end — classifies, retrieves grounded answers from a real knowledge base, drafts a reply, scores confidence, and routes to the right team. Runs fully locally via Ollama or in the cloud via OpenAI.

---

## How It Works

```
Customer ticket
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
JSON response + SQLite log
```

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Pydantic v2, slowapi |
| LLM | Ollama (`qwen3.5:9b`) or OpenAI (`gpt-4o-mini`) |
| Embeddings | `nomic-embed-text` (Ollama) or `text-embedding-3-small` (OpenAI) |
| Vector store | FAISS (LangChain) |
| Knowledge base | [Bitext Customer Support Dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset) — 26,872 Q&A pairs |
| Database | SQLite |
| React UI | Vite + TypeScript + Tailwind v4 + Recharts + Lucide |
| Streamlit UI | Python fallback (no Node required) |
| Containers | Docker + docker-compose |

---

## Project Structure

```
ai-support-agent/
├── app/
│   ├── main.py          # FastAPI — routes, CORS, rate limiting, request logging
│   ├── agent.py         # Pipeline orchestrator
│   ├── pipeline.py      # Single LLM call: classify + reply + confidence + grounded
│   ├── retriever.py     # FAISS vector store — build from KB or load from disk
│   ├── router.py        # Routing rules
│   ├── config.py        # Settings, LLM factory (Ollama ↔ OpenAI toggle)
│   └── database.py      # SQLite — save, list, metrics
├── data/
│   ├── knowledge_base.txt   # RAG corpus built from Bitext dataset
│   ├── eval_samples.json    # 200 labelled samples for evaluation
│   └── faiss_index/         # Auto-generated (deleted on KB rebuild)
├── ui-react/            # React + Vite frontend (port 5173)
│   └── src/
│       ├── views/       # AnalyzeView, DashboardView, LiveFeedView
│       ├── components/  # ConfidenceArc, Badge, KpiCard, Sidebar
│       └── hooks/       # useAnalyze, useMetrics, useLiveFeed, useHealth
├── ui/
│   └── app.py           # Streamlit frontend (port 8501)
├── scripts/
│   ├── build_knowledge_base.py   # Download Bitext, build KB + eval set
│   └── clean_knowledge_base.py   # Replace template placeholders in KB
├── evaluation/
│   └── evaluation.py    # Offline eval — accuracy, grounding, confidence, latency
├── Dockerfile
├── Dockerfile.ui
├── docker-compose.yml
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
```

Switch to OpenAI by setting `LLM_PROVIDER=openai` and adding `OPENAI_API_KEY`.

### 3. Pull Ollama models

```bash
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

### 4. Build the knowledge base

```bash
python scripts/build_knowledge_base.py
```

Downloads the Bitext dataset (~10 MB from HuggingFace), writes `data/knowledge_base.txt` and `data/eval_samples.json`, deletes stale FAISS index.

---

## Running

### Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### React UI (recommended)

```bash
cd ui-react
npm install
npm run dev        # http://localhost:5173
```

### Streamlit UI (no Node required)

```bash
streamlit run ui/app.py    # http://localhost:8501
```

### Docker

```bash
docker-compose up --build
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Analyze a ticket — returns category, priority, reply, confidence, route |
| `GET` | `/health` | Backend status and active model |
| `GET` | `/tickets?limit=N&offset=N` | Paginated ticket history |
| `GET` | `/metrics` | Totals, category/priority breakdown, avg confidence |
| `GET` | `/docs` | Swagger UI |

**Request**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice for my last order and need a refund."}'
```

**Response**

```json
{
  "category":    "Billing",
  "priority":    "High",
  "confidence":  8,
  "grounded":    true,
  "route_to":    "Finance — Urgent",
  "reply_draft": "I'm sorry to hear you were charged twice. We'll investigate and process a refund within 3–5 business days..."
}
```

---

## Evaluation

```bash
python evaluation/evaluation.py --samples 50
python evaluation/evaluation.py --samples 200 --output results.json
```

Reports category accuracy, grounding rate, avg confidence, human-review escalation rate, and avg latency per ticket.

---

## React UI — Triage

Three views built with React 19, TypeScript (strict), Tailwind v4, Recharts, Lucide.

| View | What it shows |
|---|---|
| **Analyze** | Sample ticket picker, textarea, animated confidence arc, streaming reply, category/priority/route badges |
| **Dashboard** | KPI cards — total tickets, avg confidence, high/critical count, grounding rate. Four charts — category donut, priority bar, confidence histogram, routing distribution |
| **Live Feed** | Auto-polls every 5 s, priority-bordered ticket cards, pause/resume toggle, slide-over detail drawer |
