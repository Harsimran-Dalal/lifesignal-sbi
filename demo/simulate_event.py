#!/usr/bin/env python3
"""CLI demo: simulate a life-event signal end-to-end for a customer."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from agents.lifesignal_agent import run_lifesignal_agent
from data.mock_transactions import seed_database
from database import SessionLocal, init_db
from models import Customer
from signal_detection.event_classifier import get_classifier
from tools.profile_fetcher import get_customer_transactions
from tools.rag_lookup import ingest_products


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_trace(trace: list[dict]) -> None:
    print_header("AGENT TRACE")
    for i, step in enumerate(trace, 1):
        print(f"\n  [{i}] {step.get('step', 'unknown').upper()}")
        print(f"      {step.get('detail', '')}")
        if step.get("data"):
            data = step["data"]
            if isinstance(data, dict) and "message" in data:
                print(f"      Message preview: {data['message'][:120]}...")
            elif isinstance(data, dict) and "top_product" in data:
                print(f"      Top product: {data['top_product']}")
                print(f"      All matches: {data.get('all_products', [])}")


async def simulate(customer_id: int) -> None:
    print_header("LifeSignal — End-to-End Demo")
    print("  Initializing database, RAG, and classifier...")

    init_db()
    seed_database()
    ingest_products()
    get_classifier()

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            print(f"\n  ERROR: Customer #{customer_id} not found.")
            print("  Available customers: 1–100")
            sys.exit(1)

        print_header(f"CUSTOMER #{customer_id}")
        print(f"  Name:     {customer.name}")
        print(f"  Age:      {customer.age}")
        print(f"  Language: {customer.language}")
        print(f"  Channel:  {customer.channel_preference}")
        print(f"  Holdings: {', '.join(customer.product_holdings or [])}")
        if customer.injected_event:
            print(f"  Injected signal (ground truth): {customer.injected_event}")

        transactions = get_customer_transactions(customer_id)
        classifier = get_classifier()
        detection = classifier.predict(
            transactions=transactions,
            age=customer.age,
            product_holdings=customer.product_holdings or [],
        )

        print_header("SIGNAL DETECTION")
        print(f"  Detected event:  {detection.event}")
        print(f"  Method:          {detection.method}")
        print(f"  Confidence:      {detection.confidence:.2%}")
        print(f"  Features:        {detection.features}")

        if detection.event == "none":
            print("\n  No life event detected — agent not triggered.")
            return

        print_header("LANGGRAPH AGENT")
        print("  Running agentic loop: rag_lookup → profile_fetcher →")
        print("  message_generator → compliance_checker → channel_router")

        result = await run_lifesignal_agent(customer_id, detection.event)
        print_trace(result.get("agent_trace", []))

        product = result.get("recommended_product") or {}
        print_header("FINAL OUTPUT")
        print(f"  Event:    {detection.event}")
        print(f"  Product:  {product.get('name', 'N/A')}")
        print(f"  Channel:  {result.get('channel', 'N/A')}")
        print(f"  Status:   {result.get('delivery_status', 'N/A')}")
        print(f"\n  Message:\n  {result.get('message_draft', '')}")
        print(f"\n{'=' * 60}\n")

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate LifeSignal for a customer")
    parser.add_argument("--customer_id", type=int, default=7, help="Customer ID (1-100)")
    args = parser.parse_args()
    asyncio.run(simulate(args.customer_id))


if __name__ == "__main__":
    main()
