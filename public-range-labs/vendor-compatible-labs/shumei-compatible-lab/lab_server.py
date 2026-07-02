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
FAMILIES = {"slide", "select", "icon_select", "seq_select", "spatial_select", "no_sense"}
COLORS = [
    ("blue", "#2b6cb0"),
    ("red", "#d64545"),
    ("green", "#2f9e44"),
    ("yellow", "#d6a700"),
    ("purple", "#7048e8"),
]


def _rng(seed: str) -> random.Random:
    return random.Random(seed)


def _meta(seed: str, difficulty: str, family: str) -> dict[str, object]:
    rng = _rng(seed + family + difficulty)
    dpr = rng.choice([1.0, 1.25, 1.5, 2.0]) if difficulty != "easy" else 1.0
    scale = rng.choice([0.85, 0.9, 1.0, 1.1, 1.2]) if difficulty in {"hard", "adversarial"} else rng.choice([0.95, 1.0, 1.05])
    offset = {"x": rng.randint(-18, 24), "y": rng.randint(-12, 18)} if difficulty != "easy" else {"x": 0, "y": 0}
    return {
        "challenge_instance_id": secrets.token_hex(8),
        "seed": seed,
        "difficulty": difficulty,
        "transform_pipeline": ["texture", "scale", "canvas_offset"] + (["occlusion", "decoy_targets"] if difficulty in {"hard", "adversarial"} else []),
        "noise_profile": {
            "background_texture": difficulty != "easy",
            "edge_noise": difficulty in {"medium", "hard", "adversarial"},
            "occlusion": difficulty in {"hard", "adversarial"},
            "compression": difficulty in {"medium", "hard", "adversarial"},
        },
        "viewport": {"width": rng.choice([360, 390, 768, 1366]), "height": rng.choice([640, 844, 900])},
        "device_pixel_ratio": dpr,
        "canvas_offset": offset,
        "scale": scale,
        "feedback_state": "not_attempted",
        "server_state": {"answer_stored_server_side": True, "used": False},
        "answer_source": "server_hidden_not_returned",
        "leakage_sensitive_fields": ["answer", "correct_option", "server_expected", "metadata_answer"],
    }


def svg_slide(seed: str, difficulty: str, answer: int) -> str:
    rng = _rng(seed)
    fakes = []
    if difficulty in {"hard", "adversarial"}:
        for _ in range(2 if difficulty == "hard" else 4):
            fake = rng.randint(35, 138)
            if abs(fake - answer) > 12:
                fakes.append(fake)
    noise = "".join(
        f"<circle cx='{rng.randint(5,155)}' cy='{rng.randint(5,65)}' r='{rng.randint(1,3)}' fill='#ccd6e0'/>"
        for _ in range({"easy": 2, "medium": 10, "hard": 22, "adversarial": 36}[difficulty])
    )
    fake_svg = "".join(f"<rect class='decoy-gap' x='{x}' y='20' width='18' height='28' fill='#303030' opacity='0.65'/>" for x in fakes)
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='82'>"
        "<rect width='180' height='82' fill='#f4f7fb'/>"
        f"{noise}{fake_svg}"
        f"<rect class='target-gap' x='{answer}' y='22' width='18' height='28' fill='#111'/>"
        "<path d='M0 56 C35 44 58 72 92 52 S142 40 180 58' stroke='#9fb3c8' fill='none'/>"
        f"<text x='8' y='76' font-size='10'>slide {difficulty}; compatible_not_official</text></svg>"
    )


def svg_grid(seed: str, difficulty: str, family: str, target: str, sequence: list[str] | None = None) -> tuple[str, list[dict[str, int | str]]]:
    rng = _rng(seed + family)
    options = COLORS[:]
    rng.shuffle(options)
    if difficulty in {"hard", "adversarial"}:
        options.extend([("red-ish", "#d94d5c"), ("green-ish", "#38a169")])
    cells: list[dict[str, int | str]] = []
    body = ["<svg xmlns='http://www.w3.org/2000/svg' width='300' height='135'>", "<rect width='300' height='135' fill='#fbfcfe'/>"]
    for idx, (name, color) in enumerate(options):
        x = 16 + (idx % 4) * 68 + rng.randint(-3, 3)
        y = 28 + (idx // 4) * 52 + rng.randint(-3, 3)
        rot = rng.choice([-11, -6, 0, 5, 9]) if difficulty != "easy" else 0
        opacity = "0.55" if difficulty == "adversarial" and idx % 5 == 0 else "1"
        body.append(f"<g transform='rotate({rot} {x+21} {y+21})'><rect data-name='{name}' x='{x}' y='{y}' width='42' height='42' fill='{color}' opacity='{opacity}'/></g>")
        body.append(f"<text x='{x+15}' y='{y+54}' font-size='10'>{idx}</text>")
        cells.append({"index": idx, "name": name, "x": x, "y": y, "cx": x + 21, "cy": y + 21})
    prompt = ",".join(sequence or [target])
    clutter = "".join(f"<line x1='{rng.randint(0,300)}' y1='{rng.randint(0,135)}' x2='{rng.randint(0,300)}' y2='{rng.randint(0,135)}' stroke='#d9e2ec'/>" for _ in range(6 if difficulty in {"hard", "adversarial"} else 1))
    body.append(clutter)
    body.append(f"<text x='8' y='14' font-size='10'>{family} {difficulty}: {prompt}; compatible_not_official</text></svg>")
    return "".join(body), cells


def build_challenge(family: str, difficulty: str) -> dict[str, object]:
    seed = secrets.token_hex(8)
    meta = _meta(seed, difficulty, family)
    cid = str(meta["challenge_instance_id"])
    rng = _rng(seed)
    if family == "slide":
        answer: object = rng.randint(42, 134)
        instruction = "move slider to the visible target gap"
        image_svg = svg_slide(seed, difficulty, int(answer))
        schema = {"type": "slide_x", "tolerance_px": {"easy": 3, "medium": 3, "hard": 2, "adversarial": 1}[difficulty]}
    elif family == "select":
        target = rng.choice(["red", "green", "blue", "purple"])
        image_svg, cells = svg_grid(seed, difficulty, family, target)
        answer = next(int(cell["index"]) for cell in cells if cell["name"] == target)
        instruction = f"select the {target} text target"
        schema = {"type": "select_option_index", "index_base": 0}
    elif family == "icon_select":
        target = rng.choice(["green", "blue", "yellow", "purple"])
        image_svg, cells = svg_grid(seed, difficulty, family, target)
        answer = next(int(cell["index"]) for cell in cells if cell["name"] == target)
        instruction = f"select the {target} icon"
        schema = {"type": "select_option_index", "index_base": 0}
    elif family == "seq_select":
        sequence = rng.sample(["red", "green", "blue", "purple"], 3)
        image_svg, cells = svg_grid(seed, difficulty, family, "sequence", sequence)
        answer = [next(int(cell["index"]) for cell in cells if cell["name"] == color) for color in sequence]
        instruction = "select " + ", then ".join(sequence)
        schema = {"type": "select_sequence", "index_base": 0}
    elif family == "spatial_select":
        target = rng.choice(["red", "green", "blue", "purple"])
        image_svg, cells = svg_grid(seed, difficulty, "spatial_select", target)
        target_cell = next(cell for cell in cells if cell["name"] == target)
        answer = {"x": target_cell["cx"], "y": target_cell["cy"]}
        instruction = f"click center of the {target} region"
        schema = {"type": "click_xy", "tolerance_px": {"easy": 4, "medium": 4, "hard": 3, "adversarial": 2}[difficulty]}
    else:
        answer = "one_click"
        image_svg, _ = svg_grid(seed, difficulty, family, "state")
        instruction = "no-sense state flow observation, then server verify"
        schema = {
            "type": "state_machine_only",
            "mode": "no_sense",
            "requires_server_verify": True,
            "requires_business_api_after_verify": True,
            "not_evasion": True,
        }
        meta["server_state"] = {
            "answer_stored_server_side": True,
            "used": False,
            "state_flow": "clean -> challenge_visible -> token_issued -> backend_accepted",
            "challenge_instance_binding": True,
            "second_challenge_possible": difficulty in {"hard", "adversarial"},
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
            self._send(200, "<html><body><h1>Shumei Compatible Lab</h1><p>compatible_not_official</p></body></html>", "text/html")
            return
        if parsed.path == "/api/challenge":
            qs = parse_qs(parsed.query)
            family = qs.get("family", ["slide"])[0]
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
