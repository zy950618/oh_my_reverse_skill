# FastAPI Adapter Scaffold

This directory is a scaffold for a future FastAPI adapter around the localhost
mock server contract. It is not wired into production and does not call real
airline sites.

`app.py` imports FastAPI only when executed in an environment that already has
the dependency installed. No dependency is added by this scaffold.

