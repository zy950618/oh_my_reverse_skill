"""从 CI 评分输出 (.ci-out/*.json) 追加一段本地历史快照。

CI 在 schedule 触发时调用:
    python tools/append_drift_history.py .ci-out metrics/drift-history.md $(date -u +%Y-%m-%d)

`metrics/` is ignored by git; CI should upload the generated history as an
artifact instead of committing it back to the repository.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: append_drift_history.py <ci-out-dir> <history-file> <date>", file=sys.stderr)
        return 2

    ci_dir = Path(sys.argv[1])
    history = Path(sys.argv[2])
    date = sys.argv[3]

    if not ci_dir.exists():
        print(f"ci-out dir not found: {ci_dir}", file=sys.stderr)
        return 1

    history.parent.mkdir(parents=True, exist_ok=True)
    if not history.exists():
        history.write_text("# 仓库漂移历史\n\n", encoding="utf-8")

    blocks: list[str] = [f"\n## {date}\n"]
    json_files = sorted(ci_dir.glob("*.json"))
    if not json_files:
        blocks.append("- 无评分数据(CI 评分步骤未产出 JSON)")
    else:
        for f in json_files:
            layer = f.stem.replace("_", "/")
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                blocks.append(f"### {layer}\n- 解析失败:{e}")
                continue
            overall = data.get("overall", {})
            blocks.append(f"### {layer}")
            blocks.append(
                f"- 均分: total={overall.get('total','?')} "
                f"(s={overall.get('structure','?')}/"
                f"o={overall.get('operational','?')}/"
                f"d={overall.get('drift','?')})"
            )
            for s in data.get("skills", []):
                sc = s.get("scores", {})
                blocks.append(
                    f"- `{s.get('skill','?')}` "
                    f"v{s.get('version','?')} "
                    f"total={sc.get('total','?')} "
                    f"(s={sc.get('structure','?')}/"
                    f"o={sc.get('operational','?')}/"
                    f"d={sc.get('drift','?')}) "
                    f"— {s.get('rating','?')}"
                )
            blocks.append("")

    with history.open("a", encoding="utf-8") as f:
        f.write("\n".join(blocks) + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
