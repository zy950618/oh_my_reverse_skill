#!/usr/bin/env python3
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "evidence" / "validate_business_data_assertions.py"), run_name="__main__")
