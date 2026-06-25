"""Fetch customer profile from PostgreSQL."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from database import SessionLocal
from models import Customer, TransactionSummary


class CustomerProfile(BaseModel):
    customer_id: int
    name: str
    age: int
    language: str = Field(description="Preferred language: en or hi")
    channel_preference: str = Field(description="whatsapp or push")
    product_holdings: list[str] = Field(default_factory=list)


def profile_fetcher(customer_id: int) -> CustomerProfile:
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        return CustomerProfile(
            customer_id=customer.id,
            name=customer.name,
            age=customer.age,
            language=customer.language,
            channel_preference=customer.channel_preference,
            product_holdings=customer.product_holdings or [],
        )
    finally:
        db.close()


def get_customer_transactions(customer_id: int) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(TransactionSummary)
            .filter(TransactionSummary.customer_id == customer_id)
            .order_by(TransactionSummary.month_index)
            .all()
        )
        return [
            {
                "month_index": r.month_index,
                "avg_credit": r.avg_credit,
                "salary_spike_ratio": r.salary_spike_ratio,
                "large_outgoing_count": r.large_outgoing_count,
                "medical_spend": r.medical_spend,
                "education_spend": r.education_spend,
                "business_spend": r.business_spend,
            }
            for r in rows
        ]
    finally:
        db.close()
