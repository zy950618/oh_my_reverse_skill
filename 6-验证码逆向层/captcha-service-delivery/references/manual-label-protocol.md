# Manual label protocol

Version: 0.1.0

Manual labels are allowed only for authorized local or owned-target datasets.
The protocol records how labels were produced and reviewed without storing
secrets or personal data.

## Label workflow

1. Redact sample: remove tokens, user identifiers, cookies, and provider
   payloads.
2. Assign label task: challenge type, coordinate space, viewport, and expected
   output schema.
3. First labeler writes ground truth and action sequence.
4. Second labeler reviews the geometry and action timing.
5. Adjudicate disagreement if coordinates differ beyond the configured
   tolerance.
6. Save final label with reviewer ids or anonymized reviewer roles.

## Required label metadata

```json
{
  "label_protocol": {
    "source_authorization": "owned_lab",
    "redaction": "no_tokens_no_user_data",
    "review": {
      "labelers": 2,
      "agreement": "accepted",
      "tolerance_css_px": 3
    }
  }
}
```

## Rules

- Use image coordinates only for model training and action schema coordinates
  for replay labels.
- Keep disagreement samples as failure evidence instead of deleting them.
- Do not use manual labels from unauthorized third-party challenges.
