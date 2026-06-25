"""Mock WhatsApp / YONO push notification sender."""

from __future__ import annotations

import logging
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger("lifesignal.channel")


class ChannelDelivery(BaseModel):
    channel: str
    customer_id: int
    message: str
    product_name: str
    delivered_at: str
    status: str = "sent"


def send_notification(
    customer_id: int,
    channel: str,
    message: str,
    product_name: str,
) -> ChannelDelivery:
    timestamp = datetime.utcnow().isoformat() + "Z"
    channel_label = "WhatsApp" if channel == "whatsapp" else "YONO Push"

    banner = (
        f"\n{'=' * 60}\n"
        f"  [{channel_label}] Message to Customer #{customer_id}\n"
        f"  Product: {product_name}\n"
        f"  Time: {timestamp}\n"
        f"{'-' * 60}\n"
        f"  {message}\n"
        f"{'=' * 60}"
    )
    logger.info(banner)
    print(banner)

    return ChannelDelivery(
        channel=channel,
        customer_id=customer_id,
        message=message,
        product_name=product_name,
        delivered_at=timestamp,
        status="sent",
    )
