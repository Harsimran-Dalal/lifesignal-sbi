"""Track nudge outcomes (opened / clicked / dismissed)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Nudge


class NudgeRecord(BaseModel):
    id: int
    customer_id: int
    detected_event: str
    recommended_product: str
    message: str
    channel: str
    compliance_pass: bool
    outcome: str
    created_at: datetime
    agent_trace: list[dict[str, Any]] = []


def log_nudge(
    customer_id: int,
    detected_event: str,
    recommended_product: str,
    message: str,
    channel: str,
    compliance_pass: bool,
    agent_trace: list[dict[str, Any]],
    outcome: str = "sent",
    db: Session | None = None,
) -> NudgeRecord:
    own_session = db is None
    session = db or SessionLocal()
    try:
        nudge = Nudge(
            customer_id=customer_id,
            detected_event=detected_event,
            recommended_product=recommended_product,
            message=message,
            channel=channel,
            compliance_pass=compliance_pass,
            outcome=outcome,
            agent_trace=agent_trace,
        )
        session.add(nudge)
        session.commit()
        session.refresh(nudge)
        return NudgeRecord.model_validate(nudge)
    finally:
        if own_session:
            session.close()


def list_nudges(limit: int = 50) -> list[NudgeRecord]:
    db = SessionLocal()
    try:
        rows = db.query(Nudge).order_by(Nudge.created_at.desc()).limit(limit).all()
        return [NudgeRecord.model_validate(r) for r in rows]
    finally:
        db.close()


def update_outcome(nudge_id: int, outcome: str) -> NudgeRecord | None:
    db = SessionLocal()
    try:
        nudge = db.query(Nudge).filter(Nudge.id == nudge_id).first()
        if not nudge:
            return None
        nudge.outcome = outcome
        db.commit()
        db.refresh(nudge)
        return NudgeRecord.model_validate(nudge)
    finally:
        db.close()
