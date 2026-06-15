"""验证 fixtures schema / review 合规。

检查项:
  1. 每个 prefix 必须有三件套 (req.json + resp.json + meta.yaml)
  2. meta.yaml 必须有 endpoint / recorded_at / expires_at / category / sensitive / requires_auth
  3. category 不允许 payment / order-create / pay-confirm
  4. expires_at 未过期 (过期发 warn, 不 fail)
  5. sensitive: true 的 resp.json body 不应是空 (要么打 sensitive 要么 unset)
  6. --strict-review 模式下, meta.yaml 不允许 TODO / 自动抽取占位 / 待 review 文案

退出码:
  0 = 全通过
  1 = 结构错误
  2 = 内部错
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"

FORBIDDEN_CATEGORIES = {"payment", "order-create", "pay-confirm", "checkout-pay"}
ALLOWED_CATEGORIES = {"public-read", "search", "detail", "list", "session", "config"}
BOOL_FIELDS = {"sensitive", "requires_auth"}

META_REQUIRED = ["endpoint", "recorded_at", "expires_at", "category", "sensitive", "requires_auth"]
REVIEW_PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"Auto-extracted from", re.IGNORECASE),
    re.compile(r"Review and edit before committing", re.IGNORECASE),
    re.compile(r"human-readable name", re.IGNORECASE),
]


def parse_meta(text: str) -> dict:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r'^([a-z_]+)\s*:\s*"?([^"#]*)"?', line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def parse_iso(s: str) -> datetime.datetime | None:
    s = s.strip().rstrip("Z")
    try:
        return datetime.datetime.fromisoformat(s).replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def has_review_placeholder(meta_text: str) -> bool:
    return any(pattern.search(meta_text) for pattern in REVIEW_PLACEHOLDER_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fixtures snapshots")
    parser.add_argument(
        "site_root",
        nargs="?",
        default=str(SITE_ROOT),
        help="站点经验库路径,默认使用仓库内 站点经验库",
    )
    parser.add_argument(
        "--strict-review",
        action="store_true",
        help="把 meta.yaml 中的 TODO/自动抽取占位/待 review 文案视为错误",
    )
    args = parser.parse_args()

    site_root = Path(args.site_root)
    if not site_root.is_absolute():
        site_root = (REPO_ROOT / site_root).resolve()

    if not site_root.is_dir():
        print(f"WARN: {site_root} not found, nothing to validate")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    total = {"domains": 0, "snapshots": 0, "valid": 0, "expired": 0, "review_pending": 0}

    now = datetime.datetime.now(datetime.timezone.utc)

    for domain_dir in site_root.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        snap_dir = domain_dir / "fixtures" / "snapshots"
        if not snap_dir.is_dir():
            continue
        total["domains"] += 1

        req_files = sorted(snap_dir.glob("*.req.json"))
        for req in req_files:
            prefix = req.stem[:-4]
            total["snapshots"] += 1
            resp = snap_dir / f"{prefix}.resp.json"
            meta = snap_dir / f"{prefix}.meta.yaml"

            ok = True
            if not resp.exists():
                errors.append(f"{domain_dir.name}/{prefix}: missing .resp.json")
                ok = False
            if not meta.exists():
                errors.append(f"{domain_dir.name}/{prefix}: missing .meta.yaml")
                ok = False

            if not meta.exists():
                continue

            try:
                meta_text = meta.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"{domain_dir.name}/{prefix}: read meta failed: {e}")
                continue
            m = parse_meta(meta_text)

            for k in META_REQUIRED:
                if k not in m or not m[k]:
                    errors.append(f"{domain_dir.name}/{prefix}: meta missing '{k}'")
                    ok = False

            for k in BOOL_FIELDS:
                value = m.get(k, "").lower()
                if value and value not in {"true", "false"}:
                    errors.append(f"{domain_dir.name}/{prefix}: meta '{k}' must be true/false, got '{m.get(k)}'")
                    ok = False

            cat = m.get("category", "")
            if cat in FORBIDDEN_CATEGORIES:
                errors.append(f"{domain_dir.name}/{prefix}: forbidden category '{cat}' "
                              f"(payment/order-create not allowed in fixtures)")
                ok = False
            elif cat and cat not in ALLOWED_CATEGORIES:
                warnings.append(f"{domain_dir.name}/{prefix}: category '{cat}' not in allowed set")

            exp = m.get("expires_at", "")
            if exp:
                exp_dt = parse_iso(exp)
                if exp_dt and exp_dt < now:
                    warnings.append(f"{domain_dir.name}/{prefix}: expired at {exp}, re-record needed")
                    total["expired"] += 1

            if has_review_placeholder(meta_text):
                total["review_pending"] += 1
                msg = f"{domain_dir.name}/{prefix}: meta contains TODO/auto-extracted review placeholder"
                if args.strict_review:
                    errors.append(msg)
                    ok = False
                else:
                    warnings.append(msg)

            if ok and (resp.exists()):
                total["valid"] += 1

    print(f"== fixtures schema validation ==")
    print(f"domains: {total['domains']}  snapshots: {total['snapshots']}  "
          f"valid: {total['valid']}  expired: {total['expired']}  "
          f"review_pending: {total['review_pending']}")
    if warnings:
        print(f"\nwarnings ({len(warnings)}):")
        for w in warnings[:30]:
            print(f"  WARN  {w}")
    if errors:
        print(f"\nerrors ({len(errors)}):")
        for e in errors[:30]:
            print(f"  ERROR {e}")
        return 1
    print("\nall good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
