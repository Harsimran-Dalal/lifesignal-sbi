"""LangGraph agentic loop for LifeSignal proactive nudges."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from channel.router import send_notification
from feedback.tracker import log_nudge
from event_queue.redis_queue import enqueue_event
from tools.compliance_checker import compliance_checker
from tools.message_generator import message_generator
from tools.profile_fetcher import profile_fetcher
from tools.rag_lookup import rag_lookup

MAX_COMPLIANCE_RETRIES = 2


class AgentState(TypedDict):
    customer_id: int
    detected_event: str
    customer_profile: dict[str, Any] | None
    recommended_products: list[dict[str, Any]]
    recommended_product: dict[str, Any] | None
    message_draft: str | None
    compliance_pass: bool
    compliance_feedback: str | None
    compliance_retries: int
    channel: str | None
    agent_trace: Annotated[list[dict[str, Any]], operator.add]
    delivery_status: str | None
    nudge_id: int | None


def _trace(step: str, detail: str, data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    entry: dict[str, Any] = {"step": step, "detail": detail}
    if data:
        entry["data"] = data
    return [entry]


async def node_rag_lookup(state: AgentState) -> dict[str, Any]:
    event = state["detected_event"]
    products = rag_lookup(event, top_k=2)
    best = products[0] if products else {
        "name": "SBI Savings Plus",
        "description": "General purpose banking product",
        "key_benefits": ["Flexible banking", "YONO access"],
        "cta_link": "https://sbi.co.in",
        "target_life_event": event,
    }
    return {
        "recommended_products": products,
        "recommended_product": best,
        "agent_trace": _trace(
            "rag_lookup",
            f"Found {len(products)} products for event '{event}'",
            {"top_product": best.get("name"), "all_products": [p["name"] for p in products]},
        ),
    }


async def node_profile_fetcher(state: AgentState) -> dict[str, Any]:
    profile = profile_fetcher(state["customer_id"])
    profile_dict = profile.model_dump()
    return {
        "customer_profile": profile_dict,
        "channel": profile.channel_preference,
        "agent_trace": _trace(
            "profile_fetcher",
            f"Loaded profile for {profile.name}",
            profile_dict,
        ),
    }


async def node_message_generator(state: AgentState) -> dict[str, Any]:
    profile = state["customer_profile"] or {}
    product = state["recommended_product"] or {}
    draft = await message_generator(
        customer_name=profile.get("name", "Customer"),
        life_event=state["detected_event"],
        product_name=product.get("name", "SBI Product"),
        product_benefits=product.get("key_benefits", []),
        language=profile.get("language", "en"),
        compliance_feedback=state.get("compliance_feedback"),
    )
    return {
        "message_draft": draft.message,
        "agent_trace": _trace(
            "message_generator",
            f"Generated {draft.language} message draft",
            {"message": draft.message},
        ),
    }


async def node_compliance_checker(state: AgentState) -> dict[str, Any]:
    message = state.get("message_draft") or ""
    result = compliance_checker(message)
    retries = state.get("compliance_retries", 0)
    if not result.passed:
        retries += 1
    return {
        "compliance_pass": result.passed,
        "compliance_feedback": result.feedback,
        "compliance_retries": retries,
        "agent_trace": _trace(
            "compliance_checker",
            "PASS" if result.passed else f"FAIL — {result.feedback}",
            {"violations": result.violations},
        ),
    }


def route_after_compliance(state: AgentState) -> Literal["channel_router", "message_generator", "end_failed"]:
    if state.get("compliance_pass"):
        return "channel_router"
    if state.get("compliance_retries", 0) <= MAX_COMPLIANCE_RETRIES:
        return "message_generator"
    return "end_failed"


async def node_channel_router(state: AgentState) -> dict[str, Any]:
    profile = state.get("customer_profile") or {}
    product = state.get("recommended_product") or {}
    channel = state.get("channel") or profile.get("channel_preference", "whatsapp")
    message = state.get("message_draft") or ""

    delivery = send_notification(
        customer_id=state["customer_id"],
        channel=channel,
        message=message,
        product_name=product.get("name", "SBI Product"),
    )

    nudge = log_nudge(
        customer_id=state["customer_id"],
        detected_event=state["detected_event"],
        recommended_product=product.get("name", "SBI Product"),
        message=message,
        channel=channel,
        compliance_pass=True,
        agent_trace=state.get("agent_trace", []),
    )

    enqueue_event(
        state["customer_id"],
        state["detected_event"],
        {"nudge_id": nudge.id, "product": product.get("name")},
    )

    return {
        "delivery_status": delivery.status,
        "nudge_id": nudge.id,
        "agent_trace": _trace(
            "channel_router",
            f"Delivered via {channel} — nudge #{nudge.id} logged",
            delivery.model_dump(),
        ),
    }


async def node_end_failed(state: AgentState) -> dict[str, Any]:
    return {
        "delivery_status": "failed_compliance",
        "agent_trace": _trace(
            "end_failed",
            "Max compliance retries exceeded — nudge not sent",
        ),
    }


def build_lifesignal_graph():
    graph = StateGraph(AgentState)

    graph.add_node("rag_lookup", node_rag_lookup)
    graph.add_node("profile_fetcher", node_profile_fetcher)
    graph.add_node("message_generator", node_message_generator)
    graph.add_node("compliance_checker", node_compliance_checker)
    graph.add_node("channel_router", node_channel_router)
    graph.add_node("end_failed", node_end_failed)

    graph.set_entry_point("rag_lookup")
    graph.add_edge("rag_lookup", "profile_fetcher")
    graph.add_edge("profile_fetcher", "message_generator")
    graph.add_edge("message_generator", "compliance_checker")
    graph.add_conditional_edges(
        "compliance_checker",
        route_after_compliance,
        {
            "channel_router": "channel_router",
            "message_generator": "message_generator",
            "end_failed": "end_failed",
        },
    )
    graph.add_edge("channel_router", END)
    graph.add_edge("end_failed", END)

    return graph.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_lifesignal_graph()
    return _agent


async def run_lifesignal_agent(customer_id: int, detected_event: str) -> AgentState:
    agent = get_agent()
    initial_state: AgentState = {
        "customer_id": customer_id,
        "detected_event": detected_event,
        "customer_profile": None,
        "recommended_products": [],
        "recommended_product": None,
        "message_draft": None,
        "compliance_pass": False,
        "compliance_feedback": None,
        "compliance_retries": 0,
        "channel": None,
        "agent_trace": [],
        "delivery_status": None,
        "nudge_id": None,
    }
    result = await agent.ainvoke(initial_state)
    return result
