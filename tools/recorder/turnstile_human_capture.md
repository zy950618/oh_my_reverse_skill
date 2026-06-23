# turnstile_human_capture.py

Visible-browser human-reviewed Cloudflare Turnstile capture.

This tool records evidence only. It does not solve, bypass, generate, or reuse CAPTCHA/WAF tokens.

## Usage

```powershell
python tools/recorder/turnstile_human_capture.py --dry-run
```

```powershell
python tools/recorder/turnstile_human_capture.py `
  --round verified `
  --auto-submit `
  --require-backend-success
```

```powershell
python tools/recorder/turnstile_human_capture.py `
  --round repeat_verified `
  --auto-submit `
  --require-backend-success
```

## Output

- `<capture-id>.har`
- `<capture-id>.png`
- `<capture-id>.summary.json`

The summary stores token field names, token lengths, backend `/status`, storage/cookie metadata, and request/response summaries. It does not store token values.

## Success Criteria

`verified` is accepted only when `/proverka.php` returns the configured `--expected-status`, default `success`.

`repeat_verified` must be captured in a new temporary profile or documented `--profile-dir` to avoid reusing stale state silently.
