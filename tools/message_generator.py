"""Generate personalized WhatsApp/push messages via GPT-4o."""

from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel

from config import settings

LANGUAGE_LABELS = {"en": "English", "hi": "Hindi"}


class MessageDraft(BaseModel):
    message: str
    language: str


async def message_generator(
    customer_name: str,
    life_event: str,
    product_name: str,
    product_benefits: list[str],
    language: str,
    compliance_feedback: str | None = None,
) -> MessageDraft:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    lang_label = LANGUAGE_LABELS.get(language, "English")
    benefits_text = ", ".join(product_benefits[:3])

    system_prompt = (
        "You are a warm, helpful SBI banking assistant writing proactive customer nudges. "
        "Write exactly 2 sentences. Be personal, respectful, and concise. "
        "Do NOT use banned phrases: guaranteed returns, risk-free, assured profit, "
        "100% safe, no risk, double your money. "
        f"Write in {lang_label}."
    )

    user_prompt = (
        f"Customer: {customer_name}\n"
        f"Detected life event: {life_event.replace('_', ' ')}\n"
        f"Recommended product: {product_name}\n"
        f"Key benefits: {benefits_text}\n"
        "Write a 2-sentence WhatsApp message introducing the product naturally."
    )

    if compliance_feedback:
        user_prompt += f"\n\nPrevious draft failed compliance: {compliance_feedback}. Rewrite avoiding banned terms."

    if not settings.openai_api_key:
        fallback = _fallback_message(customer_name, product_name, language)
        return MessageDraft(message=fallback, language=language)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=200,
    )

    content = response.choices[0].message.content or _fallback_message(
        customer_name, product_name, language
    )
    return MessageDraft(message=content.strip(), language=language)


def _fallback_message(name: str, product: str, language: str) -> str:
    if language == "hi":
        return (
            f"नमस्ते {name}, हमने आपकी हाल की जरूरतों को देखते हुए {product} "
            f"आपके लिए उपयुक्त हो सकता है। YONO ऐप पर विवरण देखें।"
        )
    return (
        f"Hi {name}, based on recent changes in your banking activity, "
        f"{product} could be a great fit for you. Explore details on the YONO app."
    )
