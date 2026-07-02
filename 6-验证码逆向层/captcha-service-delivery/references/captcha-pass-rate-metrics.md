# CAPTCHA pass-rate metrics

Version: 0.1.0

Pass-rate reporting separates local action replay success from real provider or
business API acceptance. Local replay can validate the model-to-action contract;
it does not prove third-party CAPTCHA automation.

## Required metrics

```json
{
  "manifest_type": "captcha_pass_rate_report",
  "schema_version": "0.1.0",
  "run_id": "passrate-20260701-sample",
  "attempts": 3,
  "passes": 3,
  "pass_rate": 1.0,
  "confidence_interval": {"method": "wilson", "lower": 0.4385, "upper": 1.0},
  "buckets": [
    {
      "provider": "custom",
      "challenge_type": "slider",
      "attempts": 3,
      "passes": 3,
      "pass_rate": 1.0
    }
  ],
  "negative_controls": [
    {"name": "wrong_offset", "attempts": 1, "expected": "reject", "observed": "reject"}
  ],
  "capability_boundary": {
    "evidence_scope": "local_lab",
    "third_party_positive_claim": false
  }
}
```

## Rules

- Pass rate is `passes / attempts`; do not report a rounded value that changes
  the result.
- Include negative controls for stale token, wrong action, wrong session, or
  wrong target when those states exist.
- Bucket by provider and challenge type; aggregate-only results are not enough.
- Use `business_api_pass_rate` only when the final protected business endpoint
  was verified and repeat-verified.
