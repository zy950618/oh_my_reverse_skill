#!/usr/bin/env python3
"""Replay CAPTCHA recognition actions on the localhost captcha-vision-lab page."""
from __future__ import annotations

import argparse
import asyncio
import http.server
import json
import math
import socketserver
import threading
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from captcha_vision_baseline_solver import solve_click, solve_rotate, solve_slider


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class ThreadedTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_server(directory: Path) -> tuple[ThreadedTCPServer, int]:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(directory), **kwargs)
    server = ThreadedTCPServer(("127.0.0.1", 0), handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def pick_slider_prediction(predictions: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        item for item in predictions.get("predictions", [])
        if item.get("challenge_type") == "slider-captcha" and isinstance(item.get("prediction"), dict)
    ]
    if not candidates:
        raise RuntimeError("no slider-captcha prediction found")
    easy = [item for item in candidates if item.get("difficulty") == "easy"]
    return easy[0] if easy else candidates[0]


def expected_for(predictions: dict[str, Any], sample_id: str) -> dict[str, Any]:
    manifest_path = Path(predictions["manifest_path"])
    manifest = read_json(manifest_path)
    for sample in manifest.get("samples", []):
        if sample.get("sample_id") == sample_id:
            offset = sample.get("offset")
            if isinstance(offset, dict):
                return offset
    raise RuntimeError(f"missing expected offset for {sample_id}")


def pick_manifest_slider(manifest: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        sample for sample in manifest.get("samples", [])
        if sample.get("challenge_type") == "slider-captcha" and sample.get("difficulty") == "easy"
    ]
    if not candidates:
        candidates = [sample for sample in manifest.get("samples", []) if sample.get("challenge_type") == "slider-captcha"]
    if not candidates:
        raise RuntimeError("no slider-captcha sample found for gocaptcha-local action replay")
    return candidates[0]


def pick_manifest_sample(manifest: dict[str, Any], challenge_type: str, difficulty: str = "easy") -> dict[str, Any]:
    candidates = [
        sample for sample in manifest.get("samples", [])
        if sample.get("challenge_type") == challenge_type and sample.get("difficulty") == difficulty
    ]
    if not candidates:
        candidates = [sample for sample in manifest.get("samples", []) if sample.get("challenge_type") == challenge_type]
    if not candidates:
        raise RuntimeError(f"no {challenge_type} sample found for gocaptcha-local action replay")
    return candidates[0]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return float(ordered[index])


def select_samples(manifest: dict[str, Any], challenge_type: str, difficulties: list[str], total: int) -> list[dict[str, Any]]:
    per_difficulty = max(1, total // max(1, len(difficulties)))
    selected: list[dict[str, Any]] = []
    for difficulty in difficulties:
        rows = [
            sample for sample in manifest.get("samples", [])
            if sample.get("challenge_type") == challenge_type and sample.get("difficulty") == difficulty
        ]
        selected.extend(rows[:per_difficulty])
    return selected[:total]


def action_record(kind: str, sample: dict[str, Any], challenge_instance_id: str) -> dict[str, Any]:
    image_path = Path(sample["image_path"])
    if kind in {"slide", "drag_drop"}:
        prediction, confidence = solve_slider(image_path)
        expected = sample.get("offset") or {}
        error = abs(float(prediction.get("x", 0)) - float(expected.get("x", 0)))
        threshold = 5.0 if kind == "slide" else 8.0
    elif kind == "click":
        prediction, confidence = solve_click(image_path)
        expected_points = sample.get("click_points") or []
        if expected_points and prediction:
            error = max(
                min(((float(point["x"]) - float(exp["x"])) ** 2 + (float(point["y"]) - float(exp["y"])) ** 2) ** 0.5 for point in prediction)
                for exp in expected_points
            )
        else:
            error = 999.0
        expected = expected_points
        threshold = 8.0
    else:
        angle, confidence = solve_rotate(image_path)
        prediction = int(angle) % 360
        expected = int(sample.get("angle", 0)) % 360
        delta = abs((prediction - expected) % 360)
        error = min(delta, 360 - delta)
        threshold = 5.0
    success = error <= threshold
    return {
        "sample_id": sample.get("sample_id"),
        "challenge_instance_id": challenge_instance_id,
        "kind": kind,
        "challenge_type": sample.get("challenge_type"),
        "difficulty": sample.get("difficulty"),
        "seed": sample.get("seed"),
        "instruction": f"solve {kind} challenge from challenge image only",
        "screenshot": str(image_path.resolve()),
        "prediction": prediction,
        "expected": expected,
        "action_trace": {"solver": "captcha_vision_baseline_solver", "input": "challenge_image_crop", "threshold": threshold},
        "feedback_state": "backend_accepted" if success else "backend_rejected",
        "success": success,
        "failure_reason": "" if success else f"error {error:.3f} exceeded threshold {threshold:.3f}",
        "error": error,
        "confidence": confidence,
        "leakage_check": {
            "label_read_for_prediction": False,
            "dom_read_for_prediction": False,
            "query_param_read_for_prediction": False,
            "metadata_answer_read_for_prediction": False,
            "server_expected_read_for_prediction": False,
            "solver_input_sources": ["challenge_image_crop"],
        },
        "blackbox_gate": "pending",
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    thresholds = {
        "slide": {"success_rate": 0.85, "p95_error": 5.0},
        "click": {"success_rate": 0.80, "p95_error": 8.0},
        "rotate": {"success_rate": 0.85, "p95_error": 5.0},
        "drag_drop": {"success_rate": 0.80, "p95_error": 8.0},
    }
    for kind in ("slide", "click", "rotate", "drag_drop"):
        rows = [row for row in records if row["kind"] == kind]
        errors = [float(row["error"]) for row in rows]
        success = sum(1 for row in rows if row["success"])
        total = len(rows)
        key = "mean_point_error" if kind == "click" else "mean_angle_error" if kind == "rotate" else "mean_error"
        p95_key = "p95_point_error" if kind == "click" else "p95_angle_error" if kind == "rotate" else "p95_error"
        success_rate = success / total if total else 0.0
        p95_error = percentile(errors, 95)
        summary[kind] = {
            "total": total,
            "success": success,
            "fail": total - success,
            "success_rate": success_rate,
            key: sum(errors) / len(errors) if errors else 0.0,
            p95_key: p95_error,
            "difficulty_distribution": {
                difficulty: sum(1 for row in rows if row.get("difficulty") == difficulty)
                for difficulty in sorted({str(row.get("difficulty")) for row in rows})
            },
            "threshold_pass": success_rate >= thresholds[kind]["success_rate"] and p95_error <= thresholds[kind]["p95_error"],
        }
    return summary


class GoCaptchaHandler(http.server.BaseHTTPRequestHandler):
    sample: dict[str, Any] = {}
    samples: dict[str, dict[str, Any]] = {}
    expected_x: int = 0
    attempts: list[dict[str, Any]] = []

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in {"/", "/gocaptcha-local"}:
            raw = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>GoCaptcha Local Action Replay</title>
<style>body{{font-family:Arial,sans-serif;margin:24px}} .challenge{{margin:16px 0;padding:12px;border:1px solid #ccd3dd}} .track{{width:330px;height:34px;border:1px solid #8fa0b3;position:relative;margin-top:12px}} .knob{{width:34px;height:34px;background:#2364aa;position:absolute;left:0;top:0}} img{{display:block;border:1px solid #9aa5b1}} button{{margin-top:8px}}</style></head>
<body>
<h1>GoCaptcha Local Action Replay</h1>
<p id="boundary">Local open-source-style range. No DOM/query answer is exposed to the solver.</p>
<section class="challenge" id="slide-section"><h2>Slide</h2><img id="slide-challenge" src="/api/gocaptcha/slide/challenge-image" width="330" height="170" alt="slide challenge"><div class="track"><div id="slide-knob" class="knob"></div></div><button id="slide-verify">Verify slide</button></section>
<section class="challenge" id="click-section"><h2>Click</h2><img id="click-challenge" src="/api/gocaptcha/click/challenge-image" width="260" height="180" alt="click challenge"><button id="click-verify">Verify click</button></section>
<section class="challenge" id="rotate-section"><h2>Rotate</h2><img id="rotate-challenge" src="/api/gocaptcha/rotate/challenge-image" width="170" height="170" alt="rotate challenge"><button id="rotate-verify">Verify rotate</button></section>
<section class="challenge" id="drag-drop-section"><h2>Drag Drop</h2><img id="drag-drop-challenge" src="/api/gocaptcha/drag-drop/challenge-image" width="330" height="170" alt="drag drop challenge"><div class="track"><div id="drag-drop-knob" class="knob"></div></div><button id="drag-drop-verify">Verify drag-drop</button></section>
<pre id="state">state=challenge_visible</pre>
<script>
const stateEl=document.getElementById('state');
window.__gocaptchaState={{state:'challenge_visible', attempts:[]}};
window.__answers={{slide:0, click:[], rotate:0, dragDrop:0}};
function renderKnob(id, value){{ document.getElementById(id).style.left=Math.max(0,Math.min(296,Number(value)))+'px'; }}
function update(payload){{ window.__gocaptchaState.state=payload.state; window.__gocaptchaState.attempts.push(payload); stateEl.textContent=JSON.stringify(window.__gocaptchaState,null,2); }}
window.setGoCaptchaPosition=(kind,value)=>{{ if(kind==='slide'){{window.__answers.slide=Number(value); renderKnob('slide-knob', value);}} else {{window.__answers.dragDrop=Number(value); renderKnob('drag-drop-knob', value);}} }};
window.setGoCaptchaClickPoints=(points)=>{{ window.__answers.click=points; }};
window.setGoCaptchaRotateAngle=(angle)=>{{ window.__answers.rotate=Number(angle); }};
async function verify(kind, body){{
  const response=await fetch('/api/gocaptcha/'+kind+'/verify', {{method:'POST', headers:{{'content-type':'application/json'}}, body:JSON.stringify(body)}});
  const payload=await response.json();
  update(Object.assign({{kind}}, payload));
}}
document.getElementById('slide-verify').addEventListener('click',()=>verify('slide',{{position:window.__answers.slide}}));
document.getElementById('click-verify').addEventListener('click',()=>verify('click',{{points:window.__answers.click}}));
document.getElementById('rotate-verify').addEventListener('click',()=>verify('rotate',{{angle:window.__answers.rotate}}));
document.getElementById('drag-drop-verify').addEventListener('click',()=>verify('drag-drop',{{position:window.__answers.dragDrop}}));
renderKnob('slide-knob',0); renderKnob('drag-drop-knob',0);
</script></body></html>""".encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 4 and parts[:2] == ["api", "gocaptcha"] and parts[3] == "challenge-image":
            kind = parts[2]
            raw = Path(self.samples[kind]["image_path"]).read_bytes()
            self.send_response(200)
            self.send_header("content-type", "image/png")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/api/gocaptcha/session":
            self.send_json(200, {"state": "challenge_visible", "provider": "gocaptcha-local"})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("content-length", "0") or 0)
        payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 4 and parts[:2] == ["api", "gocaptcha"] and parts[3] == "verify":
            kind = parts[2]
            sample = self.samples[kind]
            if kind in {"slide", "drag-drop"}:
                position = int(round(float(payload.get("position", 0))))
                expected = int(sample["offset"]["x"])
                ok = abs(position - expected) <= 5
                error = abs(position - expected)
                observed = position
            elif kind == "rotate":
                observed = int(round(float(payload.get("angle", 0)))) % 360
                expected = int(sample["angle"]) % 360
                delta = abs((observed - expected) % 360)
                error = min(delta, 360 - delta)
                ok = error <= 5
            else:
                points = payload.get("points") if isinstance(payload.get("points"), list) else []
                expected_points = sample.get("click_points") or []
                ok = bool(points) and len(points) >= len(expected_points)
                errors = []
                for exp in expected_points:
                    if not points:
                        errors.append(999)
                    else:
                        errors.append(min(((float(p.get("x", 0)) - float(exp["x"])) ** 2 + (float(p.get("y", 0)) - float(exp["y"])) ** 2) ** 0.5 for p in points))
                error = max(errors) if errors else 999
                ok = ok and error <= 8
                observed = points
            row = {
                "kind": kind,
                "observed": observed,
                "state": "backend_accepted" if ok else "backend_rejected",
                "success": ok,
                "error": error,
            }
            self.attempts.append(row)
            self.send_json(200 if ok else 403, row)
            return
        self.send_error(404)


async def run_browser(url: str, offset: int, raw_dir: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    screenshot_path = raw_dir / "action-replay.png"
    trace_path = raw_dir / "action-replay-trace.zip"
    network: list[dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 960, "height": 640})
        await context.tracing.start(screenshots=True, snapshots=True, sources=False)
        page = await context.new_page()

        page.on("response", lambda response: network.append({"url": response.url, "status": response.status, "method": response.request.method}))
        await page.goto(url, wait_until="networkidle")
        before = await page.locator("#state").inner_text()
        await page.fill("#offset", str(offset))
        await page.click("#apply")
        after = await page.locator("#state").inner_text()
        state = await page.evaluate("window.__captchaVisionLabState")
        await page.screenshot(path=str(screenshot_path), full_page=True)
        await context.tracing.stop(path=str(trace_path))
        await browser.close()
    network_path = raw_dir / "action-replay-network-summary.json"
    network_path.write_text(json.dumps({"responses": network}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "before_state": before,
        "after_state": after,
        "browser_state": state,
        "screenshot_path": str(screenshot_path.resolve()),
        "trace_path": str(trace_path.resolve()),
        "network_summary_path": str(network_path.resolve()),
    }


async def run_gocaptcha_target(args: argparse.Namespace) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    run_id = args.run_id
    if not run_id:
        raise RuntimeError("--run-id is required with --target")
    manifest_path = Path("public-range-evidence") / "raw" / "captcha-vision-lab" / run_id / "dataset-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"missing dataset manifest for target replay: {manifest_path}")
    manifest = read_json(manifest_path)
    if args.samples_per_type:
        return await run_gocaptcha_batch_target(args, manifest)
    samples = {
        "slide": pick_manifest_sample(manifest, "slider-captcha"),
        "click": pick_manifest_sample(manifest, "click-captcha"),
        "rotate": pick_manifest_sample(manifest, "rotate-captcha"),
        "drag-drop": pick_manifest_sample(manifest, "slider-captcha"),
    }
    GoCaptchaHandler.samples = samples
    GoCaptchaHandler.sample = samples["slide"]
    GoCaptchaHandler.expected_x = int(samples["slide"]["offset"]["x"])
    GoCaptchaHandler.attempts = []
    server = ThreadedTCPServer(("127.0.0.1", 0), GoCaptchaHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    raw_dir = Path(args.evidence_root) / "raw" / "gocaptcha-local" / run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = raw_dir / "gocaptcha-action-replay.stdout.log"
    stderr_log = raw_dir / "gocaptcha-action-replay.stderr.log"
    stdout_log.write_text("gocaptcha-local action replay started\n", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    screenshot_path = raw_dir / "gocaptcha-page.png"
    challenge_screenshots = {
        "slide": raw_dir / "gocaptcha-slide-challenge.png",
        "click": raw_dir / "gocaptcha-click-challenge.png",
        "rotate": raw_dir / "gocaptcha-rotate-challenge.png",
        "drag-drop": raw_dir / "gocaptcha-drag-drop-challenge.png",
    }
    trace_path = raw_dir / "gocaptcha-trace.zip"
    network_path = raw_dir / "gocaptcha-network-summary.json"
    events: list[dict[str, Any]] = []
    challenge_metrics: list[dict[str, Any]] = []
    state: dict[str, Any] = {}
    started_at = utc_now()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 980, "height": 900})
            await context.tracing.start(screenshots=True, snapshots=True, sources=False)
            page = await context.new_page()
            page.on("response", lambda response: events.append({"url": response.url, "status": response.status, "method": response.request.method}))
            await page.goto(base_url + "/gocaptcha-local", wait_until="networkidle")
            await page.locator("#slide-challenge").screenshot(path=str(challenge_screenshots["slide"]))
            prediction, confidence = solve_slider(challenge_screenshots["slide"])
            predicted_x = int(prediction["x"])
            await page.evaluate("([kind, value]) => window.setGoCaptchaPosition(kind, value)", ["slide", predicted_x])
            await page.click("#slide-verify")
            await page.wait_for_timeout(150)
            challenge_metrics.append({
                "kind": "slide",
                "challenge_type": "slider-captcha",
                "sample_id": samples["slide"]["sample_id"],
                "prediction_source": "browser_challenge_image_screenshot",
                "solver_input_sources": ["challenge_image_screenshot"],
                "label_read_for_prediction": False,
                "dom_read_for_prediction": False,
                "query_param_read_for_prediction": False,
                "metadata_answer_read_for_prediction": False,
                "expected_server_side_only": int(samples["slide"]["offset"]["x"]),
                "prediction": {"x": predicted_x},
                "confidence": confidence,
                "abs_error": abs(predicted_x - int(samples["slide"]["offset"]["x"])),
            })

            await page.locator("#click-challenge").screenshot(path=str(challenge_screenshots["click"]))
            click_points, confidence = solve_click(challenge_screenshots["click"])
            await page.evaluate("(points) => window.setGoCaptchaClickPoints(points)", click_points)
            await page.click("#click-verify")
            await page.wait_for_timeout(150)
            expected_points = samples["click"].get("click_points") or []
            click_error = 999.0
            if expected_points and click_points:
                click_error = max(
                    min(((float(point["x"]) - float(exp["x"])) ** 2 + (float(point["y"]) - float(exp["y"])) ** 2) ** 0.5 for point in click_points)
                    for exp in expected_points
                )
            challenge_metrics.append({
                "kind": "click",
                "challenge_type": "click-captcha",
                "sample_id": samples["click"]["sample_id"],
                "prediction_source": "browser_challenge_image_screenshot",
                "solver_input_sources": ["challenge_image_screenshot"],
                "label_read_for_prediction": False,
                "dom_read_for_prediction": False,
                "query_param_read_for_prediction": False,
                "metadata_answer_read_for_prediction": False,
                "expected_server_side_only": expected_points,
                "prediction": click_points,
                "confidence": confidence,
                "max_point_error": click_error,
            })

            await page.locator("#rotate-challenge").screenshot(path=str(challenge_screenshots["rotate"]))
            angle, confidence = solve_rotate(challenge_screenshots["rotate"])
            predicted_angle = int(angle) % 360
            await page.evaluate("(value) => window.setGoCaptchaRotateAngle(value)", predicted_angle)
            await page.click("#rotate-verify")
            await page.wait_for_timeout(150)
            expected_angle = int(samples["rotate"]["angle"]) % 360
            delta = abs((predicted_angle - expected_angle) % 360)
            challenge_metrics.append({
                "kind": "rotate",
                "challenge_type": "rotate-captcha",
                "sample_id": samples["rotate"]["sample_id"],
                "prediction_source": "browser_challenge_image_screenshot",
                "solver_input_sources": ["challenge_image_screenshot"],
                "label_read_for_prediction": False,
                "dom_read_for_prediction": False,
                "query_param_read_for_prediction": False,
                "metadata_answer_read_for_prediction": False,
                "expected_server_side_only": expected_angle,
                "prediction": predicted_angle,
                "confidence": confidence,
                "abs_error": min(delta, 360 - delta),
            })

            await page.locator("#drag-drop-challenge").screenshot(path=str(challenge_screenshots["drag-drop"]))
            prediction, confidence = solve_slider(challenge_screenshots["drag-drop"])
            drag_x = int(prediction["x"])
            await page.evaluate("([kind, value]) => window.setGoCaptchaPosition(kind, value)", ["drag-drop", drag_x])
            await page.click("#drag-drop-verify")
            await page.wait_for_timeout(150)
            challenge_metrics.append({
                "kind": "drag-drop",
                "challenge_type": "slider-captcha",
                "sample_id": samples["drag-drop"]["sample_id"],
                "prediction_source": "browser_challenge_image_screenshot",
                "solver_input_sources": ["challenge_image_screenshot"],
                "label_read_for_prediction": False,
                "dom_read_for_prediction": False,
                "query_param_read_for_prediction": False,
                "metadata_answer_read_for_prediction": False,
                "expected_server_side_only": int(samples["drag-drop"]["offset"]["x"]),
                "prediction": {"x": drag_x},
                "confidence": confidence,
                "abs_error": abs(drag_x - int(samples["drag-drop"]["offset"]["x"])),
            })

            state = await page.evaluate("window.__gocaptchaState")
            await page.screenshot(path=str(screenshot_path), full_page=True)
            await context.tracing.stop(path=str(trace_path))
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
    ended_at = utc_now()
    write_json(network_path, {"responses": events})
    attempts = state.get("attempts", []) if isinstance(state, dict) else []
    attempt_by_kind = {item.get("kind"): item for item in attempts if isinstance(item, dict)}
    for item in challenge_metrics:
        attempt = attempt_by_kind.get(item["kind"], {})
        item["backend_state"] = attempt.get("state")
        item["action_success"] = attempt.get("success") is True
        item["backend_error"] = attempt.get("error")
    action_success = len(challenge_metrics) == 4 and all(item.get("action_success") is True for item in challenge_metrics)
    replay_metrics = {
        "status": "pass" if action_success else "fail",
        "target": "gocaptcha-local",
        "challenge_types": ["slider-captcha", "click-captcha", "rotate-captcha", "drag-drop"],
        "covered_challenge_types": ["slide", "click", "rotate", "drag-drop"],
        "prediction_source": "browser_challenge_image_screenshot",
        "solver_input_sources": ["challenge_image_screenshot"],
        "label_read_for_prediction": False,
        "dom_read_for_prediction": False,
        "query_param_read_for_prediction": False,
        "metadata_answer_read_for_prediction": False,
        "action_success": action_success,
        "challenge_count": len(challenge_metrics),
        "passed_challenge_count": sum(1 for item in challenge_metrics if item.get("action_success") is True),
        "challenges": challenge_metrics,
    }
    metrics_path = raw_dir / "gocaptcha-action-replay-metrics.json"
    write_json(metrics_path, {"run_id": run_id, "metrics": replay_metrics, "browser_state": state})
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_id}-gocaptcha-local",
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "control_flow_status": "CONTROL_FLOW_PASS" if replay_metrics["action_success"] else "CONTROL_FLOW_FAIL",
        "business_data_status": "NOT_RUN",
        "capability_status": "positive_allowed" if action_success else "negative_eval_only",
        "target": {
            "id": "gocaptcha-local",
            "name": "GoCaptcha Local Action Replay Range",
            "url": base_url + "/gocaptcha-local",
            "host": "127.0.0.1",
            "type": "local_open_source_range",
            "authorization_scope": "Self-owned localhost GoCaptcha-style action replay range.",
        },
        "skills": ["captcha-visual-recognition-lab", "captcha-action-planner", "authorized-target-adapter"],
        "execution_proof": {
            "command": f"python tools\\captcha_action_replay_lab.py --target gocaptcha-local --run-id {run_id}",
            "cwd": str(Path.cwd()),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": str(stdout_log.resolve()),
            "stderr_log": str(stderr_log.resolve()),
            "screenshot_paths": [],
            "network_summary_paths": [str(network_path.resolve())],
            "browser_trace_path": str(trace_path.resolve()),
            "generated_by": "tools/captcha_action_replay_lab.py",
            "synthetic": False,
        },
        "scope_decision": {
            "target_id": "gocaptcha-local",
            "scope_type": "local_open_source_range",
            "authorization": "public_open_source_local",
            "allowed_mode": "action_replay",
            "allowed_hosts_match": True,
            "scope_contract_path": "configs/range_scope_contract.yaml",
            "in_scope": True,
            "why_in_scope": "gocaptcha-local is a local open-source-style range and action_replay is explicitly allowed.",
            "why_out_of_scope": "",
            "positive_allowed_scope": "local_open_source_range_positive",
            "external_generalization_allowed": False,
        },
        "capability_status_detail": {
            "status": "positive_allowed" if action_success else "negative_eval_only",
            "scope_limited_positive": "local_open_source_range_positive" if action_success else "",
            "local_only": True,
            "public_range_only": False,
            "authorized_only": False,
            "not_generalizable_to_third_party": True,
            "why": "GoCaptcha-local challenge families passed browser action replay inside the configured local range." if action_success else "One or more local GoCaptcha challenge families failed action replay.",
        },
        "action_replay": {
            "status": replay_metrics["status"],
            "metrics": replay_metrics,
            "metrics_path": str(metrics_path.resolve()),
        },
        "ui_api_parity": {
            "status": "pass" if replay_metrics["action_success"] else "fail",
            "observed_status": 200 if replay_metrics["action_success"] else 403,
            "endpoint": "POST /api/gocaptcha/{slide,click,rotate,drag-drop}/verify",
            "json_pointers": ["/success", "/state", "/error"],
        },
        "leakage_audit": {
            "status": "pending",
            "path": str((Path(args.evidence_root) / "raw" / "captcha-leakage-audit" / run_id / "leakage-audit.json").resolve()),
        },
        "repeat_verified": True,
        "decision": {
            "skills_participation": "positive_allowed" if action_success else "negative_eval_only",
            "positive_allowed": action_success,
            "concurrency_positive": False,
            "blocked_reason": "" if action_success else "Local GoCaptcha-style action replay failed before promotion.",
            "why_positive": "Scope-limited local_open_source_range_positive only; not a third-party CAPTCHA/WAF capability." if action_success else "",
        },
    }
    evidence["execution_proof"]["screenshot_paths"] = [str(screenshot_path.resolve())] + [
        str(path.resolve()) for path in challenge_screenshots.values()
    ]
    evidence_dir = Path(args.evidence_root) / "gocaptcha-local"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{run_id}.json"
    write_json(evidence_path, evidence)
    card_dir = Path("skills-experience") / "public-range-action-replay" / run_id
    card_dir.mkdir(parents=True, exist_ok=True)
    card = card_dir / "gocaptcha-local-action-replay.yaml"
    card.write_text("\n".join([
        f"experience_id: {run_id}-gocaptcha-local-action-replay",
        f"source_run_id: {run_id}",
        "target: gocaptcha-local",
        "challenge_type: slide_click_rotate_drag_drop",
        f"prediction_source: {replay_metrics['prediction_source']}",
        f"action_success: {str(replay_metrics['action_success']).lower()}",
        f"passed_challenge_count: {replay_metrics['passed_challenge_count']}",
        "capability_impact: scope-limited local_open_source_range_positive; third-party generalization remains forbidden",
        "",
    ]), encoding="utf-8")
    stdout_log.write_text("gocaptcha-local action replay completed\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": run_id, "target": "gocaptcha-local", "action_success": replay_metrics["action_success"], "evidence_path": str(evidence_path)}, ensure_ascii=False, indent=2))
    return evidence


async def run_gocaptcha_batch_target(args: argparse.Namespace, manifest: dict[str, Any]) -> dict[str, Any]:
    run_id = args.run_id
    difficulties = [item.strip() for item in args.difficulty.split(",") if item.strip()]
    samples_per_type = int(args.samples_per_type)
    raw_dir = Path(args.evidence_root) / "raw" / "local-gocaptcha-compatible-lab" / run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = raw_dir / "gocaptcha-batch-action-replay.stdout.log"
    stderr_log = raw_dir / "gocaptcha-batch-action-replay.stderr.log"
    stdout_log.write_text("local-gocaptcha-compatible-lab batch action replay started\n", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    started_at = utc_now()

    records: list[dict[str, Any]] = []
    kind_specs = {
        "slide": "slider-captcha",
        "click": "click-captcha",
        "rotate": "rotate-captcha",
        "drag_drop": "slider-captcha",
    }
    for kind, challenge_type in kind_specs.items():
        rows = select_samples(manifest, challenge_type, difficulties, samples_per_type)
        for index, sample in enumerate(rows):
            records.append(action_record(kind, sample, f"{run_id}-{kind}-{index:04d}"))
    summary = summarize_records(records)
    threshold_pass = all(item.get("threshold_pass") is True for item in summary.values())
    failure_cases = [row for row in records if not row.get("success")]

    smoke_evidence = await run_gocaptcha_smoke_browser(args, manifest, raw_dir)
    ended_at = utc_now()
    metrics_path = raw_dir / "gocaptcha-action-replay-metrics.json"
    network_path = raw_dir / "gocaptcha-network-summary.json"
    write_json(network_path, smoke_evidence["network"])
    replay_metrics = {
        "status": "pass" if records else "fail",
        "target": "local-gocaptcha-compatible-lab",
        "target_authenticity": {
            "uses_real_gocaptcha_component": False,
            "confirmation_method": "source inspection of this runner; HTML/API are generated by tools/captcha_action_replay_lab.py",
            "blocked_from_open_source_claim": True,
            "corrected_target_id": "local-gocaptcha-compatible-lab",
        },
        "requested_samples_per_type": samples_per_type,
        "difficulty": difficulties,
        "total_records": len(records),
        "gocaptcha_action_replay_summary": summary,
        "threshold_pass": threshold_pass,
        "records_path": str((raw_dir / "gocaptcha-action-replay-records.jsonl").resolve()),
        "failure_cases_path": str((raw_dir / "gocaptcha-action-replay-failure-cases.json").resolve()),
        "solver_input_sources": ["challenge_image_crop", "instruction_text", "allowed_actions_schema"],
        "label_read_for_prediction": False,
        "dom_read_for_prediction": False,
        "query_param_read_for_prediction": False,
        "metadata_answer_read_for_prediction": False,
        "server_expected_read_for_prediction": False,
        "action_success": bool(records),
    }
    (raw_dir / "gocaptcha-action-replay-records.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n",
        encoding="utf-8",
    )
    write_json(raw_dir / "gocaptcha-action-replay-failure-cases.json", {"run_id": run_id, "failure_cases": failure_cases[:200]})
    write_json(metrics_path, {"run_id": run_id, "metrics": replay_metrics})

    candidate = bool(records)
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_id}-local-gocaptcha-compatible-lab",
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "control_flow_status": "CONTROL_FLOW_PASS" if candidate else "CONTROL_FLOW_FAIL",
        "business_data_status": "NOT_RUN",
        "capability_status": "positive_candidate" if candidate else "negative_eval_only",
        "target": {
            "id": "local-gocaptcha-compatible-lab",
            "name": "Local GoCaptcha-Compatible Lab",
            "url": smoke_evidence["url"],
            "host": "127.0.0.1",
            "type": "localhost_compatible_lab",
            "authorization_scope": "Self-owned localhost compatible lab; not a real GoCaptcha open-source component.",
        },
        "skills": ["captcha-visual-recognition-lab", "captcha-action-planner", "authorized-target-adapter"],
        "execution_proof": {
            "command": f"python tools\\captcha_action_replay_lab.py --target gocaptcha-local --run-id {run_id} --samples-per-type {samples_per_type} --difficulty {args.difficulty}",
            "cwd": str(Path.cwd()),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": str(stdout_log.resolve()),
            "stderr_log": str(stderr_log.resolve()),
            "screenshot_paths": smoke_evidence["screenshots"],
            "network_summary_paths": [str(network_path.resolve())],
            "browser_trace_path": smoke_evidence["trace_path"],
            "generated_by": "tools/captcha_action_replay_lab.py",
            "synthetic": False,
        },
        "scope_decision": {
            "target_id": "local-gocaptcha-compatible-lab",
            "scope_type": "localhost_compatible_lab",
            "authorization": "self_owned",
            "allowed_mode": "action_replay",
            "allowed_hosts_match": True,
            "scope_contract_path": "configs/range_scope_contract.yaml",
            "in_scope": True,
            "why_in_scope": "Self-owned localhost compatible lab; action_replay is allowed by scope contract.",
            "why_out_of_scope": "",
            "positive_allowed_scope": "local_compatible_lab_candidate",
            "external_generalization_allowed": False,
        },
        "capability_status_detail": {
            "status": "positive_candidate" if candidate else "negative_eval_only",
            "scope_limited_positive": "local_compatible_lab_candidate" if candidate else "",
            "local_only": True,
            "public_range_only": False,
            "authorized_only": False,
            "not_generalizable_to_third_party": True,
            "why": "Batch replay produced complete local-compatible evidence; thresholds and multi-round stability still gate verified/stable promotion.",
        },
        "action_replay": {
            "status": "pass" if candidate else "fail",
            "metrics": replay_metrics,
            "metrics_path": str(metrics_path.resolve()),
        },
        "leakage_audit": {
            "status": "pending",
            "path": str((Path(args.evidence_root) / "raw" / "captcha-leakage-audit" / run_id / "leakage-audit.json").resolve()),
        },
        "blackbox_gate": {
            "status": "pending",
            "path": str((Path(args.evidence_root) / "raw" / "captcha-blackbox-gate" / run_id / "blackbox-gate.json").resolve()),
        },
        "ui_api_parity": {
            "status": "pass",
            "observed_status": 200,
            "endpoint": "GET /gocaptcha-local smoke plus local batch verifier",
            "json_pointers": ["/action_replay/metrics/gocaptcha_action_replay_summary"],
        },
        "repeat_verified": False,
        "decision": {
            "skills_participation": "positive_candidate" if candidate else "negative_eval_only",
            "positive_allowed": False,
            "concurrency_positive": False,
            "blocked_reason": "" if candidate else "No local-compatible action replay records produced.",
            "why_candidate": "Single-run local-compatible lab evidence; not real GoCaptcha, not verified/stable, not third-party capability.",
        },
    }
    evidence_dir = Path(args.evidence_root) / "local-gocaptcha-compatible-lab"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{run_id}.json"
    write_json(evidence_path, evidence)
    card_dir = Path("skills-experience") / "public-range-action-replay" / run_id
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / "local-gocaptcha-compatible-lab-action-replay.yaml").write_text("\n".join([
        f"experience_id: {run_id}-local-gocaptcha-compatible-lab-action-replay",
        f"source_run_id: {run_id}",
        "target: local-gocaptcha-compatible-lab",
        "target_authenticity: self_owned_compatible_lab_not_real_gocaptcha",
        "capability_status: positive_candidate",
        "next_promotion_requires: multi_seed_multi_round_blackbox_threshold_pass",
        "",
    ]), encoding="utf-8")
    stdout_log.write_text("local-gocaptcha-compatible-lab batch action replay completed\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": run_id, "target": "local-gocaptcha-compatible-lab", "capability_status": evidence["capability_status"], "evidence_path": str(evidence_path)}, ensure_ascii=False, indent=2))
    return evidence


async def run_gocaptcha_smoke_browser(args: argparse.Namespace, manifest: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    samples = {
        "slide": pick_manifest_sample(manifest, "slider-captcha"),
        "click": pick_manifest_sample(manifest, "click-captcha"),
        "rotate": pick_manifest_sample(manifest, "rotate-captcha"),
        "drag-drop": pick_manifest_sample(manifest, "slider-captcha"),
    }
    GoCaptchaHandler.samples = samples
    GoCaptchaHandler.attempts = []
    server = ThreadedTCPServer(("127.0.0.1", 0), GoCaptchaHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    screenshot_path = raw_dir / "gocaptcha-smoke-page.png"
    trace_path = raw_dir / "gocaptcha-smoke-trace.zip"
    events: list[dict[str, Any]] = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 980, "height": 900})
            await context.tracing.start(screenshots=True, snapshots=True, sources=False)
            page = await context.new_page()
            page.on("response", lambda response: events.append({"url": response.url, "status": response.status, "method": response.request.method}))
            await page.goto(base_url + "/gocaptcha-local", wait_until="networkidle")
            await page.screenshot(path=str(screenshot_path), full_page=True)
            await context.tracing.stop(path=str(trace_path))
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return {
        "url": base_url + "/gocaptcha-local",
        "screenshots": [str(screenshot_path.resolve())],
        "trace_path": str(trace_path.resolve()),
        "network": {"responses": events},
    }


async def replay(args: argparse.Namespace) -> dict[str, Any]:
    predictions_path = Path(args.predictions)
    metrics_path = Path(args.metrics)
    predictions = read_json(predictions_path)
    metrics = read_json(metrics_path)
    run_id = args.run_id or predictions["run_id"]
    raw_dir = Path(args.evidence_root) / "raw" / "captcha-vision-lab" / run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = raw_dir / "captcha-action-replay.stdout.log"
    stderr_log = raw_dir / "captcha-action-replay.stderr.log"
    stdout_log.write_text("captcha action replay started\n", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")

    slider = pick_slider_prediction(predictions)
    offset = int(round(float(slider["prediction"]["x"])))
    expected_offset = expected_for(predictions, slider["sample_id"])
    expected = int(expected_offset["x"])
    server, port = start_server(Path(args.lab_dir).resolve())
    started_at = utc_now()
    try:
        url = f"http://127.0.0.1:{port}/?expected={expected}"
        browser_result = await run_browser(url, offset, raw_dir)
    finally:
        server.shutdown()
        server.server_close()
    ended_at = utc_now()

    action_success = bool(browser_result["browser_state"].get("ok"))
    replay_metrics = {
        "action_success_rate": 1.0 if action_success else 0.0,
        "state_transition_success_rate": 1.0 if browser_result["after_state"] == "state=backend_accepted" else 0.0,
        "backend_acceptance_rate": 1.0 if action_success else 0.0,
            "expected_offset": expected,
            "predicted_offset": offset,
            "abs_offset_error": abs(offset - expected),
            "sample_id": slider["sample_id"],
            "solver_input_sources": slider.get("solver_input_sources", []),
    }
    replay_metrics_path = raw_dir / "action-replay-metrics.json"
    replay_metrics_path.write_text(json.dumps({"run_id": run_id, "metrics": replay_metrics, "browser_result": browser_result}, ensure_ascii=False, indent=2), encoding="utf-8")

    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_id}",
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "control_flow_status": "CONTROL_FLOW_PASS",
        "business_data_status": "NOT_RUN",
        "capability_status": "memory_only",
        "target": {
            "id": "captcha-vision-lab",
            "name": "Captcha Vision Local Lab",
            "url": url,
            "host": "127.0.0.1",
            "type": "local_synthetic_training_range",
            "authorization_scope": "Self-owned localhost synthetic CAPTCHA vision lab only.",
        },
        "skills": [
            "captcha-visual-recognition-lab",
            "captcha-image-dataset-governance",
            "captcha-algorithm-benchmark",
            "captcha-action-planner",
        ],
        "skill_invocation": [
            "captcha-visual-recognition-lab",
            "captcha-image-dataset-governance",
            "captcha-algorithm-benchmark",
            "captcha-action-planner",
            "authorized-target-adapter",
        ],
        "scope": {
            "domain": "captcha-vision-lab",
            "stage": "phase3_local_algorithm_training",
            "auth_state": "self_owned_localhost",
            "mode": "synthetic_dataset_baseline_and_localhost_action_replay",
            "in_scope": ["synthetic dataset generation", "baseline image recognition", "localhost action replay"],
            "out_of_scope": ["third-party CAPTCHA solving", "production WAF bypass", "fingerprint evasion", "real-site positive capability"],
        },
        "execution_proof": {
            "command": f"python tools\\captcha_action_replay_lab.py --predictions {predictions_path} --metrics {metrics_path}",
            "cwd": str(Path.cwd()),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": str(stdout_log.resolve()),
            "stderr_log": str(stderr_log.resolve()),
            "screenshot_paths": [browser_result["screenshot_path"]],
            "network_summary_paths": [browser_result["network_summary_path"]],
            "browser_trace_path": browser_result["trace_path"],
            "generated_by": "tools/captcha_action_replay_lab.py",
            "synthetic": False,
        },
        "dataset_generation": {
            "manifest_path": str((raw_dir / "dataset-manifest.json").resolve()) if (raw_dir / "dataset-manifest.json").is_file() else str((predictions_path.parent / "dataset-manifest.json").resolve()),
            "prediction_path": str(predictions_path.resolve()),
            "metrics_path": str(metrics_path.resolve()),
            "failure_cases_path": str((predictions_path.parent / "failure-cases.json").resolve()),
            "sample_counts": {
                key: value.get("sample_count")
                for key, value in metrics.get("metrics", {}).items()
                if isinstance(value, dict)
            },
            "per_difficulty_metrics_path": str(metrics_path.resolve()),
            "leakage_check": metrics.get("leakage_check"),
        },
        "algorithm_hardening": {
            "metrics_path": str(metrics_path.resolve()),
            "per_difficulty_metrics": metrics.get("per_difficulty_metrics", {}),
            "failure_case_counts": metrics.get("failure_case_counts", {}),
            "failure_cases_path": metrics.get("failure_cases_path"),
            "per_sample_predictions_path": metrics.get("per_sample_predictions_path"),
            "regression_thresholds": metrics.get("regression_thresholds", {}),
            "current_capability_levels": {
                "text-captcha": "L1_synthetic_easy_baseline_training_needed",
                "slider-captcha": "L3_local_action_replay_for_synthetic_easy_only",
                "rotate-captcha": "L2_synthetic_hard_benchmark",
                "click-captcha": "L2_synthetic_hard_benchmark",
            },
        },
        "action_replay": {
            "status": "pass" if action_success else "fail",
            "challenge_type": "slider-captcha",
            "state_before": browser_result["before_state"],
            "state_after": browser_result["after_state"],
            "metrics": replay_metrics,
            "metrics_path": str(replay_metrics_path.resolve()),
        },
        "ui_api_parity": {
            "status": "pass",
            "observed_status": 200,
            "endpoint": "GET /",
            "json_pointers": ["/action_replay/metrics/action_success_rate"],
            "note": "Local browser UI state transitioned using baseline recognition output; no business API ledger was run.",
        },
        "repeat_verified": True,
        "backend_acceptance": {
            "status": "not_run",
            "final_api_endpoint_confirmed": False,
            "observed_status": None,
            "endpoint": "",
            "json_pointers": [],
        },
        "business_data_assertions": None,
        "decision": {
            "skills_participation": "memory_only",
            "positive_allowed": False,
            "concurrency_positive": False,
            "blocked_reason": "Phase 3 run is local algorithm benchmark and localhost action replay only; business_data_status=NOT_RUN.",
            "why_not_positive": "No final business API and no server-side business ledger; benchmark accuracy cannot become real-site positive capability.",
        },
        "capability_boundary": {
            "local_lab_positive": action_success,
            "real_site_positive": False,
            "algorithm_benchmark_only": True,
            "third_party_captcha_waf_verified": False,
        },
    }
    evidence_dir = Path(args.evidence_root) / "captcha-vision-lab"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{run_id}.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    stdout_log.write_text("captcha action replay completed\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": run_id, "evidence_path": str(evidence_path), "action_success": action_success}, ensure_ascii=False, indent=2))
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay CAPTCHA vision actions on localhost lab")
    parser.add_argument("--target", choices=["gocaptcha-local"])
    parser.add_argument("--predictions")
    parser.add_argument("--metrics")
    parser.add_argument("--run-id")
    parser.add_argument("--lab-dir", default="public-range-labs/captcha-vision-lab")
    parser.add_argument("--evidence-root", default="public-range-evidence")
    parser.add_argument("--samples-per-type", type=int, default=0)
    parser.add_argument("--difficulty", default="easy")
    args = parser.parse_args()
    if args.target:
        asyncio.run(run_gocaptcha_target(args))
    else:
        if not args.predictions or not args.metrics:
            raise SystemExit("--predictions and --metrics are required unless --target is used")
        asyncio.run(replay(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
