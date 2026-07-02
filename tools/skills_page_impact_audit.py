#!/usr/bin/env python3
"""Audit SKILL pages for scoped, evidence-linked capability wording."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SKILL_PAGES = {
    "web-h5-loop-engineering": ROOT / "1-业务流程层" / "web-h5-loop-engineering" / "SKILL.md",
    "authorized-target-adapter": ROOT / "1-业务流程层" / "authorized-target-adapter" / "SKILL.md",
    "js-page-runtime-parity": ROOT / "2-JS逆向工具层" / "js-page-runtime-parity" / "SKILL.md",
    "captcha-service-delivery": ROOT / "6-验证码逆向层" / "captcha-service-delivery" / "SKILL.md",
    "captcha-model-training": ROOT / "6-验证码逆向层" / "captcha-model-training" / "SKILL.md",
    "captcha-visual-recognition-lab": ROOT / "6-验证码逆向层" / "captcha-visual-recognition-lab" / "SKILL.md",
    "captcha-algorithm-benchmark": ROOT / "6-验证码逆向层" / "captcha-algorithm-benchmark" / "SKILL.md",
    "captcha-action-planner": ROOT / "6-验证码逆向层" / "captcha-action-planner" / "SKILL.md",
    "captcha-provider-diagnostics": ROOT / "6-验证码逆向层" / "captcha-provider-diagnostics" / "SKILL.md",
    "browser-fingerprint-surface-lab": ROOT / "7-指纹风控层" / "browser-fingerprint-surface-lab" / "SKILL.md",
    "fingerprint-block-reason-diagnostics": ROOT / "7-指纹风控层" / "fingerprint-block-reason-diagnostics" / "SKILL.md",
}
for extra_name in ("captcha-dataset-flywheel", "captcha-open-source-model-stack", "captcha-model-action-e2e"):
    extra_path = ROOT / "6-验证码逆向层" / extra_name / "SKILL.md"
    if extra_path.is_file():
        SKILL_PAGES[extra_name] = extra_path
FORBIDDEN_CLAIMS = [
    "real third-party captcha capability",
    "fingerprint evasion capability",
    "production waf bypass",
    "stable_positive from single run",
    "universal captcha solving",
]
NEGATION_MARKERS = (
    "not ",
    "cannot ",
    "must not ",
    "do not ",
    "does not ",
    "without ",
    "禁止",
    "不得",
    "不能",
    "不是",
    "不等于",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_negated_claim(lower: str, index: int) -> bool:
    context = lower[max(0, index - 260) : index]
    return any(marker in context for marker in NEGATION_MARKERS)


def contains_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SKILLS page impact")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    modified: list[str] = []
    overclaimed: list[dict[str, Any]] = []
    missing_evidence_links: list[dict[str, Any]] = []
    missing_eval_links: list[dict[str, Any]] = []
    required_downgrades: list[dict[str, Any]] = []
    required_next_training: list[dict[str, Any]] = []
    family_rules: list[str] = []
    leakage_rules: list[str] = []
    website_rules: list[str] = []
    candidate_rules: list[str] = []

    for name, path in SKILL_PAGES.items():
        text = read_text(path)
        if not text:
            missing_evidence_links.append({"skill": name, "reason": "missing SKILL.md"})
            continue
        lower = text.lower()
        if args.run_id in text:
            modified.append(name)
        if args.run_id in text and "public-range-evidence" not in text:
            missing_evidence_links.append({"skill": name, "reason": "run_id present without evidence path"})
        if args.run_id in text and "evals/" not in text:
            missing_eval_links.append({"skill": name, "reason": "run_id present without eval path"})
        for claim in FORBIDDEN_CLAIMS:
            start = 0
            while True:
                idx = lower.find(claim, start)
                if idx < 0:
                    break
                if not is_negated_claim(lower, idx):
                    overclaimed.append({"skill": name, "claim": claim, "index": idx})
                start = idx + len(claim)
        if contains_any(text, ["challenge_family", "family-level", "per-family", "per family", "challenge_type"]):
            family_rules.append(name)
        if contains_any(text, ["solver_input_payload", "solver_input_redactor", "correct_option_index", "hold_time", "public_range_answer_leakage_audit"]):
            leakage_rules.append(name)
        if contains_any(text, ["scope classification", "unknown_third_party", "production_unverified", "authorized_target", "observation_only"]):
            website_rules.append(name)
        if contains_any(text, ["positive_candidate", "positive_verified", "stable_positive"]):
            candidate_rules.append(name)
        if "rotate" in lower and "training_needed" in lower:
            required_next_training.append({"skill": name, "family": "gocaptcha.rotate"})
        if "click" in lower and "training_needed" in lower:
            required_next_training.append({"skill": name, "family": "gocaptcha.click"})
        if "sequence accuracy low" in lower or "low sequence accuracy" in lower:
            required_downgrades.append({"skill": name, "reason": "text OCR remains memory_only until sequence accuracy passes"})

    required_pages = {
        "captcha-provider-diagnostics",
        "captcha-visual-recognition-lab",
        "captcha-action-planner",
        "authorized-target-adapter",
        "fingerprint-block-reason-diagnostics",
        "browser-fingerprint-surface-lab",
        "js-page-runtime-parity",
        "web-h5-loop-engineering",
        "captcha-dataset-flywheel",
        "captcha-open-source-model-stack",
        "captcha-model-action-e2e",
    }
    missing_required = sorted(required_pages - set(modified))
    if missing_required:
        missing_evidence_links.extend({"skill": item, "reason": f"missing run_id {args.run_id}"} for item in missing_required)

    status = "PASS" if not overclaimed and not missing_required and family_rules and leakage_rules and website_rules else "REVIEW_REQUIRED"
    report = {
        "tool": "skills_page_impact_audit",
        "run_id": args.run_id,
        "modified_skill_pages": modified,
        "new_real_experience_rules": candidate_rules,
        "family_level_capabilities": family_rules,
        "overclaimed_capabilities": overclaimed,
        "missing_evidence_links": missing_evidence_links,
        "missing_eval_links": missing_eval_links,
        "leakage_sensitive_rules": leakage_rules,
        "real_website_handling_rules": website_rules,
        "required_downgrades": required_downgrades,
        "required_next_training": required_next_training,
        "final_status": status,
    }
    out = ROOT / "public-range-evidence" / "raw" / "skills-page-impact-audit" / args.run_id / "skills-page-impact-audit.json"
    write_json(out, report)
    print(json.dumps({"status": status, "run_id": args.run_id, "report_path": str(out)}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
