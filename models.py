from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

LIFE_EVENTS = [
    "new_job",
    "marriage",
    "pre_retirement",
    "child_birth",
    "business_started",
    "none",
]


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    channel_preference: Mapped[str] = mapped_column(String(20), default="whatsapp")
    product_holdings: Mapped[list] = mapped_column(JSON, default=list)
    injected_event: Mapped[str | None] = mapped_column(String(30), nullable=True)

    transactions: Mapped[list["TransactionSummary"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    nudges: Mapped[list["Nudge"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class TransactionSummary(Base):
    __tablename__ = "transaction_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    month_index: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_credit: Mapped[float] = mapped_column(Float, nullable=False)
    salary_spike_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    large_outgoing_count: Mapped[int] = mapped_column(Integer, default=0)
    medical_spend: Mapped[float] = mapped_column(Float, default=0.0)
    education_spend: Mapped[float] = mapped_column(Float, default=0.0)
    business_spend: Mapped[float] = mapped_column(Float, default=0.0)

    customer: Mapped["Customer"] = relationship(back_populates="transactions")


class Nudge(Base):
    __tablename__ = "nudges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    detected_event: Mapped[str] = mapped_column(String(30), nullable=False)
    recommended_product: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    compliance_pass: Mapped[bool] = mapped_column(default=True)
    outcome: Mapped[str] = mapped_column(String(20), default="sent")
    agent_trace: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="nudges")
