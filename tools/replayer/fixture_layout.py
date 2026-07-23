#!/usr/bin/env python3
"""Select the single fixture layout used by active replayer tools."""
from pathlib import Path


def select_fixture_layout(fixtures_dir: Path) -> tuple[Path, Path]:
    """Return ``(selected_root, selected_root / "snapshots")``.

    An existing active directory always wins.  Its contents are deliberately
    not considered, so a damaged or empty active layout cannot fall back to
    legacy or historical fixtures.
    """
    active_root = fixtures_dir / "active"
    selected_root = active_root if active_root.is_dir() else fixtures_dir
    return selected_root, selected_root / "snapshots"
