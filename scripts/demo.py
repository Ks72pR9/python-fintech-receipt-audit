"""Run one payment decision against Infrai."""

from src.infrai_client import InfraiClient
from src.receipt_service import PaymentEvent, ReceiptService


def main() -> None:
    event = PaymentEvent(
        payment_id="pay_demo_1042",
        customer_email="chenhua@changba.com",
        amount_cents=2599,
        risk_score=12,
    )
    result = ReceiptService(InfraiClient()).process(event)
    print(result)


if __name__ == "__main__":
    main()
