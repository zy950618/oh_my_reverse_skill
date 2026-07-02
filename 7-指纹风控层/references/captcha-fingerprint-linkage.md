# CAPTCHA And Fingerprint Linkage Reference

Use this reference to record observed linkage between CAPTCHA/risk state and
browser fingerprint surfaces. It is diagnostics-only.

Allowed observations:

- provider marker
- widget or challenge id
- risk state transition
- surface hash reference
- session context reference
- backend acceptance reference
- fact labels

Required boundaries:

- Challenge endpoint success is not business success.
- CAPTCHA token reuse is prohibited.
- Fingerprint spoofing is prohibited.
- Final business API evidence is required before any positive capability claim.
- Repeat verification is required before stability claims.

Safe actions are record, downgrade, human review, official API fallback, or stop.

