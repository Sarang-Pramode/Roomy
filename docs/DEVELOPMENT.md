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

Distribution name: **`roomy-observability`**. Install: `pip install roomy-observability`. Import: `import roomy`. CLI: `roomy`.

### One-time setup

1. Create accounts on [PyPI](https://pypi.org/account/register/) and (optional) [TestPyPI](https://test.pypi.org/account/register/).
2. Create an **API token** (PyPI → Account settings → API tokens). Scope: entire account or project `roomy-observability` after the first upload.

### Every release

1. Bump **`version`** in [`packages/roomy/pyproject.toml`](../packages/roomy/pyproject.toml) and in [`packages/roomy/src/roomy/__init__.py`](../packages/roomy/src/roomy/__init__.py).
2. Update root [`CHANGELOG.md`](../CHANGELOG.md).
3. From **`packages/roomy`** (clean build):

   ```bash
   rm -rf dist/
   pip install build twine
   python -m build
   python -m twine check dist/*
   ```

4. Upload (use a **token**, not your password):

   ```bash
   python -m twine upload dist/*
   ```

   When prompted: **Username** `__token__`, **Password** your PyPI API token (including the `pypi-` prefix).

   Or: `python -m twine upload dist/* --username __token__ --password "$(pbpaste)"` after copying the token on macOS.

5. Optional dry run on TestPyPI first:

   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

   Then: `pip install --index-url https://test.pypi.org/simple/ roomy-observability`

### After publish

Confirm: [https://pypi.org/project/roomy-observability/](https://pypi.org/project/roomy-observability/) (once live).

### Publishing from GitHub (recommended)

The workflow [`.github/workflows/publish-pypi.yml`](../.github/workflows/publish-pypi.yml) runs when you **publish a GitHub Release** (not draft). It builds `packages/roomy` and uploads to PyPI using **Trusted Publishing** (no long-lived API token in GitHub secrets).

1. On [PyPI](https://pypi.org/manage/project/roomy-observability/settings/publishing/) → **Publishing** → add a trusted publisher:
   - **PyPI Project:** `roomy-observability`
   - **Owner:** `Sarang-Pramode`
   - **Repository:** `Roomy`
   - **Workflow name:** `publish-pypi.yml`
   - **Environment:** leave blank (unless you add a GitHub Environment later)
2. On GitHub: bump version, update `CHANGELOG.md`, push to `main`.
3. **Releases** → **Draft a new release** → choose tag `v0.x.y` (create new tag on `main`) → publish release.

The workflow uploads the artifacts built from that tag’s tree.

## Docker

From repo root: `docker compose up` starts API on port 8765 (see `docker-compose.yml`).
