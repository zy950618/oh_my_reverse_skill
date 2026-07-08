#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "web_h5" / "verify_delivery.py"), run_name="__main__")
