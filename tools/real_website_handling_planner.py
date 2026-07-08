#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "web_h5" / "real_website_handling_planner.py"), run_name="__main__")
