#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "site_memory" / "backfill_from_site_memory.py"), run_name="__main__")
