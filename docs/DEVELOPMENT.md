# Roomy — Development

## Python environment

From `packages/roomy`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api,openai]"
pytest
```

## Run sample agent

From repository root (after editable install):

```bash
export ROOMY_DB_PATH="$PWD/traces.db"
python agents/minimal_chain.py
roomy sessions list --db "$ROOMY_DB_PATH"
```

## API + web UI

Terminal 1:

```bash
roomy serve --db traces.db --port 8765
```

Terminal 2:

```bash
cd apps/web
npm install
npm run dev
```

Vite proxies `/sessions`, `/steps`, `/health` to `http://127.0.0.1:8765`.

## Configuration (optional)

Set `ROOMY_CONFIG` to a YAML file, for example:

```yaml
db_path: ./traces.db
capture_raw: true
redaction:
  enabled: true
  store_full_text: true
  pii_email: false
```

## Release checklist (PyPI)

1. Update version in `packages/roomy/pyproject.toml` and `roomy/__init__.py`.
2. Update `CHANGELOG.md`.
3. `python -m build` (ensure `build` installed) and `twine upload dist/*`.
4. The distribution name is **`roomy-observability`**; end users run `pip install roomy-observability` and `import roomy`.

## Docker

From repo root: `docker compose up` starts API on port 8765 (see `docker-compose.yml`).
