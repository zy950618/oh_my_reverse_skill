#!/usr/bin/env python3
"""List local CAPTCHA solver registry entries."""
from __future__ import annotations
import json
REGISTRY = {
    "text-captcha": "threshold_template_text_baseline",
    "slider-captcha": "connected_component_or_edge_brightness_gap_scan",
    "rotate-captcha": "red_edge_orientation_baseline",
    "click-captcha": "red_component_click_baseline",
}
if __name__ == "__main__":
    print(json.dumps({"status": "PASS", "registry": REGISTRY}, indent=2))

