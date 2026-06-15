# Capture Run

```yaml
run_id:
domain:
started_at:
operator:
stage:
auth_state:
browser_profile_id:
state_reset:
source_memory_read:
  reverse_memory:
  site_known_failures:
  site_test_log:
  knowledge_graph:
  impact_regression:
capture_outputs:
  har:
  devtools_events:
  screenshots:
script_hashes:
  - url:
    hash:
    etag:
network_ids:
  - request_id:
    url:
    method:
    status:
storage_state:
  cookies_summary:
  local_storage_keys:
  session_storage_keys:
  service_worker_state:
freshness_decision:
```

## Notes

- Do not mix request ids across runs.
- Do not reuse scriptId after page refresh without re-searching the script.
- Do not mark a value observed unless it belongs to this `run_id` or was revalidated by this `run_id`.
