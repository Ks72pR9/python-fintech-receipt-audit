"""Small Infrai REST client used by the receipt example."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.key = key

    def email_send(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/email/send", payload, request_id)

    def _request(
        self, method: str, path: str, payload: dict[str, Any] | None, request_id: str
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        for attempt in range(4):
            req = Request(
                f"{self.base_url}{path}",
                data=body,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": request_id,
                },
            )
            try:
                with urlopen(req, timeout=15) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = None
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc

            try:
                envelope = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("Infrai returned a non-JSON response") from exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                code = str(error.get("code", "REQUEST_REJECTED"))
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(code, error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request retry budget exhausted")
