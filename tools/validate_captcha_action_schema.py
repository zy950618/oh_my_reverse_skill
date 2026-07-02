#!/usr/bin/env python3
"""Validate a CAPTCHA action schema manifest using only the Python stdlib."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ACTION_KINDS = {
    "pointer_down",
    "pointer_move",
    "pointer_up",
    "tap",
    "click",
    "wait",
    "drag_start",
    "drag_move",
    "drag_end",
}
DEFAULT_MANIFEST = Path("public-range-evidence/captcha-model-lab/manifests/action_manifest.json")


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail("manifest root must be an object")
    return data


def require_mapping(data: dict, key: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        fail(f"{key} must be an object")
    return value


def require_list(data: dict, key: str) -> list:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key} must be a non-empty list")
    return value


def require_number(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{key} must be a number")
    return float(value)


def validate_actions(manifest: dict) -> None:
    viewport = require_mapping(manifest, "viewport")
    width = require_number(viewport, "width")
    height = require_number(viewport, "height")
    if width <= 0 or height <= 0:
        fail("viewport width and height must be positive")
    if require_number(viewport, "device_pixel_ratio") <= 0:
        fail("viewport.device_pixel_ratio must be positive")

    actions = require_list(manifest, "actions")
    previous_time = -1.0
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            fail(f"actions[{index}] must be an object")
        kind = action.get("kind")
        if kind not in ACTION_KINDS:
            fail(f"actions[{index}].kind is unsupported: {kind!r}")
        time_ms = require_number(action, "time_ms")
        if time_ms < previous_time:
            fail(f"actions[{index}].time_ms is not monotonic")
        previous_time = time_ms
        if kind != "wait":
            x = require_number(action, "x")
            y = require_number(action, "y")
            if not (0 <= x <= width and 0 <= y <= height):
                fail(f"actions[{index}] coordinate is outside viewport")


def validate_state_machine(manifest: dict) -> None:
    machine = require_mapping(manifest, "challenge_state_machine")
    states = require_list(machine, "states")
    initial_state = machine.get("initial_state")
    if initial_state not in states:
        fail("challenge_state_machine.initial_state must be in states")
    terminal_states = require_list(machine, "terminal_states")
    for state in terminal_states:
        if state not in states:
            fail(f"terminal state {state!r} is missing from states")
    transitions = require_list(machine, "transitions")
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            fail(f"transitions[{index}] must be an object")
        if transition.get("from") not in states:
            fail(f"transitions[{index}].from is not a known state")
        if transition.get("to") not in states:
            fail(f"transitions[{index}].to is not a known state")
        if not transition.get("event"):
            fail(f"transitions[{index}].event is required")


def validate_manifest(path: Path) -> None:
    manifest = load_json(path)
    if manifest.get("manifest_type") != "captcha_action_schema":
        fail("manifest_type must be captcha_action_schema")
    for key in ("schema_version", "challenge_type", "provider"):
        if not manifest.get(key):
            fail(f"{key} is required")

    coordinate_space = require_mapping(manifest, "coordinate_space")
    for key in ("origin", "units", "rounding"):
        if not coordinate_space.get(key):
            fail(f"coordinate_space.{key} is required")
    require_mapping(manifest, "target_element")
    require_mapping(manifest, "mobile_h5_transform")
    require_list(manifest, "provider_detection_signals")
    validate_actions(manifest)
    validate_state_machine(manifest)

    boundary = require_mapping(manifest, "capability_boundary")
    if boundary.get("third_party_positive_claim") is not False:
        fail("capability_boundary.third_party_positive_claim must be false for lab action evidence")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        validate_manifest(args.manifest)
    except Exception as exc:
        print(f"FAIL {args.manifest}: {exc}", file=sys.stderr)
        return 1
    print(f"PASS {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
