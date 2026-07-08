#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "fingerprint" / "validate_browser_context_isolation.py"), run_name="__main__")
