# Roomy examples

## Web chatbot (`web_chatbot.py`)

A **LangGraph** ReAct agent using **OpenAI** with a **`fetch_webpage`** tool so you can ask questions grounded in public URLs.

### Setup

1. From the repo root, use a virtualenv and install Roomy plus example dependencies:

   ```bash
   cd packages/roomy
   pip install -e ".[api,openai,examples]"
   cd ../..
   ```

2. Configure secrets (not committed):

   ```bash
   cp examples/.env.example examples/.env
   ```

   Edit `examples/.env` and set **`OPENAI_API_KEY`**. Optionally set **`OPENAI_MODEL`** (default `gpt-4o-mini`).

### Run the chatbot

From the **repo root**:

```bash
python examples/web_chatbot.py
```

The script sets **`ROOMY_DB_PATH`** for its own process to **`examples/traces.db`** under the repo (absolute path). You do **not** need to export it for the chatbot. Optional: set **`ROOMY_DB_PATH`** in your shell or in `examples/.env` to override.

Open the dashboard in your browser when the agent starts (Vite must already be running, see below):

```bash
python examples/web_chatbot.py --open-dashboard
# or: python examples/web_chatbot.py -o
```

From any terminal, after `npm run dev` is up:

```bash
roomy dashboard
```

Optional flags: `roomy dashboard --port 5173 --host 127.0.0.1`

- **`/new`** — clear conversation  
- **`/quit`** — exit and flush Roomy session  

### Inspect traces (CLI)

Use the **same** database file the script printed (`roomy serve --db "..."` or `examples/traces.db`):

```bash
roomy sessions list --db examples/traces.db
roomy sessions show <session-id> --db examples/traces.db
```

Or export once per shell:

```bash
export ROOMY_DB_PATH="$PWD/examples/traces.db"
roomy sessions list
```

### Roomy API + web UI (three terminals)

**Terminal 1 — traces API** (use the same DB path as the chatbot; copy from the script’s startup line or use):

```bash
cd /path/to/Roomy
roomy serve --db "$PWD/examples/traces.db" --host 127.0.0.1 --port 8765
```

**Terminal 2 — React UI**

```bash
cd apps/web
npm install
npm run dev
```

**Terminal 3 — chatbot**

```bash
cd /path/to/Roomy
python examples/web_chatbot.py
# optional: python examples/web_chatbot.py --open-dashboard
```

The dev server proxies `/sessions`, `/steps`, etc. to port **8765**.

### “This site can’t be reached” / `ERR_CONNECTION_REFUSED` on port 5173

Port **5173** is the **Vite** dev server (`npm run dev` in `apps/web`). If you close that terminal, nothing listens on 5173 anymore — start it again:

```bash
cd apps/web && npm install && npm run dev
```

`roomy dashboard` checks the port first; use `roomy dashboard --skip-check` only if you intentionally want to open the URL without verifying.

### Safety

- `fetch_webpage` is for **local development** only; it fetches arbitrary URLs you ask for. Do not expose this script on the public internet without hardening.
