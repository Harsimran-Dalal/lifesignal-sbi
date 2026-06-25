"""Generate synthetic customer transaction data and persist to PostgreSQL."""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy.orm import Session

from database import SessionLocal, init_db
from models import Customer, TransactionSummary

INDIAN_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Shaurya", "Atharv", "Advik", "Pranav", "Kabir", "Rudra",
    "Ananya", "Aadhya", "Diya", "Pari", "Anika", "Navya", "Sara", "Myra", "Aanya",
    "Kiara", "Ira", "Avni", "Riya", "Saanvi", "Priya", "Neha", "Kavita", "Sunita",
    "Rajesh", "Amit", "Suresh", "Ravi", "Deepak", "Manoj", "Vikram", "Rohit",
    "Harsimran", "Sparsh", "Daljit", "Harpreet", "Gurleen", "Simran", "Jaspreet",
]

INDIAN_LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Reddy", "Iyer",
    "Nair", "Das", "Chopra", "Malhotra", "Bhatia", "Kapoor", "Mehta", "Joshi",
    "Dalal", "Bhaskar", "Gill", "Kaur", "Chauhan", "Yadav", "Mishra", "Pandey",
]

PRODUCT_HOLDINGS_POOL = [
    "savings_account",
    "current_account",
    "fixed_deposit",
    "credit_card",
    "personal_loan",
    "home_loan",
    "mutual_fund",
    "insurance",
]

INJECTED_EVENTS = [
    "new_job",
    "marriage",
    "pre_retirement",
    "child_birth",
    "business_started",
]


def _random_name() -> str:
    return f"{random.choice(INDIAN_FIRST_NAMES)} {random.choice(INDIAN_LAST_NAMES)}"


def _base_monthly_features(age: int, holdings_count: int) -> dict[str, float | int]:
    base_salary = random.uniform(35000, 120000)
    return {
        "avg_credit": round(base_salary + random.uniform(-5000, 5000), 2),
        "salary_spike_ratio": round(random.uniform(0.95, 1.08), 3),
        "large_outgoing_count": random.randint(0, 2),
        "medical_spend": round(random.uniform(500, 3000), 2),
        "education_spend": round(random.uniform(0, 2000), 2),
        "business_spend": round(random.uniform(0, 1500), 2),
    }


def _inject_event_pattern(event: str, months: list[dict[str, Any]]) -> None:
    if event == "new_job":
        months[-2]["salary_spike_ratio"] = 1.45
        months[-2]["avg_credit"] = round(months[-3]["avg_credit"] * 1.45, 2)
        months[-1]["salary_spike_ratio"] = 1.42
        months[-1]["avg_credit"] = round(months[-3]["avg_credit"] * 1.42, 2)
    elif event == "marriage":
        for m in months[-2:]:
            m["large_outgoing_count"] = random.randint(8, 15)
            m["avg_credit"] = round(m["avg_credit"] * 0.7, 2)
    elif event == "pre_retirement":
        pass  # age handled at customer level
    elif event == "child_birth":
        months[-1]["medical_spend"] = round(random.uniform(15000, 40000), 2)
        months[-1]["education_spend"] = round(random.uniform(5000, 15000), 2)
    elif event == "business_started":
        for m in months[-3:]:
            m["business_spend"] = round(random.uniform(25000, 80000), 2)
            m["large_outgoing_count"] = random.randint(5, 12)


def generate_customer_record(
    customer_id: int,
    injected_event: str | None = None,
) -> dict[str, Any]:
    age = random.randint(58, 65) if injected_event == "pre_retirement" else random.randint(22, 55)
    language = random.choice(["en", "en", "en", "hi"])
    channel = random.choice(["whatsapp", "whatsapp", "push"])
    holdings = random.sample(PRODUCT_HOLDINGS_POOL, k=random.randint(1, 4))

    months: list[dict[str, Any]] = []
    for month_index in range(6):
        features = _base_monthly_features(age, len(holdings))
        features["month_index"] = month_index
        months.append(features)

    if injected_event:
        _inject_event_pattern(injected_event, months)

    return {
        "id": customer_id,
        "name": _random_name(),
        "age": age,
        "language": language,
        "channel_preference": channel,
        "product_holdings": holdings,
        "injected_event": injected_event,
        "transactions": months,
    }


def generate_all_customers(count: int = 100, signal_count: int = 20) -> list[dict[str, Any]]:
    random.seed(42)
    customers: list[dict[str, Any]] = []
    signal_indices = set(random.sample(range(1, count + 1), signal_count))
    signal_indices.add(7)  # demo customer always has an injected signal

    for i in range(1, count + 1):
        event = None
        if i in signal_indices:
            event = INJECTED_EVENTS[(i - 1) % len(INJECTED_EVENTS)]
        customers.append(generate_customer_record(i, injected_event=event))

    return customers


def save_customers_to_db(customers: list[dict[str, Any]], db: Session) -> None:
    db.query(TransactionSummary).delete()
    db.query(Customer).delete()
    db.commit()

    for record in customers:
        customer = Customer(
            id=record["id"],
            name=record["name"],
            age=record["age"],
            language=record["language"],
            channel_preference=record["channel_preference"],
            product_holdings=record["product_holdings"],
            injected_event=record.get("injected_event"),
        )
        db.add(customer)
        db.flush()

        for tx in record["transactions"]:
            db.add(
                TransactionSummary(
                    customer_id=customer.id,
                    month_index=tx["month_index"],
                    avg_credit=tx["avg_credit"],
                    salary_spike_ratio=tx["salary_spike_ratio"],
                    large_outgoing_count=tx["large_outgoing_count"],
                    medical_spend=tx["medical_spend"],
                    education_spend=tx["education_spend"],
                    business_spend=tx["business_spend"],
                )
            )

    db.commit()


def seed_database(force: bool = False) -> list[dict[str, Any]]:
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Customer).count()
        if existing >= 100 and not force:
            customers = []
            for c in db.query(Customer).order_by(Customer.id).all():
                txs = (
                    db.query(TransactionSummary)
                    .filter(TransactionSummary.customer_id == c.id)
                    .order_by(TransactionSummary.month_index)
                    .all()
                )
                customers.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "age": c.age,
                        "language": c.language,
                        "channel_preference": c.channel_preference,
                        "product_holdings": c.product_holdings,
                        "injected_event": c.injected_event,
                        "transactions": [
                            {
                                "month_index": t.month_index,
                                "avg_credit": t.avg_credit,
                                "salary_spike_ratio": t.salary_spike_ratio,
                                "large_outgoing_count": t.large_outgoing_count,
                                "medical_spend": t.medical_spend,
                                "education_spend": t.education_spend,
                                "business_spend": t.business_spend,
                            }
                            for t in txs
                        ],
                    }
                )
            return customers

        customers = generate_all_customers()
        save_customers_to_db(customers, db)
        return customers
    finally:
        db.close()


if __name__ == "__main__":
    data = seed_database(force=True)
    print(f"Seeded {len(data)} customers to PostgreSQL")
