from src.receipt_service import PaymentEvent, ReceiptService


class FakeClient:
    def __init__(self):
        self.calls = []

    def email_send(self, payload, request_id):
        self.calls.append((payload, request_id))
        return {"message_id": "msg_123"}


def test_high_risk_payment_is_held_without_email():
    client = FakeClient()
    result = ReceiptService(client).process(
        PaymentEvent("pay_7", "a@example.com", 1000, risk_score=91)
    )
    assert result.decision == "manual_review"
    assert result.message_id is None
    assert client.calls == []


def test_ordinary_payment_sends_a_receipt_with_stable_request_id():
    client = FakeClient()
    result = ReceiptService(client).process(
        PaymentEvent("pay_8", "a@example.com", 1000, risk_score=10)
    )
    assert result.decision == "send_receipt"
    assert result.message_id == "msg_123"
    assert client.calls[0][1] == "receipt-pay_8"
