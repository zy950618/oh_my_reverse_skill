#!/usr/bin/env python3
"""Local-only example client for the airline lab mock server."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:18991"


def get_json(path: str) -> dict:
    with urlopen(BASE_URL + path, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = Request(BASE_URL + path, data=data, headers={"content-type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    search = get_json("/api/search?origin=KUL&destination=SIN&date=2026-08-01")
    detail = post_json("/api/detail", {"session_id": search["session_id"], "flight_id": search["flights"][0]["flight_id"]})
    order = post_json(
        "/api/order",
        {
            "session_id": detail["session_id"],
            "flight_id": detail["flight"]["flight_id"],
            "detail_nonce": detail["detail_nonce"],
        },
    )
    print(json.dumps({"search": search, "detail": detail, "order": order}, indent=2))


if __name__ == "__main__":
    main()

