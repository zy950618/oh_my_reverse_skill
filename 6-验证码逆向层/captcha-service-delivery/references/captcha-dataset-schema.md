# CAPTCHA dataset schema

Version: 0.1.0

The dataset schema tracks provenance, splits, labels, and safety boundaries for
local CAPTCHA model work. Datasets may be synthetic, public lab data, or
explicitly authorized owned-target captures. They must not contain production
tokens, user identifiers, cookies, or raw provider secrets.

## Dataset manifest

```json
{
  "manifest_type": "captcha_dataset",
  "schema_version": "0.1.0",
  "dataset_id": "captcha-model-lab-sample",
  "license_scope": "authorized_public_lab",
  "created_at": "2026-07-01T00:00:00Z",
  "label_schema": "captcha_action_schema@0.1.0",
  "splits": {"train": 1, "validation": 1, "test": 1},
  "samples": [
    {
      "sample_id": "sample-slider-001",
      "split": "train",
      "provider": "custom",
      "challenge_type": "slider",
      "image_path": "../samples/images/sample-slider-001.ppm",
      "label_path": "../samples/labels/sample-slider-001.json",
      "provenance": {
        "source": "local_synthetic",
        "authorization": "owned_lab",
        "redaction": "no_tokens_no_user_data"
      }
    }
  ]
}
```

## Label record

```json
{
  "sample_id": "sample-slider-001",
  "challenge_type": "slider",
  "provider": "custom",
  "ground_truth": {
    "target_offset_css_px": 135,
    "success_condition": "drag_handle_to_gap"
  },
  "actions": [
    {"kind": "pointer_down", "x": 61, "y": 330, "time_ms": 0},
    {"kind": "pointer_move", "x": 196, "y": 330, "time_ms": 420},
    {"kind": "pointer_up", "x": 196, "y": 330, "time_ms": 520}
  ]
}
```

## Rules

- Each sample has a split, provider, challenge type, image path, label path, and
  provenance block.
- Splits are counted in the manifest and must match the sample records.
- Manual labels require two-reviewer agreement or an explicit adjudication
  note when used for benchmark claims.
- Dataset evidence is local model evidence only. It does not prove provider or
  business API acceptance.
