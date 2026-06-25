"""XGBoost life-event signal detector with rule-based fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder

from models import LIFE_EVENTS

FEATURE_NAMES = [
    "avg_credit",
    "salary_spike_ratio",
    "large_outgoing_count",
    "age",
    "product_holdings_count",
    "medical_spend",
    "education_spend",
    "business_spend",
]


@dataclass
class DetectionResult:
    event: str
    confidence: float
    method: str
    features: dict[str, float | int]


class EventClassifier:
    def __init__(self) -> None:
        self.model: xgb.XGBClassifier | None = None
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(LIFE_EVENTS)
        self._train()

    def _synthetic_training_rows(self) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(42)
        rows: list[list[float]] = []
        labels: list[str] = []

        for _ in range(200):
            rows.append([
                rng.uniform(30000, 80000),
                rng.uniform(0.9, 1.1),
                rng.integers(0, 3),
                rng.integers(25, 50),
                rng.integers(1, 4),
                rng.uniform(500, 3000),
                rng.uniform(0, 2000),
                rng.uniform(0, 1500),
            ])
            labels.append("none")

        patterns = {
            "new_job": lambda: [
                95000, 1.45, 1, 32, 2, 1200, 800, 500,
            ],
            "marriage": lambda: [
                45000, 1.0, 12, 28, 3, 2000, 1500, 800,
            ],
            "pre_retirement": lambda: [
                70000, 1.02, 1, 61, 4, 2500, 1000, 600,
            ],
            "child_birth": lambda: [
                55000, 1.05, 2, 30, 2, 28000, 12000, 700,
            ],
            "business_started": lambda: [
                60000, 1.08, 8, 35, 2, 1500, 900, 55000,
            ],
        }

        for event, fn in patterns.items():
            for _ in range(80):
                base = fn()
                noisy = [b * rng.uniform(0.92, 1.08) if isinstance(b, float) else b for b in base]
                rows.append(noisy)
                labels.append(event)

        return np.array(rows, dtype=np.float32), np.array(labels)

    def _train(self) -> None:
        x, y = self._synthetic_training_rows()
        y_encoded = self.label_encoder.transform(y)
        self.model = xgb.XGBClassifier(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            eval_metric="mlogloss",
        )
        self.model.fit(x, y_encoded)

    def extract_features(
        self,
        transactions: list[dict[str, Any]],
        age: int,
        product_holdings: list[str],
    ) -> dict[str, float | int]:
        if not transactions:
            return {name: 0 for name in FEATURE_NAMES}

        recent = transactions[-1]
        avg_credit = float(np.mean([t["avg_credit"] for t in transactions]))
        return {
            "avg_credit": round(avg_credit, 2),
            "salary_spike_ratio": float(recent.get("salary_spike_ratio", 1.0)),
            "large_outgoing_count": int(recent.get("large_outgoing_count", 0)),
            "age": age,
            "product_holdings_count": len(product_holdings),
            "medical_spend": float(recent.get("medical_spend", 0)),
            "education_spend": float(recent.get("education_spend", 0)),
            "business_spend": float(recent.get("business_spend", 0)),
        }

    def rule_based_fallback(self, transactions: list[dict[str, Any]], age: int) -> str | None:
        if len(transactions) >= 3:
            last_two = transactions[-2:]
            if all(t.get("salary_spike_ratio", 1.0) >= 1.4 for t in last_two):
                return "new_job"

        if age >= 58:
            return "pre_retirement"

        recent = transactions[-1] if transactions else {}
        if recent.get("large_outgoing_count", 0) >= 8:
            return "marriage"
        if recent.get("medical_spend", 0) >= 15000:
            return "child_birth"
        if recent.get("business_spend", 0) >= 25000:
            return "business_started"

        return None

    def predict(
        self,
        transactions: list[dict[str, Any]],
        age: int,
        product_holdings: list[str],
    ) -> DetectionResult:
        features = self.extract_features(transactions, age, product_holdings)
        feature_vector = np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float32)

        rule_event = self.rule_based_fallback(transactions, age)
        if rule_event:
            return DetectionResult(
                event=rule_event,
                confidence=0.95,
                method="rule_based",
                features=features,
            )

        assert self.model is not None
        proba = self.model.predict_proba(feature_vector)[0]
        pred_idx = int(np.argmax(proba))
        event = self.label_encoder.inverse_transform([pred_idx])[0]
        confidence = float(proba[pred_idx])

        return DetectionResult(
            event=event,
            confidence=confidence,
            method="xgboost",
            features=features,
        )


_classifier: EventClassifier | None = None


def get_classifier() -> EventClassifier:
    global _classifier
    if _classifier is None:
        _classifier = EventClassifier()
    return _classifier
