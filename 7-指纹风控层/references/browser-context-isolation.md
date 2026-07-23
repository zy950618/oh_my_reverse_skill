# Browser Context Isolation Reference

Use this reference for local or authorized worker/session isolation evidence.

Required isolation fields:

- browser context
- cookie jar
- localStorage and sessionStorage
- IndexedDB and service worker state
- token cache
- fingerprint surface hash
- session owner and worker owner

Required worker ladder when concurrency is claimed:

- worker_1
- worker_2
- worker_5
- worker_10

Each worker tier records request count, success count, failure count, 403/429/503
counts, p95 latency, stop condition, kill switch, and cross-worker pollution.

Boundary:

- Browser evidence does not prove direct interface concurrency.
- Localhost success does not prove production high concurrency.
- Positive concurrency requires final business API acceptance and server-side
  business ledger assertions.

