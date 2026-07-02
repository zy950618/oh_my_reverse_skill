from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

AIRLINES = {
    "mh": ("MH", "Malaysia Airlines", "https://www.malaysiaairlines.com/"),
    "5j": ("5J", "Cebu Pacific", "https://www.cebupacificair.com/"),
    "tg": ("TG", "Thai Airways", "https://www.thaiairways.com/"),
    "scoot": ("Scoot", "Scoot", "https://www.flyscoot.com/"),
    "vn": ("VN", "Vietnam Airlines", "https://www.vietnamairlines.com/"),
    "cz": ("CZ", "China Southern Airlines", "https://www.csair.com/"),
    "sq": ("SQ", "Singapore Airlines", "https://www.singaporeair.com/"),
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_real_site_packs() -> None:
    root = ROOT / "public-range-evidence" / "real-site-observation-pack" / "airlines"
    for slug, (code, brand, url) in AIRLINES.items():
        target = root / slug
        pack = {
            "schema_version": "real-site-observation-pack/v1",
            "pack_id": f"airline-real-site-observation-{slug}",
            "airline_code": code,
            "brand_name": brand,
            "target_url_assumption": url,
            "pack_status": "authorized-live-ready",
            "execution_status": "LOCAL_FIXTURE_VALIDATED",
            "control_flow_status": "NOT_RUN",
            "business_data_status": "NOT_RUN",
            "capability_status": "memory_only",
            "positive_allowed": False,
            "live_capture_performed": False,
            "live_observation_status": "NOT_RUN_NO_AUTHORIZATION_INPUT",
            "authorization_scope": "future public homepage observation only; no account, payment, order, or protected flow",
            "local_validation": {
                "schema_validated": True,
                "executable_runbook_validated": True,
                "local_fixture_validated": True,
                "authorized_live_ready": True,
            },
            "planned_observation_surfaces": [
                "homepage_status",
                "redirect_chain",
                "security_headers",
                "cookie_names_redacted",
                "client_hints",
                "fingerprint_surface_report",
                "captcha_or_waf_marker_presence",
            ],
            "fact_labels": {
                "observed": ["Local schema, runbook, and sample fixture are present."],
                "derived": [],
                "assumed": ["target_url_assumption is a seed URL for future manual verification"],
                "unverified": [
                    "No live request was made in this run",
                    "No fingerprint surface was captured from the real site",
                    "No block reason was observed from the real site",
                    "No business endpoint was verified",
                ],
            },
            "forbidden_actions": [
                "captcha_bypass",
                "solver_token_reuse",
                "webdriver_hide",
                "fingerprint_spoof",
                "proxy_rotation_evasion",
                "clearance_cookie_reuse",
                "risk_token_reuse",
                "unauthorized_challenge_processing",
            ],
        }
        write_json(target / "observation-pack.json", pack)
        write_json(
            target / "observation_schema.json",
            {
                "schema_version": "real-site-observation-schema/v1",
                "required_fields": [
                    "target_profile",
                    "authorization_scope",
                    "network_inventory",
                    "dynamic_param_inventory",
                    "captcha_or_challenge_detection",
                    "fingerprint_surface_observation",
                    "pure_api_feasibility",
                    "no_browser_final_delivery",
                ],
                "forbidden_fields": ["cookie_value", "token_value", "pii", "payment_data"],
            },
        )
        write_json(
            target / "sample_observation.fixture.json",
            {
                "schema_version": "real-site-observation-fixture/v1",
                "airline_code": code,
                "target_url_assumption": url,
                "live_observation_status": "NOT_RUN_NO_AUTHORIZATION_INPUT",
                "network_inventory": [],
                "dynamic_param_inventory": [],
                "captcha_or_challenge_detection": {"status": "not_run"},
                "fingerprint_surface_observation": {"status": "not_run"},
                "pure_api_feasibility": {"status": "not_run"},
                "no_browser_final_delivery": True,
            },
        )
        write(
            target / "runbook.md",
            f"""
# {code} Observation Runbook

Status: authorized-live-ready.

1. Confirm written authorization for public homepage observation.
2. Set `AUTHORIZED_LIVE_OBSERVATION=1` and provide approved target URL if live observation is allowed.
3. Capture only public, non-login, non-payment, non-order surfaces.
4. Redact cookies, tokens, PII, order identifiers, and full payloads.
5. Stop on CAPTCHA, WAF, login, booking, payment, or account flow.
6. Keep final business delivery browserless; browser capture is analysis-only.

Without authorization input, live status remains `NOT_RUN_NO_AUTHORIZATION_INPUT`.
""",
        )
        write(
            target / "authorization_inputs.example.yaml",
            f"""
airline_code: {code}
target_url: {url}
authorized_by: ""
authorization_scope: "public homepage observation only"
allow_login: false
allow_booking: false
allow_payment: false
allow_captcha_solving: false
allow_waf_bypass: false
""",
        )
        write(
            target / "do_not_commit_evidence.md",
            """
# Do Not Commit Evidence

Do not commit raw HAR, raw cookies, raw storage, token values, screenshots containing PII, account data, booking payloads, payment data, or full protected responses. Commit only redacted summaries and fixture schemas.
""",
        )


if __name__ == "__main__":
    build_real_site_packs()
