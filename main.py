"""FastAPI entry point for LifeSignal."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.lifesignal_agent import run_lifesignal_agent
from data.mock_transactions import seed_database
from database import get_db, init_db
from feedback.tracker import list_nudges
from models import Customer, TransactionSummary
from event_queue.redis_queue import queue_length
from signal_detection.event_classifier import get_classifier
from tools.profile_fetcher import get_customer_transactions
from tools.rag_lookup import ingest_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lifesignal")


class CustomerSummary(BaseModel):
    id: int
    name: str
    age: int
    language: str
    channel_preference: str
    product_holdings: list[str]
    injected_event: str | None = None


class TriggerResponse(BaseModel):
    customer_id: int
    detected_event: str
    detection_method: str
    confidence: float
    recommended_product: str | None
    message: str | None
    channel: str | None
    delivery_status: str | None
    agent_trace: list[dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LifeSignal...")
    init_db()
    seed_database()
    ingest_products()
    get_classifier()
    logger.info("LifeSignal ready — DB seeded, RAG ingested, classifier trained")
    yield


app = FastAPI(
    title="LifeSignal",
    description="Proactive Agentic AI for Life-Event-Driven Banking Engagement",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "LifeSignal",
        "redis_queue_depth": queue_length(),
    }


@app.get("/customers", response_model=list[CustomerSummary])
async def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.id).all()
    return [
        CustomerSummary(
            id=c.id,
            name=c.name,
            age=c.age,
            language=c.language,
            channel_preference=c.channel_preference,
            product_holdings=c.product_holdings or [],
            injected_event=c.injected_event,
        )
        for c in customers
    ]


@app.get("/nudges")
async def get_nudges():
    return [n.model_dump() for n in list_nudges()]


@app.post("/trigger/{customer_id}", response_model=TriggerResponse)
async def trigger_agent(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    transactions = get_customer_transactions(customer_id)
    classifier = get_classifier()
    detection = classifier.predict(
        transactions=transactions,
        age=customer.age,
        product_holdings=customer.product_holdings or [],
    )

    if detection.event == "none":
        return TriggerResponse(
            customer_id=customer_id,
            detected_event="none",
            detection_method=detection.method,
            confidence=detection.confidence,
            recommended_product=None,
            message=None,
            channel=None,
            delivery_status="skipped_no_signal",
            agent_trace=[{"step": "signal_detection", "detail": "No life event detected"}],
        )

    result = await run_lifesignal_agent(customer_id, detection.event)
    product = result.get("recommended_product") or {}

    return TriggerResponse(
        customer_id=customer_id,
        detected_event=detection.event,
        detection_method=detection.method,
        confidence=detection.confidence,
        recommended_product=product.get("name"),
        message=result.get("message_draft"),
        channel=result.get("channel"),
        delivery_status=result.get("delivery_status"),
        agent_trace=result.get("agent_trace", []),
    )
