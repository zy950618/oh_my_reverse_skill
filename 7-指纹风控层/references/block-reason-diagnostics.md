# Block Reason Diagnostics Reference

Use this reference when a run has response evidence and needs attribution. Keep
observed signals separate from derived block reasons.

Minimum evidence:

- status code and response class
- request context and session context
- fingerprint surface report reference when fingerprint attribution is in scope
- authorization scope
- fact labels

Allowed classifications:

- blocked_by_scope
- blocked_by_auth
- blocked_by_stale_state
- blocked_by_fingerprint_signal
- blocked_by_rate_limit
- blocked_by_business_rule
- unknown

Safe next actions:

- stop
- ask for authorization
- reset local lab state
- reduce rate
- use official API fallback
- route to human review
- record a negative eval

Forbidden outputs:

- webdriver hiding
- fingerprint spoofing
- proxy rotation for evasion
- clearance cookie reuse
- risk token reuse
- CAPTCHA or WAF bypass instructions

