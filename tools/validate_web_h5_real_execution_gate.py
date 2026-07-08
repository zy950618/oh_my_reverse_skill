#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "web_h5" / "validate_web_h5_real_execution_gate.py"), run_name="__main__")
