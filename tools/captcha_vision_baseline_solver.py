#!/usr/bin/env python3
"""Run hardened local CAPTCHA baseline solvers without answer leakage."""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


TEXT_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "calibri.ttf", "consola.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def crop_bbox(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    bw = gray.point(lambda p: 0 if p < 170 else 255)
    inv = ImageOps.invert(bw)
    box = inv.getbbox()
    return bw.crop(box) if box else bw


def template_for(ch: str) -> Image.Image:
    image = Image.new("RGB", (42, 48), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((7, 4), ch, font=font(32), fill=(30, 30, 30))
    return crop_bbox(image).resize((24, 32))


TEMPLATES = {ch: template_for(ch) for ch in TEXT_CHARS}


def template_distance(a: Image.Image, b: Image.Image) -> float:
    a = a.resize((24, 32)).convert("L")
    b = b.resize((24, 32)).convert("L")
    total = 0
    for y in range(32):
        for x in range(24):
            total += abs(a.getpixel((x, y)) - b.getpixel((x, y)))
    return total / (24 * 32)


def solve_text(image_path: Path) -> tuple[str, float]:
    image = Image.open(image_path).convert("RGB")
    # The baseline assumes five visible glyph regions but does not read labels or metadata answers.
    regions = []
    usable_width = 190
    start_x = 8
    cell = usable_width // 5
    for i in range(5):
        regions.append(image.crop((start_x + i * cell, 8, start_x + (i + 1) * cell + 6, 70)))
    prediction = ""
    scores = []
    for region in regions:
        glyph = crop_bbox(region).resize((24, 32))
        best_ch = "?"
        best_dist = 999999.0
        for ch, tmpl in TEMPLATES.items():
            dist = template_distance(glyph, tmpl)
            if dist < best_dist:
                best_dist = dist
                best_ch = ch
        prediction += best_ch
        scores.append(best_dist)
    confidence = max(0.0, 1.0 - (sum(scores) / len(scores) / 120.0)) if scores else 0.0
    return prediction, confidence


def solve_slider(image_path: Path) -> tuple[dict[str, int], float]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    visited: set[tuple[int, int]] = set()
    components: list[tuple[int, int, int, int, int]] = []
    for y in range(20, height - 20):
        for x in range(20, width - 20):
            if (x, y) in visited:
                continue
            r, g, b = image.getpixel((x, y))
            if r + g + b <= 705:
                continue
            stack = [(x, y)]
            visited.add((x, y))
            xs: list[int] = []
            ys: list[int] = []
            while stack:
                px, py = stack.pop()
                xs.append(px)
                ys.append(py)
                for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                    if nx < 20 or ny < 20 or nx >= width - 20 or ny >= height - 20 or (nx, ny) in visited:
                        continue
                    rr, gg, bb = image.getpixel((nx, ny))
                    if rr + gg + bb > 705:
                        visited.add((nx, ny))
                        stack.append((nx, ny))
            if len(xs) >= 200:
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                box_w = max_x - min_x + 1
                box_h = max_y - min_y + 1
                if 22 <= box_w <= 56 and 22 <= box_h <= 56:
                    components.append((len(xs), min_x, min_y, box_w, box_h))
    if components:
        _, x, y, _, _ = max(components, key=lambda item: item[0])
        return {"x": int(x), "y": int(y)}, 0.85

    column_scores: list[tuple[float, int]] = []
    row_scores: list[tuple[float, int]] = []
    for x in range(20, width - 20):
        bright = 0
        edge = 0
        for y in range(20, height - 20, 2):
            r, g, b = image.getpixel((x, y))
            if r + g + b > 650:
                bright += 1
            if x + 1 < width:
                r2, g2, b2 = image.getpixel((x + 1, y))
                if abs(r - r2) + abs(g - g2) + abs(b - b2) > 70:
                    edge += 1
        column_scores.append((bright * 2.0 + edge * 0.6, x))
    for y in range(20, height - 20):
        bright = 0
        edge = 0
        for x in range(20, width - 20, 2):
            r, g, b = image.getpixel((x, y))
            if r + g + b > 650:
                bright += 1
            if y + 1 < height:
                r2, g2, b2 = image.getpixel((x, y + 1))
                if abs(r - r2) + abs(g - g2) + abs(b - b2) > 70:
                    edge += 1
        row_scores.append((bright * 2.0 + edge * 0.6, y))
    best_col, x = max(column_scores)
    best_row, y = max(row_scores)
    return {"x": max(0, int(x) - 1), "y": max(0, int(y) - 1)}, min(1.0, (best_col + best_row) / 260.0)


def solve_rotate(image_path: Path) -> tuple[int, float]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    cx, cy = width / 2, height / 2
    points: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))
            if r > 155 and g < 115 and b < 115:
                points.append((x, y))
    if not points:
        return 0, 0.0
    far = max(points, key=lambda point: (point[0] - cx) ** 2 + (point[1] - cy) ** 2)
    radians = math.atan2(cy - far[1], far[0] - cx)
    return int(round(math.degrees(radians))) % 360, min(1.0, len(points) / 800.0)


def solve_click(image_path: Path) -> tuple[list[dict[str, int]], float]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    visited: set[tuple[int, int]] = set()
    points: list[dict[str, int]] = []
    for y in range(height):
        for x in range(width):
            if (x, y) in visited:
                continue
            r, g, b = image.getpixel((x, y))
            if not (r > 160 and g < 100 and b < 100):
                continue
            stack = [(x, y)]
            visited.add((x, y))
            xs: list[int] = []
            ys: list[int] = []
            while stack:
                px, py = stack.pop()
                xs.append(px)
                ys.append(py)
                for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height or (nx, ny) in visited:
                        continue
                    rr, gg, bb = image.getpixel((nx, ny))
                    if rr > 160 and gg < 110 and bb < 110:
                        visited.add((nx, ny))
                        stack.append((nx, ny))
            if len(xs) >= 60:
                points.append({"x": int(sum(xs) / len(xs)), "y": int(sum(ys) / len(ys))})
    return points[:5], min(1.0, len(points) / 3.0)


def solve_multi_image(image_path: Path) -> tuple[dict[str, list[int]], float]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    grid = 3
    cell_w = width / grid
    cell_h = height / grid
    positives: list[int] = []
    scores: list[float] = []
    for idx in range(9):
        row, col = divmod(idx, 3)
        left = int(col * cell_w)
        top = int(row * cell_h)
        right = int((col + 1) * cell_w)
        bottom = int((row + 1) * cell_h)
        red_score = 0
        total = 0
        for y in range(top + 6, bottom - 6, 3):
            for x in range(left + 6, right - 6, 3):
                r, g, b = image.getpixel((x, y))
                total += 1
                if r > 150 and g < 120 and b < 120:
                    red_score += 1
        ratio = red_score / total if total else 0.0
        scores.append(ratio)
        if ratio > 0.08:
            positives.append(idx)
    return {"positive_indices": positives}, max(scores) if scores else 0.0


def solve_sample(sample: dict[str, Any]) -> dict[str, Any]:
    challenge_type = sample["challenge_type"]
    image_path = Path(sample["image_path"])
    if challenge_type == "text-captcha":
        prediction, confidence = solve_text(image_path)
        solver = "threshold_template_text_baseline"
    elif challenge_type == "slider-captcha":
        prediction, confidence = solve_slider(image_path)
        solver = "edge_brightness_gap_scan_baseline"
    elif challenge_type == "rotate-captcha":
        prediction, confidence = solve_rotate(image_path)
        solver = "red_edge_orientation_baseline"
    elif challenge_type == "click-captcha":
        prediction, confidence = solve_click(image_path)
        solver = "red_component_click_baseline"
    elif challenge_type == "multi-image-select":
        prediction, confidence = solve_multi_image(image_path)
        solver = "red_cell_multi_image_baseline"
    else:
        prediction = None
        confidence = 0.0
        solver = "unsupported"
    return {
        "sample_id": sample["sample_id"],
        "image_path": str(image_path),
        "label_path": sample["label_path"],
        "challenge_type": challenge_type,
        "difficulty": sample["difficulty"],
        "split": sample.get("split"),
        "prediction": prediction,
        "confidence": confidence,
        "solver": solver,
        "solver_input_sources": ["challenge_image"],
        "label_read_for_prediction": False,
        "dom_read_for_prediction": False,
        "query_param_read_for_prediction": False,
        "metadata_answer_read_for_prediction": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CAPTCHA vision baseline solvers")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    manifest = read_json(manifest_path)
    predictions = [solve_sample(sample) for sample in manifest.get("samples", [])]
    payload = {
        "run_id": manifest.get("run_id"),
        "generated_at": utc_now(),
        "manifest_path": str(manifest_path),
        "prediction_count": len(predictions),
        "leakage_claim": {
            "solver_input_sources": ["challenge_image"],
            "label_read_for_prediction": False,
            "dom_read_for_prediction": False,
            "query_param_read_for_prediction": False,
            "metadata_answer_read_for_prediction": False,
        },
        "predictions": predictions,
    }
    output_path = Path(args.output) if args.output else manifest_path.parent / "baseline-predictions.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": payload["run_id"], "prediction_path": str(output_path), "prediction_count": len(predictions)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
