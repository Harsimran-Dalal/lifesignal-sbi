# LifeSignal — Proactive Agentic AI for Life-Event-Driven Banking Engagement

**Team:** Harsimran Singh Dalal & Sparsh Bhaskar — Thapar Institute of Engineering and Technology

LifeSignal detects life-event signals from customer transaction patterns and autonomously sends hyper-personalized SBI product recommendations via WhatsApp or YONO push — before the customer asks.

---

## Overview

| Layer | Technology |
|-------|------------|
| API | FastAPI |
| Agent orchestration | LangGraph |
| LLM | OpenAI GPT-4o (async) |
| RAG | ChromaDB + text-embedding-3-small |
| Signal detection | XGBoost + rule-based fallback |
| Database | PostgreSQL (SQLAlchemy) |
| Event queue | Redis |
| Deployment | Docker + docker-compose |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Transaction    │     │  Signal Detection │     │  LangGraph      │
│  Data (PG)      │────▶│  XGBoost + Rules  │────▶│  Agent Loop     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
         ┌─────────────────────────────────────────────────┼──────────────────────┐
         │                     │              │            │           │          │
         ▼                     ▼              ▼            ▼           ▼          ▼
   ┌───────────┐        ┌────────────┐  ┌──────────┐ ┌─────────┐ ┌────────┐ ┌───────┐
   │ RAG       │        │ Profile    │  │ Message  │ │Compliance│ │Channel │ │Feedback│
   │ ChromaDB  │        │ Fetcher    │  │ GPT-4o   │ │ Checker  │ │ Router │ │ Tracker│
   └───────────┘        └────────────┘  └──────────┘ └─────────┘ └────────┘ └───────┘
                                                                              │
                                                                              ▼
                                                                        ┌──────────┐
                                                                        │  Redis   │
                                                                        │  Queue   │
                                                                        └──────────┘
```

**Agent flow:** `rag_lookup` → `profile_fetcher` → `message_generator` → `compliance_checker` → (retry if fail, max 2) → `channel_router`

**Detected life events:** `new_job`, `marriage`, `pre_retirement`, `child_birth`, `business_started`, `none`

---

## Setup

### 1. Clone and configure

```bash
cd lifesignal-sbi
cp .env.example .env
# Add your OPENAI_API_KEY to .env (optional — fallback messages work without it)
```

### 2. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and the FastAPI app on `http://localhost:8000`.

### 3. Install Python deps (for local demo CLI)

```bash
pip install -r requirements.txt
```

Ensure `.env` points to local services:

```
DATABASE_URL=postgresql://user:password@localhost:5432/lifesignal
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
```

---

## Demo Usage

### CLI simulation (recommended for hackathon demo)

```bash
python demo/simulate_event.py --customer_id 7
```

Output includes:
- Customer profile
- XGBoost / rule-based signal detection
- Full agent trace (tool call order)
- Final WhatsApp message and product recommendation

Try other injected-signal customers: `1`, `2`, `3`, … (20 of 100 have clear life-event patterns).

### API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + Redis queue depth |
| GET | `/customers` | List all mock customers |
| POST | `/trigger/{customer_id}` | Run signal detection + agent |
| GET | `/nudges` | Sent nudges with outcomes |

```bash
curl http://localhost:8000/health
curl http://localhost:8000/customers
curl -X POST http://localhost:8000/trigger/7
curl http://localhost:8000/nudges
```

---

## Project Structure

```
lifesignal-sbi/
├── main.py                    # FastAPI app
├── docker-compose.yml
├── requirements.txt
├── agents/lifesignal_agent.py # LangGraph StateGraph
├── tools/                     # RAG, profile, message, compliance
├── signal_detection/          # XGBoost classifier
├── data/                      # Mock transactions + SBI catalog
├── channel/router.py          # Mock WhatsApp / push sender
├── feedback/tracker.py        # Nudge outcome logging
├── event_queue/redis_queue.py # Redis event queue
└── demo/simulate_event.py     # End-to-end CLI demo
```

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | FastAPI (Python 3.11) |
| Agent | LangGraph StateGraph |
| LLM | GPT-4o via AsyncOpenAI |
| Embeddings | text-embedding-3-small |
| Vector DB | ChromaDB |
| ML | XGBoost + scikit-learn |
| ORM | SQLAlchemy 2.0 |
| Cache / Queue | Redis |
| DB | PostgreSQL 16 |

---

## Compliance & Safety

Outbound messages pass a rule-based compliance checker that blocks banned phrases (`guaranteed returns`, `risk-free`, etc.). Failed drafts are regenerated up to 2 times before the nudge is dropped.

---

## License

Built for SBI Hackathon 2025 — demo / prototype use only.
