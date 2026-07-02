#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


CHALLENGES: dict[str, dict[str, object]] = {}
DIFFICULTIES = {"easy", "medium", "hard", "adversarial"}
FAMILIES = {"slider", "puzzle", "spatial_reasoning", "image_restore", "no_trace", "one_click"}
COLORS = [("orange", "#f08c00"), ("purple", "#7048e8"), ("cyan", "#0b7285"), ("green", "#2f9e44"), ("red", "#d64545")]


def _rng(seed: str) -> random.Random:
    return random.Random(seed)


def _meta(seed: str, difficulty: str, family: str) -> dict[str, object]:
    rng = _rng(seed + family + difficulty)
    return {
        "challenge_instance_id": secrets.token_hex(8),
        "seed": seed,
        "difficulty": difficulty,
        "transform_pipeline": ["texture", "compression", "scale", "canvas_offset"] + (["decoy_gap", "occlusion"] if difficulty in {"hard", "adversarial"} else []),
        "noise_profile": {
            "background_compression": difficulty != "easy",
            "texture_interference": difficulty in {"medium", "hard", "adversarial"},
            "shape_interference": difficulty in {"hard", "adversarial"},
            "multi_gap": difficulty in {"hard", "adversarial"},
        },
        "viewport": {"width": rng.choice([375, 414, 768, 1440]), "height": rng.choice([667, 896, 900])},
        "device_pixel_ratio": rng.choice([1.0, 1.25, 1.5, 2.0]) if difficulty != "easy" else 1.0,
        "canvas_offset": {"x": rng.randint(-20, 24), "y": rng.randint(-14, 16)} if difficulty != "easy" else {"x": 0, "y": 0},
        "scale": rng.choice([0.86, 0.92, 1.0, 1.08, 1.18]) if difficulty in {"hard", "adversarial"} else rng.choice([0.96, 1.0, 1.04]),
        "feedback_state": "not_attempted",
        "server_state": {"answer_stored_server_side": True, "used": False},
        "answer_source": "server_hidden_not_returned",
        "leakage_sensitive_fields": ["answer", "correct_option", "server_expected", "metadata_answer"],
    }


def svg_slider(seed: str, difficulty: str, answer: int) -> str:
    rng = _rng(seed)
    decoys = []
    if difficulty in {"hard", "adversarial"}:
        for _ in range(2 if difficulty == "hard" else 5):
            x = rng.randint(35, 160)
            if abs(x - answer) > 14:
                decoys.append(x)
    noise = "".join(f"<rect x='{rng.randint(0,198)}' y='{rng.randint(0,78)}' width='2' height='2' fill='#c7d2fe'/>" for _ in range({"easy": 4, "medium": 16, "hard": 28, "adversarial": 44}[difficulty]))
    fake = "".join(f"<circle class='decoy-gap' cx='{x}' cy='42' r='11' fill='#303030' opacity='0.55'/>" for x in decoys)
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='210' height='90'><rect width='210' height='90' fill='#edf2ff'/>"
        f"{noise}{fake}<circle class='target-gap' cx='{answer}' cy='42' r='11' fill='#101010'/>"
        f"<text x='8' y='82' font-size='10'>slider {difficulty}; compatible_not_official</text></svg>"
    )


def svg_grid(seed: str, difficulty: str, family: str, target: str, sequence: list[str] | None = None) -> tuple[str, list[dict[str, int | str]]]:
    rng = _rng(seed + family)
    options = COLORS[:]
    rng.shuffle(options)
    if difficulty in {"hard", "adversarial"}:
        options.extend([("cyan-ish", "#0e7490"), ("orange-ish", "#fb923c")])
    cells: list[dict[str, int | str]] = []
    body = ["<svg xmlns='http://www.w3.org/2000/svg' width='300' height='135'>", "<rect width='300' height='135' fill='#f8fafc'/>"]
    for idx, (name, color) in enumerate(options):
        x = 16 + (idx % 4) * 68 + rng.randint(-3, 3)
        y = 28 + (idx // 4) * 52 + rng.randint(-3, 3)
        rot = rng.choice([-10, -5, 0, 7, 12]) if difficulty != "easy" else 0
        body.append(f"<g transform='rotate({rot} {x+21} {y+21})'><rect data-name='{name}' x='{x}' y='{y}' width='42' height='42' fill='{color}'/></g>")
        body.append(f"<text x='{x+15}' y='{y+54}' font-size='10'>{idx}</text>")
        cells.append({"index": idx, "name": name, "x": x, "y": y, "cx": x + 21, "cy": y + 21})
    clutter = "".join(f"<circle cx='{rng.randint(0,300)}' cy='{rng.randint(0,135)}' r='2' fill='#dbeafe'/>" for _ in range(12 if difficulty in {"hard", "adversarial"} else 3))
    body.append(clutter)
    body.append(f"<text x='8' y='14' font-size='10'>{family} {difficulty}: {','.join(sequence or [target])}; compatible_not_official</text></svg>")
    return "".join(body), cells


def build_challenge(family: str, difficulty: str) -> dict[str, object]:
    seed = secrets.token_hex(8)
    meta = _meta(seed, difficulty, family)
    cid = str(meta["challenge_instance_id"])
    rng = _rng(seed)
    if family == "slider":
        answer: object = rng.randint(45, 158)
        instruction = "slide to the black circle"
        image_svg = svg_slider(seed, difficulty, int(answer))
        schema = {"type": "slide_x", "tolerance_px": {"easy": 3, "medium": 3, "hard": 2, "adversarial": 1}[difficulty]}
    elif family == "puzzle":
        target = rng.choice(["cyan", "orange", "purple", "green"])
        image_svg, cells = svg_grid(seed, difficulty, family, target)
        answer = next(int(cell["index"]) for cell in cells if cell["name"] == target)
        instruction = f"choose {target} puzzle tile"
        schema = {"type": "select_option_index", "index_base": 0}
    elif family == "spatial_reasoning":
        target = rng.choice(["orange", "purple", "cyan", "green"])
        image_svg, cells = svg_grid(seed, difficulty, family, target)
        target_cell = next(cell for cell in cells if cell["name"] == target)
        answer = {"x": target_cell["cx"], "y": target_cell["cy"]}
        instruction = f"click center of the {target} square"
        schema = {"type": "click_xy", "tolerance_px": {"easy": 4, "medium": 4, "hard": 3, "adversarial": 2}[difficulty]}
    elif family == "image_restore":
        sequence = rng.sample(["cyan", "purple", "orange", "green"], 3)
        image_svg, cells = svg_grid(seed, difficulty, family, "sequence", sequence)
        answer = [next(int(cell["index"]) for cell in cells if cell["name"] == color) for color in sequence]
        instruction = "restore order " + ", then ".join(sequence)
        schema = {"type": "select_sequence", "index_base": 0}
    elif family == "one_click":
        answer = "one_click"
        image_svg, _ = svg_grid(seed, difficulty, family, "confirm")
        instruction = "one click confirmation state flow"
        schema = {"type": "one_click", "state_machine_only": True, "not_evasion": True}
        meta["server_state"] = {
            "answer_stored_server_side": True,
            "used": False,
            "state_flow": "clean -> one_click_visible -> backend_accepted",
            "challenge_instance_binding": True,
            "second_challenge_possible": False,
        }
    else:
        variants = ["no_trace_pass", "no_trace_fail_then_slider", "no_trace_fail_then_puzzle", "no_trace_fail_then_image_restore"]
        variant = variants[int(seed[:2], 16) % len(variants)]
        answer = "one_click"
        image_svg, _ = svg_grid(seed, difficulty, family, "state")
        instruction = f"no trace state flow variant {variant}"
        schema = {
            "type": "no_trace_state_machine",
            "state_machine_only": True,
            "variant": variant,
            "second_challenge_family": {
                "no_trace_pass": "",
                "no_trace_fail_then_slider": "slider",
                "no_trace_fail_then_puzzle": "puzzle",
                "no_trace_fail_then_image_restore": "image_restore",
            }[variant],
            "not_evasion": True,
        }
        meta["server_state"] = {
            "answer_stored_server_side": True,
            "used": False,
            "state_flow": f"clean -> no_trace_probe -> {variant} -> backend_feedback",
            "challenge_instance_binding": True,
            "second_challenge_possible": variant != "no_trace_pass",
            "state_flow_variant": variant,
        }
    payload = {
        **meta,
        "challenge_id": cid,
        "family": family,
        "instruction": instruction,
        "image_svg": image_svg,
        "image_path": f"inline://{family}/{difficulty}/{cid}.svg",
        "screenshot": "inline_svg",
        "expected_action_schema": schema,
        "allowed_action_schema": schema,
    }
    CHALLENGES[cid] = {"answer": answer, "family": family, "difficulty": difficulty, "used": False, "schema": schema, "created_at": time.time()}
    return payload


def _prediction_ok(prediction: object, challenge: dict[str, object]) -> bool:
    answer = challenge["answer"]
    schema = challenge.get("schema") if isinstance(challenge.get("schema"), dict) else {}
    tolerance = int(schema.get("tolerance_px") or 0)
    if isinstance(answer, int):
        return isinstance(prediction, int) and abs(prediction - answer) <= tolerance
    if isinstance(answer, list):
        return prediction == answer
    if isinstance(answer, dict) and isinstance(prediction, dict):
        try:
            return abs(float(prediction.get("x")) - float(answer["x"])) <= tolerance and abs(float(prediction.get("y")) - float(answer["y"])) <= tolerance
        except Exception:
            return False
    return prediction == answer


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: object, content_type: str = "application/json") -> None:
        raw = json.dumps(payload).encode("utf-8") if content_type == "application/json" else str(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, "<html><body><h1>Aliyun Compatible Lab</h1><p>compatible_not_official</p></body></html>", "text/html")
            return
        if parsed.path == "/api/challenge":
            qs = parse_qs(parsed.query)
            family = qs.get("family", ["slider"])[0]
            difficulty = qs.get("difficulty", ["easy"])[0]
            if family not in FAMILIES or difficulty not in DIFFICULTIES:
                self._send(404, {"error": "unknown_family_or_difficulty"})
                return
            self._send(200, build_challenge(family, difficulty))
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/api/verify":
            self._send(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        challenge = CHALLENGES.get(str(payload.get("challenge_id")))
        if not challenge or challenge.get("used") or time.time() - float(challenge.get("created_at", 0)) > 60:
            self._send(403, {"ok": False, "reason": "stale_or_duplicate"})
            return
        challenge["used"] = True
        ok = _prediction_ok(payload.get("prediction"), challenge)
        self._send(200 if ok else 403, {"ok": ok, "family": challenge.get("family"), "difficulty": challenge.get("difficulty"), "reason": "" if ok else "wrong_prediction"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
