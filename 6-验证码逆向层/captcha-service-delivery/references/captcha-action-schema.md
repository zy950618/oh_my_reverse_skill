# CAPTCHA action schema

Version: 0.1.0

This reference defines the portable action output expected from a CAPTCHA
recognition model before any replay layer consumes it. It is a schema for
authorized local labs or explicitly authorized targets. It is not a bypass
claim for third-party managed challenges.

## Required manifest fields

```json
{
  "schema_version": "0.1.0",
  "manifest_type": "captcha_action_schema",
  "challenge_type": "slider | click_select | rotate | text | icon_select",
  "provider": "recaptcha | hcaptcha | turnstile | slider | custom | unknown",
  "coordinate_space": {
    "origin": "viewport_css_px | element_css_px | image_px | normalized",
    "units": "css_px | image_px | ratio",
    "rounding": "nearest_int | preserve_float"
  },
  "viewport": {
    "width": 390,
    "height": 844,
    "device_pixel_ratio": 3.0
  },
  "target_element": {
    "selector_hint": "[data-captcha-root]",
    "bbox_css_px": {"x": 12, "y": 220, "width": 366, "height": 240}
  },
  "actions": [
    {"kind": "pointer_down", "x": 61, "y": 330, "time_ms": 0},
    {"kind": "pointer_move", "x": 196, "y": 330, "time_ms": 420},
    {"kind": "pointer_up", "x": 196, "y": 330, "time_ms": 520}
  ],
  "challenge_state_machine": {
    "initial_state": "loaded",
    "terminal_states": ["accepted", "rejected", "blocked"],
    "states": ["loaded", "predicted", "submitted", "accepted", "rejected", "blocked"],
    "transitions": [
      {"from": "loaded", "event": "model_prediction", "to": "predicted"},
      {"from": "predicted", "event": "action_replay", "to": "submitted"}
    ]
  }
}
```

## Rules

- Coordinates must name their origin and unit. A raw `(x, y)` pair without a
  coordinate space is invalid.
- `time_ms` is monotonic and starts at zero for the action sequence.
- Token values, challenge ids, motion telemetry, and provider payloads are not
  stored in the action manifest.
- The final action manifest records the model intent only. Backend acceptance
  still requires separate `verified` and `repeat_verified` evidence.
