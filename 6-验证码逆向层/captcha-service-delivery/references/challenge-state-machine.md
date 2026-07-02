# Challenge state machine

Version: 0.1.0

The challenge state machine records what was observed around a model prediction
and action replay. It prevents treating a rendered widget, provider config, or
local action success as backend acceptance.

## Common states

```text
loaded -> predicted -> action_ready -> submitted
submitted -> provider_accepted -> business_accepted
submitted -> provider_rejected
submitted -> blocked
business_accepted -> repeat_verified
```

## Required state labels

- `loaded`: widget or local lab challenge is visible.
- `predicted`: model produced an action schema.
- `action_ready`: coordinate transform and validation passed.
- `submitted`: action replay was attempted.
- `provider_accepted`: provider or lab verifier accepted the action.
- `business_accepted`: final protected business endpoint accepted the result.
- `repeat_verified`: a separate repeat run accepted the result.
- `provider_rejected`: verifier rejected the action.
- `blocked`: manual challenge, protection, missing authorization, or unsupported
  challenge stopped the run.

## Rules

- `provider_accepted` is not equal to `business_accepted`.
- `business_accepted` is not equal to `repeat_verified`.
- Third-party positive capability requires authorized `business_accepted` and
  `repeat_verified` evidence, not just local state transitions.
