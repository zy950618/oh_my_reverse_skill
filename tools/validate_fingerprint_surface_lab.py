#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "fingerprint" / "validate_fingerprint_surface_lab.py"), run_name="__main__")
