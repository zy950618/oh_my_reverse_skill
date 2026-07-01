from __future__ import annotations

import re
from pathlib import Path


DEFAULT_DIMENSIONS = {
    "structure": 25,
    "operational": 25,
    "consistency": 30,
    "drift": 20,
}

DEFAULT_LAYER_THRESHOLDS = {
    "1-业务流程层": 70,
    "2-JS逆向工具层": 15,
    "4-通用规范层": 15,
    "5-沉淀工具层": 70,
    "6-验证码逆向层": 70,
    "7-指纹风控层": 70,
}

DEFAULT_LAYER_GATE_MODES = {
    "1-业务流程层": "active",
    "2-JS逆向工具层": "active",
    "4-通用规范层": "active",
    "5-沉淀工具层": "active",
    "6-验证码逆向层": "active",
    "7-指纹风控层": "advisory",
}


def _config_path(repo_root: Path) -> Path:
    return repo_root / "99-SKILLS治理" / "skill-score-rubric.yaml"


def load_skill_score_config(repo_root: Path) -> dict:
    """Read the repository scoring rubric.

    This intentionally parses only the simple YAML shapes used by
    99-SKILLS治理/skill-score-rubric.yaml, avoiding a PyYAML dependency.
    """
    path = _config_path(repo_root)
    config = {
        "path": str(path),
        "scoring_dimensions": dict(DEFAULT_DIMENSIONS),
        "layer_thresholds": dict(DEFAULT_LAYER_THRESHOLDS),
        "layer_gate_modes": dict(DEFAULT_LAYER_GATE_MODES),
        "ci_score_files": [f"{layer}.json" for layer in DEFAULT_LAYER_THRESHOLDS],
    }
    if not path.is_file():
        return config

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    section: str | None = None
    current_dimension: str | None = None
    dimensions: dict[str, int] = {}
    thresholds: dict[str, int] = {}
    modes: dict[str, str] = {}
    score_files: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            current_dimension = None
            continue

        if section == "scoring_dimensions":
            dim_match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
            if dim_match:
                current_dimension = dim_match.group(1)
                continue
            points_match = re.match(r"^    points:\s*(\d+)\s*$", line)
            if current_dimension and points_match:
                dimensions[current_dimension] = int(points_match.group(1))
                continue

        if section == "layer_thresholds":
            match = re.match(r'^  "?([^":]+)"?:\s*(\d+)\s*$', line)
            if match:
                thresholds[match.group(1)] = int(match.group(2))
                continue

        if section == "layer_gate_modes":
            match = re.match(r'^  "?([^":]+)"?:\s*([A-Za-z_-]+)\s*$', line)
            if match:
                modes[match.group(1)] = match.group(2)
                continue

        if section == "ci_score_files":
            match = re.match(r'^  -\s*"?([^"]+)"?\s*$', line)
            if match:
                score_files.append(match.group(1))

    if dimensions:
        config["scoring_dimensions"] = dimensions
    if thresholds:
        config["layer_thresholds"] = thresholds
    if modes:
        config["layer_gate_modes"] = modes
    if score_files:
        config["ci_score_files"] = score_files
    return config
