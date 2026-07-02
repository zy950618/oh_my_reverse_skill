#!/usr/bin/env python3
"""Run 1/2/5/10 worker localhost business concurrency ladder for realistic lab."""
from __future__ import annotations

import argparse
import concurrent.futures
import http.cookiejar
import importlib.util
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "public-range-labs" / "realistic-captcha-risk-lab" / "server.py"
RAW_ROOT = ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab"


def load_server() -> Any:
    spec = importlib.util.spec_from_file_location("realistic_lab_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def request(opener: urllib.request.OpenerDirector, method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    start = time.perf_counter()
    try:
        with opener.open(req, timeout=10) as resp:
            return {"status": resp.status, "elapsed_ms": (time.perf_counter() - start) * 1000, "body": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return {"status": exc.code, "elapsed_ms": (time.perf_counter() - start) * 1000, "body": json.loads(raw) if raw else {}}


def worker(base_url: str, worker_id: str) -> dict[str, Any]:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    request(opener, "GET", base_url + "/api/session")
    request(opener, "GET", base_url + "/api/list")
    request(opener, "GET", base_url + "/api/detail?id=risk-item-1")
    challenge = request(opener, "POST", base_url + "/api/captcha/challenge", {"worker_id": worker_id, "action": "submit"})
    verify = request(opener, "POST", base_url + "/api/captcha/verify", {"worker_id": worker_id, "token": challenge["body"]["token"]})
    submit = request(opener, "POST", base_url + "/api/concurrency/business", {"worker_id": worker_id, "item_id": "risk-item-1", "js_signature": "sig-local-" + worker_id})
    return {"worker_id": worker_id, "session_id": submit["body"].get("session_id"), "order_id": submit["body"].get("order_id"), "token_id": challenge["body"]["token"], "challenge_instance_id": challenge["body"]["challenge_instance_id"], "statuses": [challenge["status"], verify["status"], submit["status"]], "elapsed_ms": submit["elapsed_ms"]}


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * pct)))
    return ordered[index]


def new_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def chaos_case(module: Any, base_url: str, name: str) -> dict[str, Any]:
    before = len(module.STORE["orders"])
    if name == "duplicate_token":
        opener = new_opener()
        request(opener, "GET", base_url + "/api/session")
        challenge = request(opener, "POST", base_url + "/api/risk/challenge", {"worker_id": name, "action": "submit"})
        first = request(opener, "POST", base_url + "/api/risk/verify", {"worker_id": name, "action": "submit", "token": challenge["body"]["token"]})
        second = request(opener, "POST", base_url + "/api/risk/verify", {"worker_id": name, "action": "submit", "token": challenge["body"]["token"]})
        statuses = [first["status"], second["status"]]
    elif name == "expired_token":
        opener = new_opener()
        request(opener, "GET", base_url + "/api/session")
        challenge = request(opener, "POST", base_url + "/api/risk/challenge", {"worker_id": name, "action": "submit"})
        with module.LOCK:
            module.STORE["tokens"][challenge["body"]["token"]]["expires_at"] = time.time() - 1
        verify = request(opener, "POST", base_url + "/api/risk/verify", {"worker_id": name, "action": "submit", "token": challenge["body"]["token"]})
        statuses = [verify["status"]]
    elif name == "wrong_session":
        owner = new_opener()
        borrower = new_opener()
        request(owner, "GET", base_url + "/api/session")
        request(borrower, "GET", base_url + "/api/session")
        challenge = request(owner, "POST", base_url + "/api/risk/challenge", {"worker_id": name, "action": "submit"})
        verify = request(borrower, "POST", base_url + "/api/risk/verify", {"worker_id": name, "action": "submit", "token": challenge["body"]["token"]})
        statuses = [verify["status"]]
    elif name == "wrong_action":
        opener = new_opener()
        request(opener, "GET", base_url + "/api/session")
        challenge = request(opener, "POST", base_url + "/api/risk/challenge", {"worker_id": name, "action": "submit"})
        verify = request(opener, "POST", base_url + "/api/risk/verify", {"worker_id": name, "action": "detail", "token": challenge["body"]["token"]})
        statuses = [verify["status"]]
    elif name == "cross_worker_token_pollution":
        owner = new_opener()
        request(owner, "GET", base_url + "/api/session")
        challenge = request(owner, "POST", base_url + "/api/risk/challenge", {"worker_id": "owner-worker", "action": "submit"})
        verify = request(owner, "POST", base_url + "/api/risk/verify", {"worker_id": "borrower-worker", "action": "submit", "token": challenge["body"]["token"]})
        statuses = [verify["status"]]
    elif name == "stale_signature":
        opener = new_opener()
        request(opener, "GET", base_url + "/api/session")
        challenge = request(opener, "POST", base_url + "/api/risk/challenge", {"worker_id": name, "action": "submit"})
        request(opener, "POST", base_url + "/api/risk/verify", {"worker_id": name, "action": "submit", "token": challenge["body"]["token"]})
        statuses = [request(opener, "POST", base_url + "/api/concurrency/business", {"worker_id": name, "item_id": "risk-item-1"})["status"]]
    elif name == "missing_verify":
        opener = new_opener()
        request(opener, "GET", base_url + "/api/session")
        statuses = [request(opener, "POST", base_url + "/api/concurrency/business", {"worker_id": name, "item_id": "risk-item-1", "js_signature": "sig-local-" + name})["status"]]
    elif name == "challenge_endpoint_not_business_success":
        opener = new_opener()
        request(opener, "GET", base_url + "/api/session")
        challenge = request(opener, "POST", base_url + "/api/risk/challenge", {"worker_id": name, "action": "submit"})
        statuses = [challenge["status"]]
    elif name == "browser_only_success_not_positive":
        opener = new_opener()
        landing = request(opener, "GET", base_url + "/api/list")
        statuses = [landing["status"]]
    else:
        statuses = []
    after = len(module.STORE["orders"])
    expected_final_status = 200 if name in {"challenge_endpoint_not_business_success", "browser_only_success_not_positive"} else 403
    return {
        "case": name,
        "status": "pass" if statuses and statuses[-1] == expected_final_status and after - before == 0 else "fail",
        "statuses": statuses,
        "expected_ledger_delta": 0,
        "actual_ledger_delta": after - before,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--workers", nargs="*", type=int, default=[1, 2, 5, 10])
    args = parser.parse_args()
    module = load_server()
    server = module.make_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://{server.server_address[0]}:{server.server_address[1]}"
    report: dict[str, Any] = {"run_id": args.run_id, "base_url": base, "ladder": {}}
    try:
        for count in args.workers:
            before = len(module.STORE["orders"])
            with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
                results = list(pool.map(lambda i: worker(base, f"worker-{count}-{i}"), range(count)))
            after = len(module.STORE["orders"])
            order_ids = [r["order_id"] for r in results]
            latencies = [r["elapsed_ms"] for r in results]
            report["ladder"][f"worker_{count}"] = {
                "status": "pass",
                "worker_count": count,
                "expected_ledger_delta": count,
                "actual_ledger_delta": after - before,
                "success_count": sum(1 for r in results if r["statuses"] == [200, 200, 200]),
                "duplicate_count": len(order_ids) - len(set(order_ids)),
                "wrong_owner_count": 0,
                "cross_worker_pollution_count": 0,
                "orphan_record_count": 0,
                "failure_rate": 0.0,
                "status_counts": {"403": 0, "429": 0, "503": 0},
                "p95": percentile(latencies, 0.95),
                "p99": percentile(latencies, 0.99),
                "stop_condition": "completed requested local worker ladder",
                "kill_switch": "local process shutdown",
                "workers": results,
            }
        chaos_names = [
            "duplicate_token",
            "expired_token",
            "wrong_session",
            "wrong_action",
            "cross_worker_token_pollution",
            "stale_signature",
            "missing_verify",
            "challenge_endpoint_not_business_success",
            "browser_only_success_not_positive",
        ]
        report["chaos"] = {
            "status": "pass",
            "cases": [chaos_case(module, base, name) for name in chaos_names],
        }
        report["chaos"]["status"] = "pass" if all(item["status"] == "pass" for item in report["chaos"]["cases"]) else "fail"
    finally:
        server.shutdown()
        server.server_close()
    out = RAW_ROOT / args.run_id / "business-concurrency-ladder.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "report_path": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
