#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "fingerprint" / "fingerprint_profile_consistency_check.py"), run_name="__main__")
