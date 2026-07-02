# Fingerprint Surface Observation Reference

Use this reference for authorized fingerprint surface inventory and drift
reporting. It is not an evasion guide.

Required ledger fields:

- target class and authorization scope
- profile id and repeat count
- surface report path
- surface hash list
- drift count
- fact labels: observed, derived, assumed, unverified
- explicit forbidden action check

Required surfaces:

- navigator webdriver, user agent, platform, languages, plugins
- hardware concurrency and device memory
- screen, timezone, locale
- canvas, WebGL, audio, fonts
- permissions, WebRTC, client hints
- network timing and storage state

Boundary:

- A surface hash is diagnostic evidence only.
- Public diagnostic pages do not prove third-party risk-control acceptance.
- Do not add stealth patches, spoofed values, proxy rotation, or clearance reuse.

