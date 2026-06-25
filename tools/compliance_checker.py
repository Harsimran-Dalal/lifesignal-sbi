"""Rule-based compliance checker for outbound nudges."""

from __future__ import annotations

import re

from pydantic import BaseModel

BANNED_PHRASES = [
    "guaranteed returns",
    "guaranteed return",
    "risk-free",
    "risk free",
    "assured profit",
    "100% safe",
    "no risk",
    "double your money",
    "sure shot",
    "fixed profit",
]


class ComplianceResult(BaseModel):
    passed: bool
    violations: list[str]
    feedback: str | None = None


def compliance_checker(message: str) -> ComplianceResult:
    lower = message.lower()
    violations: list[str] = []

    for phrase in BANNED_PHRASES:
        if phrase in lower:
            violations.append(phrase)

    if re.search(r"\b100\s*%\s*(safe|profit|return)", lower):
        violations.append("100% claim")

    if violations:
        return ComplianceResult(
            passed=False,
            violations=violations,
            feedback=f"Remove or rephrase banned terms: {', '.join(violations)}",
        )

    if len(message.strip()) < 20:
        return ComplianceResult(
            passed=False,
            violations=["too_short"],
            feedback="Message is too short. Write 2 complete sentences.",
        )

    return ComplianceResult(passed=True, violations=[])
