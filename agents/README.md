# Example agents

These scripts are for **local development** of Roomy. Install the Python package in editable mode from `packages/roomy`, then run:

```bash
export ROOMY_DB_PATH=/absolute/path/to/traces.db
python minimal_chain.py
```

Use `roomy sessions list --db "$ROOMY_DB_PATH"` to inspect captured sessions.
