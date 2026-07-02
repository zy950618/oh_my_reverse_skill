"""Optional FastAPI adapter scaffold for the local airline lab."""
from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception as exc:  # pragma: no cover - dependency is optional here.
    FastAPI = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


if FastAPI is not None:
    app = FastAPI(title="Airline Lab Order Flow", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "airline-lab-order-flow"}

    @app.get("/search")
    def search() -> dict[str, object]:
        return {
            "status": "ok",
            "session_id": "lab-session-001",
            "flights": [
                {
                    "flight_id": "LAB-MH-001",
                    "origin": "KUL",
                    "destination": "SIN",
                    "currency": "MYR",
                    "price": 120.0,
                }
            ],
        }
else:
    app = None


def dependency_status() -> dict[str, str]:
    if IMPORT_ERROR is None:
        return {"fastapi": "available"}
    return {"fastapi": "missing", "reason": str(IMPORT_ERROR)}

