"""Domain workflow: decide whether a payment may trigger an emailed receipt."""

from dataclasses import dataclass
from typing import Any

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    customer_email: str
    amount_cents: int
    risk_score: int


@dataclass(frozen=True)
class NotificationRecord:
    payment_id: str
    decision: str
    message_id: str | None


class ReceiptService:
    # The domain call is intentionally named after the public idiom: infrai.email.send.
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def process(self, event: PaymentEvent) -> NotificationRecord:
        decision = "manual_review" if event.risk_score >= 80 else "send_receipt"
        if decision == "manual_review":
            return NotificationRecord(event.payment_id, decision, None)

        payload: dict[str, Any] = {
            "to": event.customer_email,
            "subject": f"Receipt for payment {event.payment_id}",
            "html": (
                f"<p>Payment <strong>{event.payment_id}</strong> received.</p>"
                f"<p>Amount: ${(event.amount_cents / 100):.2f}</p>"
            ),
        }
        data = self.client.email_send(payload, request_id=f"receipt-{event.payment_id}")
        return NotificationRecord(event.payment_id, decision, data.get("message_id"))
