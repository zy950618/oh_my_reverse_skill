# Curl Examples

Local mock server only:

```bash
python public-range-evidence/airline-lab-order-flow/mock_server/server.py --port 18991
curl http://127.0.0.1:18991/health
curl "http://127.0.0.1:18991/api/search?origin=KUL&destination=SIN&date=2026-08-01"
curl -X POST http://127.0.0.1:18991/api/detail -H "content-type: application/json" -d "{\"session_id\":\"lab-session-001\",\"flight_id\":\"LAB-MH-001\"}"
curl -X POST http://127.0.0.1:18991/api/order -H "content-type: application/json" -d "{\"session_id\":\"lab-session-001\",\"flight_id\":\"LAB-MH-001\",\"detail_nonce\":\"detail-nonce-001\"}"
```

These examples do not call real airline sites.

