#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "js_runtime" / "js_page_runtime_parity_runner.py"), run_name="__main__")
