# Roomy — Development

## Python environment

From `packages/roomy`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api,openai]"
pytest
```

## LangGraph + OpenAI example

See [examples/README.md](../examples/README.md) (`web_chatbot.py`, `.env` for `OPENAI_API_KEY`).

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

The workflow [`.github/workflows/publish-pypi.yml`](../.github/workflows/publish-pypi.yml) runs when you **publish a GitHub Release**. It does **not** run on every push to `main` (only when you publish a release for a tag). It builds `packages/roomy` and uploads to PyPI using **Trusted Publishing** (OIDC — no API token in GitHub secrets).

#### One-time: GitHub

1. Open **https://github.com/Sarang-Pramode/Roomy/settings/environments**
2. **New environment** → name: **`release`** (must match the workflow and PyPI form).
3. Optional: add protection rules (e.g. required reviewers) before production uploads.

#### One-time: PyPI

1. **https://pypi.org/manage/project/roomy-observability/settings/publishing/**
2. **Add a new pending publisher** (GitHub) with exactly:
   - **Owner:** `Sarang-Pramode`
   - **Repository name:** `Roomy`
   - **Workflow name:** `publish-pypi.yml` — not `workflow.yml`; the file lives at `.github/workflows/publish-pypi.yml`.
   - **Environment name:** `release` — must match the GitHub Environment and `environment: release` in the workflow job.

3. Click **Add**, then confirm the pending publisher (PyPI may ask you to verify).

#### Each release

1. On `main`: bump **`version`** in `packages/roomy/pyproject.toml` and `packages/roomy/src/roomy/__init__.py`, update **`CHANGELOG.md`**, commit, push.
2. **GitHub → Releases → Draft a new release** → create or select tag **`vX.Y.Z`** targeting `main` → **Publish release**.

The workflow runs once and uploads that commit’s tree to PyPI. The tag should match the version you set in `pyproject.toml`.

## Docker

From repo root: `docker compose up` starts API on port 8765 (see `docker-compose.yml`).
