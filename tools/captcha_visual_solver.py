#!/usr/bin/env python3
"""Compatibility wrapper for visual baseline inference."""
from __future__ import annotations
import runpy
if __name__ == "__main__":
    runpy.run_path("tools/captcha_vision_baseline_solver.py", run_name="__main__")

