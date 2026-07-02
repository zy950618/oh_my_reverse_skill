#!/usr/bin/env python3
"""Generate hardened local synthetic CAPTCHA vision datasets for Phase 3.1."""
from __future__ import annotations

import argparse
import json
import math
import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


GENERATOR_VERSION = "captcha-vision-generator/3.1.0"
CHALLENGE_TYPES = ("text-captcha", "slider-captcha", "rotate-captcha", "click-captcha", "multi-image-select")
DIFFICULTIES = ("easy", "medium", "hard", "adversarial")
TEXT_CHARS = string.ascii_uppercase + string.digits


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_run_id() -> str:
    return "run-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-captcha-vision-hardening"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "calibri.ttf", "consola.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def add_noise(draw: ImageDraw.ImageDraw, rng: random.Random, width: int, height: int, count: int) -> None:
    for _ in range(count):
        x = rng.randrange(width)
        y = rng.randrange(height)
        shade = rng.randrange(40, 230)
        draw.point((x, y), fill=(shade, shade, shade))


def maybe_jpeg(image: Image.Image, path: Path, difficulty: str) -> Path:
    if difficulty not in {"hard", "adversarial"}:
        image.save(path)
        return path
    jpeg_path = path.with_suffix(".jpg")
    image.save(jpeg_path, quality=45 if difficulty == "adversarial" else 68)
    return jpeg_path


def split_for(index: int) -> str:
    mod = index % 10
    if mod < 7:
        return "train"
    if mod < 9:
        return "val"
    return "test"


def base_label(
    sample_id: str,
    challenge_type: str,
    difficulty: str,
    image_path: Path,
    label_path: Path,
    seed: int,
    transform_pipeline: list[str],
    answer: Any,
    index: int,
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "challenge_type": challenge_type,
        "difficulty": difficulty,
        "image_path": str(image_path),
        "label_path": str(label_path),
        "seed": seed,
        "generator_version": GENERATOR_VERSION,
        "transform_pipeline": transform_pipeline,
        "answer_source": "synthetic_generator_label",
        "split": split_for(index),
        "synthetic": True,
        "authorized_sample": False,
        "source_scope": "localhost_synthetic",
        "answer": answer,
        "bounding_boxes": [],
        "click_points": [],
        "offset": None,
        "angle": None,
        "generated_at": utc_now(),
    }


def save_label(label_path: Path, label: dict[str, Any]) -> None:
    label_path.write_text(json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8")


def text_sample(out_dir: Path, index: int, seed: int, difficulty: str) -> dict[str, Any]:
    rng = random.Random(seed)
    width, height = 210, 78
    answer = "".join(rng.choice(TEXT_CHARS) for _ in range(5))
    image = Image.new("RGB", (width, height), (235, 240, 242))
    draw = ImageDraw.Draw(image)
    transform = ["grayscale_ready_background", "random_spacing", "noise"]
    fnt = font(32)
    x = 12
    boxes = []
    for i, ch in enumerate(answer):
        spacing = rng.randint(34, 39) if difficulty == "easy" else rng.randint(29, 43)
        y = 18 + rng.randint(-2, 2)
        glyph = Image.new("RGBA", (42, 48), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glyph)
        gd.text((7, 4), ch, font=fnt, fill=(25 + rng.randint(0, 35), 35, 55, 255))
        if difficulty in {"hard", "adversarial"}:
            glyph = glyph.rotate(rng.uniform(-18, 18), expand=False, resample=Image.Resampling.BICUBIC)
            transform.append("char_rotation")
        if difficulty == "adversarial" and i > 0:
            x -= rng.randint(5, 10)
            transform.append("sticky_chars")
        image.paste(glyph, (x, y), glyph)
        boxes.append({"x": x, "y": y, "width": 42, "height": 48, "char_index": i})
        x += spacing
    line_count = {"easy": 1, "medium": 4, "hard": 7, "adversarial": 10}[difficulty]
    for _ in range(line_count):
        draw.line(
            (rng.randrange(width), rng.randrange(height), rng.randrange(width), rng.randrange(height)),
            fill=(rng.randrange(70, 210), rng.randrange(70, 210), rng.randrange(70, 210)),
            width=1 if difficulty != "adversarial" else 2,
        )
    add_noise(draw, rng, width, height, {"easy": 80, "medium": 260, "hard": 520, "adversarial": 900}[difficulty])
    if difficulty in {"hard", "adversarial"}:
        image = image.filter(ImageFilter.GaussianBlur(0.5 if difficulty == "hard" else 0.9))
        transform.append("blur")
    sample_id = f"text-{difficulty}-{index:04d}"
    image_path = maybe_jpeg(image, out_dir / f"{sample_id}.png", difficulty)
    label_path = out_dir / f"{sample_id}.json"
    label = base_label(sample_id, "text-captcha", difficulty, image_path, label_path, seed, transform, answer, index)
    label["bounding_boxes"] = boxes
    label["charset"] = "ascii_upper_digits"
    save_label(label_path, label)
    return label


def textured_background(width: int, height: int, rng: random.Random) -> Image.Image:
    image = Image.new("RGB", (width, height), (190, 207, 216))
    draw = ImageDraw.Draw(image)
    for x in range(0, width, 12):
        shade = 135 + ((x * 11) % 70)
        draw.rectangle((x, 0, x + rng.randint(4, 10), height), fill=(shade, min(235, shade + 22), min(245, shade + 35)))
    for _ in range(70):
        x = rng.randrange(width)
        y = rng.randrange(height)
        draw.ellipse((x, y, x + rng.randint(4, 14), y + rng.randint(4, 14)), fill=(rng.randrange(110, 205), rng.randrange(130, 210), rng.randrange(145, 220)))
    return image


def slider_sample(out_dir: Path, index: int, seed: int, difficulty: str) -> dict[str, Any]:
    rng = random.Random(seed)
    width, height = 330, 170
    gap_w = rng.randint(34, 42)
    gap_h = rng.randint(34, 42)
    gap_x = rng.randint(88, 250)
    gap_y = rng.randint(38, 96)
    image = textured_background(width, height, rng)
    draw = ImageDraw.Draw(image, "RGBA")
    transform = ["background_texture", "gap_edge_noise", "shadow"]
    if difficulty == "easy":
        fill = (255, 255, 255, 245)
        outline = (30, 50, 65, 255)
    elif difficulty == "medium":
        fill = (238, 244, 246, 210)
        outline = (65, 90, 105, 255)
        transform.append("alpha_interference")
    else:
        fill = (210, 224, 232, 175)
        outline = (90, 110, 125, 210)
        transform.extend(["low_contrast_gap", "multi_gap_distractors", "jpeg_compression"])
    draw.rectangle((gap_x + 4, gap_y + 5, gap_x + gap_w + 4, gap_y + gap_h + 5), fill=(30, 30, 30, 35))
    draw.rectangle((gap_x, gap_y, gap_x + gap_w, gap_y + gap_h), fill=fill, outline=outline, width=2)
    distractors = {"easy": 0, "medium": 1, "hard": 3, "adversarial": 5}[difficulty]
    for _ in range(distractors):
        dx = rng.randint(60, 260)
        dy = rng.randint(34, 105)
        if abs(dx - gap_x) < 18:
            dx = max(20, dx - 42)
        draw.rectangle((dx, dy, dx + gap_w, dy + gap_h), fill=(230, 235, 238, 95), outline=(80, 90, 95, 120), width=1)
    if difficulty in {"hard", "adversarial"}:
        image = image.filter(ImageFilter.GaussianBlur(0.35 if difficulty == "hard" else 0.65))
    sample_id = f"slider-{difficulty}-{index:04d}"
    image_path = maybe_jpeg(image, out_dir / f"{sample_id}.png", difficulty)
    label_path = out_dir / f"{sample_id}.json"
    label = base_label(sample_id, "slider-captcha", difficulty, image_path, label_path, seed, transform, {"x": gap_x, "y": gap_y}, index)
    label["bounding_boxes"] = [{"x": gap_x, "y": gap_y, "width": gap_w, "height": gap_h}]
    label["offset"] = {"x": gap_x, "y": gap_y}
    save_label(label_path, label)
    return label


def rotate_sample(out_dir: Path, index: int, seed: int, difficulty: str) -> dict[str, Any]:
    rng = random.Random(seed)
    size = 170
    angle = rng.randint(0, 359)
    image = Image.new("RGB", (size, size), (236, 241, 244))
    draw = ImageDraw.Draw(image, "RGBA")
    cx = size // 2 + (rng.randint(-5, 5) if difficulty in {"hard", "adversarial"} else 0)
    cy = size // 2 + (rng.randint(-5, 5) if difficulty in {"hard", "adversarial"} else 0)
    radius = 55
    transform = ["random_angle", "edge_direction_feature"]
    radians = math.radians(angle)
    end = (cx + int(math.cos(radians) * radius), cy - int(math.sin(radians) * radius))
    draw.ellipse((20, 20, size - 20, size - 20), outline=(115, 130, 140, 255), width=2)
    if difficulty in {"hard", "adversarial"}:
        transform.extend(["center_offset", "symmetric_distractor", "blur", "compression"])
        draw.line((cx, cy, cx - (end[0] - cx), cy - (end[1] - cy)), fill=(200, 80, 80, 110), width=6)
    draw.line((cx, cy, end[0], end[1]), fill=(220, 42, 42, 255), width=8)
    draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(55, 65, 75, 255))
    draw.ellipse((end[0] - 8, end[1] - 8, end[0] + 8, end[1] + 8), fill=(220, 42, 42, 255))
    add_noise(draw, rng, size, size, {"easy": 40, "medium": 150, "hard": 350, "adversarial": 700}[difficulty])
    if difficulty in {"hard", "adversarial"}:
        image = image.filter(ImageFilter.GaussianBlur(0.45 if difficulty == "hard" else 0.85))
    sample_id = f"rotate-{difficulty}-{index:04d}"
    image_path = maybe_jpeg(image, out_dir / f"{sample_id}.png", difficulty)
    label_path = out_dir / f"{sample_id}.json"
    label = base_label(sample_id, "rotate-captcha", difficulty, image_path, label_path, seed, transform, angle, index)
    label["angle"] = angle
    label["center"] = {"x": cx, "y": cy}
    save_label(label_path, label)
    return label


def click_sample(out_dir: Path, index: int, seed: int, difficulty: str) -> dict[str, Any]:
    rng = random.Random(seed)
    width, height = 260, 180
    image = Image.new("RGB", (width, height), (238, 241, 243))
    draw = ImageDraw.Draw(image, "RGBA")
    transform = ["target_region_detection", "distractors"]
    target_count = 1 if difficulty == "easy" else 2 if difficulty == "medium" else 3
    boxes = []
    click_points = []
    for i in range(target_count):
        x = rng.randint(25, width - 55)
        y = rng.randint(25, height - 55)
        w = h = rng.randint(22, 32)
        draw.rectangle((x, y, x + w, y + h), fill=(225, 45, 45, 235), outline=(120, 10, 10, 255), width=2)
        boxes.append({"x": x, "y": y, "width": w, "height": h, "target_index": i})
        click_points.append({"x": x + w // 2, "y": y + h // 2, "target_index": i})
    for _ in range({"easy": 3, "medium": 8, "hard": 15, "adversarial": 25}[difficulty]):
        x = rng.randint(5, width - 30)
        y = rng.randint(5, height - 30)
        color = (rng.randrange(40, 170), rng.randrange(80, 180), rng.randrange(160, 230), 150)
        draw.ellipse((x, y, x + rng.randint(12, 28), y + rng.randint(12, 28)), fill=color)
    if difficulty in {"hard", "adversarial"}:
        image = image.filter(ImageFilter.GaussianBlur(0.35 if difficulty == "hard" else 0.65))
        transform.extend(["blur", "color_distractors"])
    sample_id = f"click-{difficulty}-{index:04d}"
    image_path = maybe_jpeg(image, out_dir / f"{sample_id}.png", difficulty)
    label_path = out_dir / f"{sample_id}.json"
    label = base_label(sample_id, "click-captcha", difficulty, image_path, label_path, seed, transform, click_points, index)
    label["bounding_boxes"] = boxes
    label["click_points"] = click_points
    save_label(label_path, label)
    return label


def multi_image_sample(out_dir: Path, index: int, seed: int, difficulty: str) -> dict[str, Any]:
    rng = random.Random(seed)
    cell = 72
    gap = 6
    grid = 3
    width = grid * cell + (grid + 1) * gap
    height = width
    image = Image.new("RGB", (width, height), (235, 238, 240))
    draw = ImageDraw.Draw(image, "RGBA")
    transform = ["grid_layout", "positive_red_square", "distractor_shapes"]
    positive_indices: list[int] = []
    target_count = 2 if difficulty in {"easy", "medium"} else 3
    positive_indices = sorted(rng.sample(range(9), target_count))
    for idx in range(9):
        row, col = divmod(idx, 3)
        x = gap + col * (cell + gap)
        y = gap + row * (cell + gap)
        draw.rectangle((x, y, x + cell, y + cell), fill=(245, 247, 248, 255), outline=(150, 160, 170, 255))
        if idx in positive_indices:
            jitter = {"easy": 2, "medium": 5, "hard": 8, "adversarial": 10}[difficulty]
            tx = x + 18 + rng.randint(-jitter, jitter)
            ty = y + 18 + rng.randint(-jitter, jitter)
            draw.rectangle((tx, ty, tx + 30, ty + 30), fill=(220, 45, 45, 235), outline=(120, 20, 20, 255), width=2)
        else:
            color = (rng.randrange(40, 120), rng.randrange(100, 190), rng.randrange(160, 230), 160)
            draw.ellipse((x + 16, y + 16, x + 52, y + 52), fill=color)
            if difficulty in {"hard", "adversarial"} and rng.random() < 0.35:
                draw.rectangle((x + 22, y + 22, x + 48, y + 48), fill=(205, 75, 75, 110))
    if difficulty in {"hard", "adversarial"}:
        image = image.filter(ImageFilter.GaussianBlur(0.35 if difficulty == "hard" else 0.65))
        transform.extend(["blur", "red_distractors"])
    sample_id = f"multi-image-{difficulty}-{index:04d}"
    image_path = maybe_jpeg(image, out_dir / f"{sample_id}.png", difficulty)
    label_path = out_dir / f"{sample_id}.json"
    answer = {"positive_indices": positive_indices}
    label = base_label(sample_id, "multi-image-select", difficulty, image_path, label_path, seed, transform, answer, index)
    label["positive_indices"] = positive_indices
    label["grid"] = {"rows": 3, "cols": 3, "cell": cell, "gap": gap}
    save_label(label_path, label)
    return label


def generate(args: argparse.Namespace) -> dict[str, Any]:
    run_id = args.run_id or default_run_id()
    root = Path(args.output_root) / "raw" / "captcha-vision-lab" / run_id
    dataset_root = root / "dataset"
    ensure_dir(dataset_root)
    samples: list[dict[str, Any]] = []
    generators = {
        "text-captcha": text_sample,
        "slider-captcha": slider_sample,
        "rotate-captcha": rotate_sample,
        "click-captcha": click_sample,
        "multi-image-select": multi_image_sample,
    }
    for challenge_type in args.types:
        for difficulty in args.difficulties:
            out_dir = dataset_root / challenge_type / difficulty
            ensure_dir(out_dir)
            count = args.adversarial_count if difficulty == "adversarial" else args.count
            for index in range(count):
                seed = args.seed + index + (10000 * (CHALLENGE_TYPES.index(challenge_type) + 1)) + (100000 * DIFFICULTIES.index(difficulty))
                samples.append(generators[challenge_type](out_dir, index, seed, difficulty))
    manifest = {
        "run_id": run_id,
        "generated_at": utc_now(),
        "generator_version": GENERATOR_VERSION,
        "challenge_types": list(args.types),
        "difficulties": list(args.difficulties),
        "count_per_type_difficulty": args.count,
        "adversarial_count_per_type": args.adversarial_count,
        "sample_count": len(samples),
        "synthetic": True,
        "authorized_sample": False,
        "source_scope": "localhost_synthetic",
        "leakage_policy": {
            "solver_must_not_read": ["label", "DOM", "query_param", "metadata_answer"],
            "action_replay_may_initialize_expected_answer": True,
            "solver_prediction_source_required": "challenge_image",
        },
        "samples": samples,
    }
    manifest_path = root / "dataset-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": run_id, "manifest_path": str(manifest_path), "sample_count": len(samples)}, ensure_ascii=False, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate hardened synthetic CAPTCHA vision dataset")
    parser.add_argument("--output-root", default="public-range-evidence")
    parser.add_argument("--run-id")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--adversarial-count", type=int, default=30)
    parser.add_argument("--types", nargs="+", default=list(CHALLENGE_TYPES), choices=CHALLENGE_TYPES)
    parser.add_argument("--difficulties", nargs="+", default=["easy", "medium", "hard"], choices=DIFFICULTIES)
    parser.add_argument("--seed", type=int, default=20260630)
    args = parser.parse_args()
    generate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
