# Live Test Policy

Default mode is dry-run. Without `authorized-live-targets.local.yaml`, runners only validate schema and produce no network side effects. Production order creation, payment, inventory lock, credential reuse, and high-frequency requests are forbidden unless explicit authorization and runbook confirmation exist.
