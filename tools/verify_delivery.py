"""verify_delivery.py: 完成度 6 维自验工具

声明"完成"前 Claude 主动跑。规则源 99-SKILLS治理/08-完成度自评.md。

返回 exit_code: 0 = 通过(或仅跳 1 维) / 2 = 跳 ≥2 维,不许声明完成
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = SCRIPT_DIR.parent
SITE_MEMORY_DIR = "站点经验库"
REVERSE_MEMORY_DIR = "逆向工程经验库"
CAPTCHA_MEMORY_DIR = "验证码经验库"
DELIVERY_CODE_MARKERS = (
    "/delivery_",
    "/delivery-",
    "/delivery/",
    "/adapter/",
    "/api/",
    "/services/",
    "/anti_bot/",
    "/crypto/",
    "/reverse/",
)
SUCCESS_DELIVERY_STATUSES = (
    "success_browserless_verified",
    "success_verified",
    "complete",
)

# 与 08-完成度自评.md 一致的窗口:近 1h
RECENT_WINDOW_SEC = 3600
# 集成层 mtime 容差:transcript mtime - 7200 秒之后算"任务期间"
INTEGRATION_MTIME_TOLERANCE_SEC = 7200

# Regression 关键词
REGRESSION_MARKERS = (
    "score_skills",
    "ci_gate",
    "pytest",
    "测试通过",
    "test pass",
)

# Honesty 关键词(在 transcript 文本末尾 3000 字符内扫)
HONESTY_MARKERS = (
    "没验证",
    "未验证",
    "not verified",
    "未在干净环境",
    "blockers",
    "局限",
)

# Cleanup 关键词
CLEANUP_MARKERS = (
    "cleanup ledger",
    "清理账本",
    "delivery-cleanup",
    "encryption-algorithm-graph",
    "加密算法图",
    "临时测试文件",
    "废代码",
    "废注释",
)


# ---------------------------------------------------------------------------
# transcript 定位与解析
# ---------------------------------------------------------------------------

def find_latest_transcript() -> Path | None:
    """从 ~/.claude/projects/ 找最近 mtime 的 .jsonl"""
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return None
    candidates: list[Path] = []
    for p in base.rglob("*.jsonl"):
        try:
            candidates.append(p)
        except Exception:
            continue
    if not candidates:
        return None
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        return None


def load_transcript(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    events: list[dict] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return events
    return events


def event_ts(ev: dict) -> float | None:
    """从一条 transcript 事件里取 unix 时间戳(秒)"""
    ts = ev.get("timestamp") or ev.get("ts")
    if not ts:
        return None
    if isinstance(ts, (int, float)):
        # 毫秒兜底
        return float(ts) / 1000.0 if ts > 10_000_000_000 else float(ts)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None
    return None


def iter_content_blocks(events: list[dict]):
    """遍历 (event_ts, block) 元组,只产出 dict 类型的 content block"""
    for ev in events:
        ts = event_ts(ev)
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    yield ts, c, ev


def extract_text(events: list[dict]) -> str:
    """抽 transcript 全文(text / tool_use input / tool_result content)"""
    parts: list[str] = []
    for _, c, _ev in iter_content_blocks(events):
        t = c.get("type")
        if t == "text":
            parts.append(str(c.get("text", "")))
        elif t == "tool_use":
            ti = c.get("input")
            if isinstance(ti, dict):
                for v in ti.values():
                    if isinstance(v, str):
                        parts.append(v)
        elif t == "tool_result":
            r = c.get("content")
            if isinstance(r, str):
                parts.append(r)
            elif isinstance(r, list):
                for rr in r:
                    if isinstance(rr, dict) and rr.get("type") == "text":
                        parts.append(str(rr.get("text", "")))
    return "\n".join(parts)


def transcript_mtime(path: Path | None) -> float:
    """transcript 文件 mtime;找不到就用 now"""
    if path is not None:
        try:
            return path.stat().st_mtime
        except Exception:
            pass
    return time.time()


# ---------------------------------------------------------------------------
# 6 维检查
# ---------------------------------------------------------------------------

def check_code(events: list[dict], now: float, blockers: list[str]) -> int:
    """1. Code: 近 1h 有成功的 bash tool_use(对应 tool_result 不是 is_error)"""
    # 第一遍:收集近 1h 的 bash tool_use_id
    bash_ids: set[str] = set()
    for ts, c, _ev in iter_content_blocks(events):
        if ts is not None and (now - ts) > RECENT_WINDOW_SEC:
            continue
        if c.get("type") != "tool_use":
            continue
        name = (c.get("name") or "").lower()
        if name in ("bash",):
            tid = c.get("id")
            if isinstance(tid, str):
                bash_ids.add(tid)
    if not bash_ids:
        blockers.append("Code: 近 1h transcript 内未发现 bash tool_use 调用")
        return 0
    # 第二遍:看对应 tool_result 是否非错误
    succeeded = False
    for _ts, c, _ev in iter_content_blocks(events):
        if c.get("type") != "tool_result":
            continue
        tid = c.get("tool_use_id")
        if tid not in bash_ids:
            continue
        if c.get("is_error") is True:
            continue
        succeeded = True
        break
    if not succeeded:
        blockers.append("Code: 近 1h bash tool_use 都没成功的 tool_result")
        return 0
    return 1


def check_docs(events: list[dict], now: float, blockers: list[str]) -> int:
    """2. Docs: 近 1h 有 Read tool_use 且 path 以 .md 结尾"""
    for ts, c, _ev in iter_content_blocks(events):
        if ts is not None and (now - ts) > RECENT_WINDOW_SEC:
            continue
        if c.get("type") != "tool_use":
            continue
        name = (c.get("name") or "").lower()
        if name != "read":
            continue
        ti = c.get("input")
        if not isinstance(ti, dict):
            continue
        # 兼容 file_path / path
        path = ti.get("file_path") or ti.get("path") or ""
        if isinstance(path, str) and path.lower().endswith(".md"):
            return 1
    blockers.append("Docs: 近 1h 内未发现 Read 任何 .md 文件")
    return 0


def check_integration(
    domain: str,
    repo_root: Path,
    transcript_mt: float,
    blockers: list[str],
) -> int:
    """3. Integration: 若 domain != none,看 site/reverse memory 关键文件 mtime"""
    if domain == "none":
        return 1
    site_dir = repo_root / SITE_MEMORY_DIR / domain
    reverse_file = repo_root / REVERSE_MEMORY_DIR / "domains" / domain / "reverse-memory.md"
    if not site_dir.exists() and not reverse_file.exists():
        blockers.append(
            f"Integration: {SITE_MEMORY_DIR}/{domain}/ 与 {REVERSE_MEMORY_DIR}/domains/{domain}/reverse-memory.md 均不存在(还未从 _templates/ 复制?)"
        )
        return 0
    threshold = transcript_mt - INTEGRATION_MTIME_TOLERANCE_SEC
    try:
        if reverse_file.exists() and reverse_file.stat().st_mtime >= threshold:
            return 1
    except Exception:
        pass
    candidates = ("test-log-lessons.md", "known-failures.md")
    updated: list[str] = []
    for name in candidates:
        f = site_dir / name
        try:
            mt = f.stat().st_mtime
        except FileNotFoundError:
            continue
        except Exception:
            continue
        if mt >= threshold:
            updated.append(name)
    if updated:
        return 1
    blockers.append(
        f"Integration: {SITE_MEMORY_DIR}/{domain}/test-log-lessons.md、known-failures.md "
        f"或 {REVERSE_MEMORY_DIR}/domains/{domain}/reverse-memory.md 在本次任务期间无 mtime 更新"
    )
    return 0


def check_regression(text: str, blockers: list[str]) -> int:
    """4. Regression: transcript 全文里出现回归检查关键词"""
    lower = text.lower()
    for kw in REGRESSION_MARKERS:
        if kw.lower() in lower:
            return 1
    blockers.append(
        "Regression: transcript 未出现 score_skills / ci_gate / pytest / 测试通过 等回归动作"
    )
    return 0


def check_honesty(text: str, blockers: list[str]) -> int:
    """5. Honesty: transcript 末尾 3000 字符里出现"没验证 / 局限 / blockers"等"""
    tail = text[-3000:] if len(text) > 3000 else text
    lower = tail.lower()
    for kw in HONESTY_MARKERS:
        if kw.lower() in lower:
            return 1
    blockers.append(
        "Honesty: transcript 末尾 3000 字符内未列出 没验证 / 未验证 / blockers / 局限"
    )
    return 0


def check_cleanup(text: str, blockers: list[str]) -> int:
    """6. Cleanup: transcript 出现清理账本或加密算法图证据。"""
    lower = text.lower()
    for kw in CLEANUP_MARKERS:
        if kw.lower() in lower:
            return 1
    blockers.append(
        "Cleanup: transcript 未出现 cleanup ledger / 清理账本 / encryption-algorithm-graph / 加密算法图 等收尾证据"
    )
    return 0


# ---------------------------------------------------------------------------
# Codex / 本地 workspace 证据模式
# ---------------------------------------------------------------------------

def git_changed_files(repo_root: Path, blockers: list[str]) -> list[str]:
    """读取当前工作区改动列表。Codex 桌面环境没有 Claude transcript 时用作本地证据。"""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--name-only"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:
        blockers.append(f"Workspace: git diff --name-only 执行失败: {e!r}")
        return []
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip()
        blockers.append(f"Workspace: git diff --name-only 返回 {proc.returncode}: {msg}")
        return []
    changed = [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]
    try:
        untracked = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--others", "--exclude-standard"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if untracked.returncode == 0:
            changed.extend(
                line.strip().replace("\\", "/")
                for line in untracked.stdout.splitlines()
                if line.strip()
            )
    except Exception:
        pass
    try:
        ignored_evidence = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--others", "--ignored", "--exclude-standard"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if ignored_evidence.returncode == 0:
            evidence_markers = (
                "delivery-cleanup.md",
                "error-correction-ledger.md",
                "impact-regression.md",
                "knowledge-graph.md",
            )
            changed.extend(
                line.strip().replace("\\", "/")
                for line in ignored_evidence.stdout.splitlines()
                if line.strip() and any(marker in line.replace("\\", "/") for marker in evidence_markers)
            )
    except Exception:
        pass
    return sorted(set(changed))


def check_code_workspace(changed: list[str], blockers: list[str]) -> int:
    """1. Code: 当前工作区存在实际改动。"""
    if changed:
        return 1
    blockers.append("Code: workspace evidence 模式下未发现 git diff 改动")
    return 0


def check_docs_workspace(changed: list[str], blockers: list[str]) -> int:
    """2. Docs: 当前任务改动包含 .md 文档。"""
    if any(path.lower().endswith(".md") for path in changed):
        return 1
    blockers.append("Docs: workspace evidence 模式下 git diff 未包含 .md 文档")
    return 0


def check_regression_workspace(repo_root: Path, now: float, blockers: list[str]) -> int:
    """4. Regression: 近 1h 生成过 Web/H5 层级评分 JSON。"""
    ci_dir = repo_root / ".ci-out"
    expected = (
        "1-业务流程层.json",
        "2-JS逆向工具层.json",
        "4-通用规范层.json",
        "5-沉淀工具层.json",
        "6-验证码逆向层.json",
    )
    missing: list[str] = []
    stale: list[str] = []
    invalid: list[str] = []
    for name in expected:
        path = ci_dir / name
        if not path.is_file():
            missing.append(name)
            continue
        try:
            if now - path.stat().st_mtime > RECENT_WINDOW_SEC:
                stale.append(name)
        except Exception:
            stale.append(name)
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            invalid.append(name)
    if not missing and not stale and not invalid:
        return 1
    blockers.append(
        "Regression: workspace evidence 模式要求近 1h 内生成有效 .ci-out 评分文件; "
        f"missing={missing}, stale={stale}, invalid={invalid}"
    )
    return 0


def check_honesty_workspace(blockers: list[str]) -> int:
    """5. Honesty: 本地模式无法预读最终答复,因此保留为声明项。"""
    blockers.append("Honesty: workspace evidence 模式无法预读最终答复; 最终答复需列出未验证项/局限")
    return 0


def check_cleanup_workspace(changed: list[str], blockers: list[str]) -> int:
    """6. Cleanup: workspace 模式检查是否接入收尾规约或清理/算法图模板。"""
    markers = (
        "99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md",
        "逆向工程经验库/_templates/delivery-cleanup.md",
        "逆向工程经验库/_templates/encryption-algorithm-graph.md",
        "delivery-cleanup.md",
        "encryption-algorithm-graph.md",
    )
    if any(any(marker in path for marker in markers) for path in changed):
        return 1
    blockers.append(
        "Cleanup: workspace evidence 模式未发现 17 收尾规约、delivery-cleanup 或 encryption-algorithm-graph 改动"
    )
    return 0


def check_captcha_completion_gate(domain: str, repo_root: Path, blockers: list[str]) -> dict:
    """CAPTCHA delivery gate: blocked verified/repeat_verified cannot pass as complete.

    This gate intentionally reads the persisted site CAPTCHA memory, because transcript/workspace
    scoring alone can miss the core delivery state.
    """
    result = {
        "applies": False,
        "status": "not_applicable",
        "memory": None,
        "verified": None,
        "repeat_verified": None,
        "success_pointer": None,
    }
    if domain == "none":
        return result

    path = repo_root / CAPTCHA_MEMORY_DIR / "domains" / domain / "captcha-memory.md"
    result["memory"] = str(path)
    if not path.is_file():
        return result

    result["applies"] = True
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception as e:
        blockers.append(f"Captcha gate: 无法读取 {path}: {e!r}")
        result["status"] = "blocked"
        return result

    lower = text.lower()

    def field_value(name: str) -> str | None:
        # YAML-like memory files are simple enough for a conservative line parser.
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith(f"{name.lower()}:"):
                return stripped.split(":", 1)[1].strip().strip("'\"")
        return None

    verified = field_value("verified")
    repeat_verified = field_value("repeat_verified")
    success_pointer = field_value("success_pointer")
    result["verified"] = verified
    result["repeat_verified"] = repeat_verified
    result["success_pointer"] = success_pointer

    blocked_markers = (
        "blocked",
        "manual",
        "unverified",
        "missing",
        "none",
        "todo",
        "unknown",
        "not_applicable",
    )

    bad_fields: list[str] = []
    for name, value in (("verified", verified), ("repeat_verified", repeat_verified)):
        if value is None:
            bad_fields.append(f"{name}=missing")
            continue
        value_lower = value.lower()
        if any(marker in value_lower for marker in blocked_markers):
            bad_fields.append(f"{name}={value}")

    if success_pointer is not None and any(marker in success_pointer.lower() for marker in ("unverified", "unknown", "missing")):
        bad_fields.append(f"success_pointer={success_pointer}")

    if bad_fields:
        blockers.append(
            "Captcha gate: verified/repeat_verified 未完成,不得通过完整交付门槛; "
            + ", ".join(bad_fields)
        )
        result["status"] = "blocked"
        return result

    result["status"] = "complete"
    return result


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _field_value_from_text(text: str, name: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(f"{name.lower()}:"):
            return stripped.split(":", 1)[1].strip().strip("'\"")
    return None


def check_delivery_memory_separation_gate(
    domain: str,
    repo_root: Path,
    changed: list[str],
    blockers: list[str],
) -> dict:
    """Project delivery code must not live in experience memory or feed SKILLS."""
    result = {
        "applies": domain != "none",
        "status": "not_applicable",
        "mixed_delivery_code": [],
        "bad_positive_memory": [],
    }
    if domain == "none":
        return result

    memory_prefixes = (
        f"{SITE_MEMORY_DIR}/{domain}/",
        f"{REVERSE_MEMORY_DIR}/domains/{domain}/",
        f"{CAPTCHA_MEMORY_DIR}/domains/{domain}/",
    )

    mixed: list[str] = []
    for rel in changed:
        normalized = rel.replace("\\", "/")
        if not normalized.startswith(memory_prefixes):
            continue
        lower = normalized.lower()
        if lower.endswith((".py", ".js", ".ts", ".mjs", ".cjs", ".java", ".go", ".rs")) and any(
            marker in lower for marker in DELIVERY_CODE_MARKERS
        ):
            mixed.append(normalized)
    if mixed:
        blockers.append(
            "Delivery separation gate: 项目交付代码混入经验库目录; "
            "交付项目代码不参与 SKILLS,请改为单独交付文件/交付包并只在经验库保留摘要: "
            + ", ".join(mixed[:10])
        )

    bad_positive: list[str] = []
    memory_files = (
        repo_root / SITE_MEMORY_DIR / domain / "site-memory.md",
        repo_root / SITE_MEMORY_DIR / domain / "test-log-lessons.md",
        repo_root / REVERSE_MEMORY_DIR / "domains" / domain / "reverse-memory.md",
        repo_root / CAPTCHA_MEMORY_DIR / "domains" / domain / "captcha-memory.md",
    )
    for path in memory_files:
        if not path.is_file():
            continue
        text = _read_text_safe(path)
        skills_participation = _field_value_from_text(text, "skills_participation")
        delivery_status = _field_value_from_text(text, "delivery_status") or _field_value_from_text(
            text, "completion_status"
        )
        if not skills_participation or skills_participation.lower() != "positive_allowed":
            continue
        if delivery_status is None or delivery_status.lower() not in SUCCESS_DELIVERY_STATUSES:
            bad_positive.append(f"{path}: delivery_status={delivery_status or 'missing'}")

    if bad_positive:
        blockers.append(
            "Delivery separation gate: 非成功经验库不得参与 SKILLS 正向评分; "
            + ", ".join(bad_positive)
        )

    if mixed or bad_positive:
        result["status"] = "blocked"
    else:
        result["status"] = "pass"
    result["mixed_delivery_code"] = mixed
    result["bad_positive_memory"] = bad_positive
    return result


# ---------------------------------------------------------------------------
# 评分 + 输出
# ---------------------------------------------------------------------------

def grade(passed_count: int) -> str:
    table = {6: "10/10", 5: "7/10", 4: "5/10", 3: "3/10", 2: "2/10", 1: "1/10", 0: "0/10"}
    return table.get(passed_count, "0/10")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="完成度 6 维自验工具 (见 99-SKILLS治理/08-完成度自评.md)"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="当前任务相关 domain (如 thaiairways.com); 用 'none' 表示纯工具改动",
    )
    parser.add_argument(
        "--transcript",
        default=None,
        help="transcript .jsonl 路径 (缺省从 ~/.claude/projects/ 找最近)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="仓库根目录 (缺省从脚本路径推断)",
    )
    parser.add_argument(
        "--evidence-mode",
        choices=("auto", "transcript", "workspace"),
        default="auto",
        help="证据来源:auto 优先 transcript,缺失时降级 workspace; transcript 强制 Claude transcript; workspace 强制本地 git/.ci-out 证据",
    )
    args = parser.parse_args()

    domain = (args.domain or "").strip().lower() or "none"
    repo_root = Path(args.repo_root).resolve() if args.repo_root else DEFAULT_REPO_ROOT

    blockers: list[str] = []

    # 定位 transcript
    transcript_path: Path | None = None
    force_transcript = args.evidence_mode == "transcript"
    if args.transcript:
        p = Path(args.transcript)
        if p.exists():
            transcript_path = p
        else:
            blockers.append(f"transcript 路径不存在: {p}")
    else:
        try:
            transcript_path = find_latest_transcript()
            if transcript_path is None:
                if force_transcript:
                    blockers.append("未在 ~/.claude/projects/ 找到 transcript .jsonl")
        except Exception as e:
            if force_transcript:
                blockers.append(f"transcript 自动定位失败: {e!r}")

    # 读 events
    try:
        events = load_transcript(transcript_path)
    except Exception as e:
        blockers.append(f"transcript 解析失败: {e!r}")
        events = []

    try:
        text = extract_text(events) if events else ""
    except Exception as e:
        blockers.append(f"transcript 文本抽取失败: {e!r}")
        text = ""

    now = time.time()
    tmt = transcript_mtime(transcript_path)
    use_workspace_evidence = (
        args.evidence_mode == "workspace"
        or (args.evidence_mode == "auto" and transcript_path is None)
    )

    # 6 维
    scores = {
        "code": 0,
        "docs": 0,
        "integration": 0,
        "regression": 0,
        "honesty": 0,
        "cleanup": 0,
    }
    changed: list[str] = []
    if use_workspace_evidence:
        changed = git_changed_files(repo_root, blockers)
        try:
            scores["code"] = check_code_workspace(changed, blockers)
        except Exception as e:
            blockers.append(f"Code 维度检查异常: {e!r}")
        try:
            scores["docs"] = check_docs_workspace(changed, blockers)
        except Exception as e:
            blockers.append(f"Docs 维度检查异常: {e!r}")
        try:
            scores["integration"] = check_integration(domain, repo_root, tmt, blockers)
        except Exception as e:
            blockers.append(f"Integration 维度检查异常: {e!r}")
        try:
            scores["regression"] = check_regression_workspace(repo_root, now, blockers)
        except Exception as e:
            blockers.append(f"Regression 维度检查异常: {e!r}")
        try:
            scores["honesty"] = check_honesty_workspace(blockers)
        except Exception as e:
            blockers.append(f"Honesty 维度检查异常: {e!r}")
        try:
            scores["cleanup"] = check_cleanup_workspace(changed, blockers)
        except Exception as e:
            blockers.append(f"Cleanup 维度检查异常: {e!r}")
    else:
        try:
            scores["code"] = check_code(events, now, blockers)
        except Exception as e:
            blockers.append(f"Code 维度检查异常: {e!r}")
        try:
            scores["docs"] = check_docs(events, now, blockers)
        except Exception as e:
            blockers.append(f"Docs 维度检查异常: {e!r}")
        try:
            scores["integration"] = check_integration(domain, repo_root, tmt, blockers)
        except Exception as e:
            blockers.append(f"Integration 维度检查异常: {e!r}")
        try:
            scores["regression"] = check_regression(text, blockers)
        except Exception as e:
            blockers.append(f"Regression 维度检查异常: {e!r}")
        try:
            scores["honesty"] = check_honesty(text, blockers)
        except Exception as e:
            blockers.append(f"Honesty 维度检查异常: {e!r}")
        try:
            scores["cleanup"] = check_cleanup(text, blockers)
        except Exception as e:
            blockers.append(f"Cleanup 维度检查异常: {e!r}")

    passed_count = sum(scores.values())
    skipped = 6 - passed_count

    captcha_gate = check_captcha_completion_gate(domain, repo_root, blockers)
    delivery_separation_gate = check_delivery_memory_separation_gate(domain, repo_root, changed, blockers)

    if captcha_gate.get("status") == "blocked" or delivery_separation_gate.get("status") == "blocked":
        exit_code = 2
    elif skipped >= 2:
        exit_code = 2
    else:
        exit_code = 0

    result = {
        "6_dim_self_score": scores,
        "passed_count": passed_count,
        "total": grade(passed_count),
        "blockers": blockers,
        "exit_code": exit_code,
        "meta": {
            "domain": domain,
            "evidence_mode": "workspace" if use_workspace_evidence else "transcript",
            "transcript": str(transcript_path) if transcript_path else None,
            "repo_root": str(repo_root),
            "ts_utc": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        },
        "captcha_completion_gate": captcha_gate,
        "delivery_memory_separation_gate": delivery_separation_gate,
    }

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    try:
        sys.stdout.buffer.write(payload.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
    except AttributeError:
        print(payload)

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        # 兜底:不允许整个工具 crash
        try:
            sys.stderr.write(f"[verify_delivery] fatal: {e!r}\n")
        except Exception:
            pass
        sys.exit(2)
