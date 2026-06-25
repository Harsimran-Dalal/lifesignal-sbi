<div align="center">

# 🚀 LifeSignal

### **Proactive Agentic AI for Life-Event-Driven Banking Engagement**

**Team:** Harsimran Singh Dalal & Sparsh Bhaskar — Thapar Institute of Engineering and Technology

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-SBI%20Hackathon-red.svg)](LICENSE)

---

## 🎯 What is LifeSignal?

LifeSignal detects **life-event signals** from customer transaction patterns and autonomously sends **hyper-personalized SBI product recommendations** via WhatsApp or YONO push — **before the customer asks**.

### ✨ Key Features

- 🔍 **Intelligent Signal Detection** — XGBoost + rule-based hybrid approach
- 🤖 **Agentic AI Workflow** — LangGraph-powered autonomous decision making
- 📝 **Hyper-Personalized Messaging** — GPT-4o with RAG for contextual recommendations
- ✅ **Compliance-First** — Built-in safety checks and regulatory compliance
- 📱 **Multi-Channel Delivery** — WhatsApp & YONO push notifications
- 🔄 **Real-Time Processing** — Redis-backed event queue for scalability

</div>

---

## 🏗️ System Architecture

<div align="center">

### High-Level Architecture

```mermaid
graph TB
    PG[PostgreSQL<br/>Transaction Data]
    XGB[XGBoost + Rules<br/>Signal Detection]
    AGENT[LangGraph Agent Loop]
    RAG[RAG Lookup<br/>ChromaDB]
    PROFILE[Profile Fetcher]
    MSG[Message Generator<br/>GPT-4o]
    COMP[Compliance Checker]
    ROUTER[Channel Router]
    TRACK[Feedback Tracker]
    REDIS[Redis Queue]
    
    PG --> XGB
    XGB --> AGENT
    AGENT --> RAG
    AGENT --> PROFILE
    AGENT --> MSG
    AGENT --> COMP
    AGENT --> ROUTER
    AGENT --> TRACK
    COMP -.-> MSG
    ROUTER --> REDIS
    
    style PG fill:#e3f2fd,stroke:#1565C0,stroke-width:3px
    style XGB fill:#fff3e0,stroke:#E65100,stroke-width:3px
    style AGENT fill:#f3e5f5,stroke:#6A1B9A,stroke-width:3px
    style RAG fill:#e8f5e9,stroke:#2E7D32,stroke-width:2px
    style PROFILE fill:#e8f5e9,stroke:#2E7D32,stroke-width:2px
    style MSG fill:#e8f5e9,stroke:#2E7D32,stroke-width:2px
    style COMP fill:#e8f5e9,stroke:#2E7D32,stroke-width:2px
    style ROUTER fill:#e8f5e9,stroke:#2E7D32,stroke-width:2px
    style TRACK fill:#e8f5e9,stroke:#2E7D32,stroke-width:2px
    style REDIS fill:#fce4ec,stroke:#AD1457,stroke-width:3px
```

### Agent Workflow Flow

```mermaid
graph LR
    A[RAG Lookup] --> B[Profile Fetcher]
    B --> C[Message Generator]
    C --> D{Compliance Check}
    D -->|Pass| E[Channel Router]
    D -->|Fail| C
    E --> F[Feedback Tracker]
    F --> G[Redis Queue]
    
    style A fill:#4CAF50,stroke:#1B5E20,stroke-width:3px
    style B fill:#2196F3,stroke:#0D47A1,stroke-width:3px
    style C fill:#FF9800,stroke:#E65100,stroke-width:3px
    style D fill:#9C27B0,stroke:#4A148C,stroke-width:3px
    style E fill:#00BCD4,stroke:#006064,stroke-width:3px
    style F fill:#795548,stroke:#3E2723,stroke-width:3px
    style G fill:#607D8B,stroke:#263238,stroke-width:3px
```

</div>

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **🌐 API Layer** | FastAPI | High-performance async API |
| **🤖 Agent Orchestration** | LangGraph | Stateful agent workflow management |
| **🧠 LLM** | OpenAI GPT-4o | Async message generation & reasoning |
| **📚 RAG** | ChromaDB + text-embedding-3-small | Vector-based knowledge retrieval |
| **🔍 Signal Detection** | XGBoost + rule-based fallback | Hybrid ML & rule engine |
| **💾 Database** | PostgreSQL (SQLAlchemy 2.0) | Transaction & customer data |
| **⚡ Event Queue** | Redis | Async message queue & caching |
| **🐳 Deployment** | Docker + docker-compose | Containerized deployment |

### Detected Life Events

| Event | Description | Recommended Products |
|-------|-------------|---------------------|
| 💼 **new_job** | Career transition | Salary accounts, credit cards |
| 💒 **marriage** | Marriage-related spending | Joint accounts, insurance |
| 🏠 **pre_retirement** | Retirement planning | Pension plans, fixed deposits |
| 👶 **child_birth** | New family member | Education savings, insurance |
| 🏢 **business_started** | Entrepreneurship | Business loans, current accounts |
| ❓ **none** | No clear signal | Generic engagement |

---

## 🛠️ Installation & Setup

<div align="center">

### Prerequisites

- 🐳 Docker & Docker Compose
- 🐍 Python 3.11+
- 🔑 OpenAI API Key (optional — fallback messages work without it)

</div>

### Step 1: Clone & Configure

```bash
# Clone the repository
git clone https://github.com/Harsimran-Dalal/lifesignal-sbi.git
cd lifesignal-sbi

# Copy environment template
cp .env.example .env

# Add your OpenAI API key (optional)
# OPENAI_API_KEY=sk-...
```

### Step 2: Start Infrastructure

```bash
# Spin up all services (PostgreSQL, Redis, FastAPI)
docker-compose up -d
```

This starts:
- 🗄️ **PostgreSQL** on port 5432
- ⚡ **Redis** on port 6379
- 🌐 **FastAPI** on http://localhost:8000

### Step 3: Install Python Dependencies (for local CLI demo)

```bash
pip install -r requirements.txt
```

### Environment Configuration

Ensure your `.env` file contains:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/lifesignal
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...  # Optional
```

---

## 🎮 Demo Usage

<div align="center">

### 🖥️ CLI Simulation (Recommended for Hackathon Demo)

```bash
python demo/simulate_event.py --customer_id 7
```

**Output includes:**
- 👤 Customer profile snapshot
- 🔍 XGBoost / rule-based signal detection results
- 🤖 Full agent trace (tool call order)
- 📱 Final WhatsApp message and product recommendation

**Try other customers:** `1`, `2`, `3`, … (20 of 100 have clear life-event patterns)

</div>

### 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + Redis queue depth |
| GET | `/customers` | List all mock customers |
| POST | `/trigger/{customer_id}` | Run signal detection + agent |
| GET | `/nudges` | Sent nudges with outcomes |

```bash
# Health check
curl http://localhost:8000/health

# List all customers
curl http://localhost:8000/customers

# Trigger signal detection for customer ID 7
curl -X POST http://localhost:8000/trigger/7

# View sent nudges
curl http://localhost:8000/nudges
```

---

## 📁 Project Structure

```
lifesignal-sbi/
├── 📄 main.py                    # FastAPI application entry point
├── 🐳 docker-compose.yml         # Multi-container orchestration
├── 📋 requirements.txt          # Python dependencies
│
├── 🤖 agents/
│   └── lifesignal_agent.py       # LangGraph StateGraph implementation
│
├── 🔧 tools/                     # Agent tools
│   ├── rag_lookup.py             # ChromaDB vector search
│   ├── profile_fetcher.py        # Customer profile retrieval
│   ├── message_generator.py      # GPT-4o message generation
│   └── compliance_checker.py     # Regulatory compliance validation
│
├── 🔍 signal_detection/          # ML-based signal detection
│   ├── xgboost_classifier.py     # XGBoost model
│   └── rule_engine.py            # Fallback rule-based detection
│
├── 💾 data/                      # Mock data & catalogs
│   ├── transactions.json         # Sample transaction data
│   └── sbi_products.json         # SBI product catalog
│
├── 📱 channel/
│   └── router.py                 # WhatsApp / YONO push routing
│
├── 📈 feedback/
│   └── tracker.py                # Nudge outcome logging
│
├── ⚡ event_queue/
│   └── redis_queue.py            # Redis-backed event queue
│
└── 🎬 demo/
    └── simulate_event.py         # End-to-end CLI demo
```

---

## 🔬 Technical Deep Dive

### Agent Workflow Details

The LangGraph agent executes the following sequence:

1. **📚 RAG Lookup** — Retrieves relevant product information from ChromaDB
2. **👤 Profile Fetcher** — Fetches customer profile and transaction history
3. **💬 Message Generator** — GPT-4o generates personalized message draft
4. **✅ Compliance Checker** — Validates message against regulatory rules
5. **🔄 Retry Loop** — If compliance fails, regenerate (max 2 attempts)
6. **📱 Channel Router** — Routes to WhatsApp or YONO based on preference
7. **📈 Feedback Tracker** — Logs nudge for outcome tracking

### Signal Detection Algorithm

**Hybrid Approach:**
- **Primary:** XGBoost classifier trained on transaction patterns
- **Fallback:** Rule-based engine for edge cases
- **Features:** Transaction frequency, amount patterns, merchant categories, temporal patterns

### Compliance & Safety

Outbound messages pass through a **rule-based compliance checker** that blocks:
- ❌ "guaranteed returns"
- ❌ "risk-free"
- ❌ "sure-shot profits"
- ❌ Other regulated phrases

Failed drafts are automatically regenerated up to **2 times** before the nudge is dropped.

---

## 🏆 Tech Stack Summary

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | FastAPI | 0.104.0 |
| **Python** | Python | 3.11 |
| **Agent Framework** | LangGraph | Latest |
| **LLM** | OpenAI GPT-4o | Async |
| **Embeddings** | text-embedding-3-small | OpenAI |
| **Vector Database** | ChromaDB | Latest |
| **ML Framework** | XGBoost + scikit-learn | Latest |
| **ORM** | SQLAlchemy | 2.0 |
| **Cache/Queue** | Redis | 7.x |
| **Database** | PostgreSQL | 16 |
| **Containerization** | Docker + docker-compose | Latest |

---

## 🤝 Contributing

This project was built for the **SBI Hackathon 2025**. For demo/prototype use only.

<div align="center">

---

**Built with ❤️ by Team Harsimran Singh Dalal & Sparsh Bhaskar**

**Thapar Institute of Engineering and Technology**

[![GitHub](https://img.shields.io/badge/GitHub-Harsimran--Dalal-blue.svg)](https://github.com/Harsimran-Dalal)

</div>
