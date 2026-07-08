from pathlib import Path
import importlib.util

_impl_path = Path(__file__).resolve().parent / "governance" / "skill_score_config.py"
_spec = importlib.util.spec_from_file_location("tools.governance.skill_score_config", _impl_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load skill score config implementation: {_impl_path}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

load_skill_score_config = _module.load_skill_score_config
