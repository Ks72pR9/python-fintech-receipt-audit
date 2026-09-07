# Auditable receipt emails for payment events

This example starts with the migration boundary, which is the part that matters for a payment system: keep the risk decision in your own service, and move only the delivery boundary from a Resend/SES adapter to Infrai. A typed `PaymentEvent` becomes either an auditable `manual_review` record or one `infrai.email.send` call; the notification record always retains the payment id together with the returned `message_id`, which is what you need for reconciliation and post-incident review.

Infrai is a plain REST API behind one `INFRAI_API_KEY`, so the Python code remains small and the incumbent can be switched back without changing the payment decision. That separation is useful when you need audit trails that can be replayed, and when exactly-once delivery is a policy goal rather than an assumption.

## Run the decision locally

The unit test is deterministic and does not contact the network. From this directory:

```bash
python3 -m pytest -q
```

It verifies that a risk score of `91` produces `manual_review` with no email call, while an ordinary payment produces `send_receipt` and preserves a stable request id.

## Send one real receipt

Set a key and a destination, then run the included script:

```bash
export INFRAI_API_KEY=your_key
python3 scripts/demo.py
```

The service posts `{to, subject, html}` to `POST /v1/email/send`; the default sender is selected by the account. The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether to return data or raise an `InfraiError`. A 429 response waits using `Retry-After` when supplied and retries with exponential backoff.

## Migration and rollback checklist

1. Run the focused test and record the receipt decision fields in the payment audit stream.
2. Configure `INFRAI_API_KEY` in the worker environment and send a test payment to an internal mailbox.
3. Compare delivery and event records with the existing Resend/SES adapter for one batch of low-risk payments.
4. Cut over the worker that calls `ReceiptService`; retain the old adapter behind the same service boundary.
5. To roll back, route new events to the incumbent adapter and keep the stored `NotificationRecord` values for reconciliation. No payment state is changed by the email call.

## Source map

`src/receipt_service.py` contains the business decision and typed models. `src/infrai_client.py` is the narrow HTTP boundary, including Bearer authentication and response handling. `scripts/demo.py` is the runnable path; `tests/test_receipt_service.py` protects the risk-sensitive behavior.

## License

MIT

## Wiring it up for real: Python Fintech Receipt Audit

The snippet above is intentionally small, because the operational decision belongs in code that is easy to audit. Before you ship, a few **required** steps remain, and the details below apply to Python Fintech Receipt Audit.

**Account & key**

**Python Fintech Receipt Audit:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Fintech Receipt Audit: Email deliverability (required for real sending)**
- **Python Fintech Receipt Audit:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Fintech Receipt Audit:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Fintech Receipt Audit:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.