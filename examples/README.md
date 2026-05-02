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

From the **repo root** (same working directory you use for `roomy serve`):

```bash
python examples/web_chatbot.py
```

By default this writes to **`./roomy_traces.db`** in the current directory — the same file `roomy serve` reads when you do **not** pass `--db` / `ROOMY_DB_PATH`. To use a different file (for example `examples/traces.db`), set the variable **for both** the API and the chatbot:

```bash
export ROOMY_DB_PATH="$PWD/examples/traces.db"
```

- **`/new`** — clear conversation  
- **`/quit`** — exit and flush Roomy session  

### Inspect traces (CLI)

```bash
roomy sessions list --db "$ROOMY_DB_PATH"
roomy sessions show <session-id> --db "$ROOMY_DB_PATH"
```

### Roomy API + web UI (three terminals)

**Terminal 1 — traces API**

```bash
cd /path/to/Roomy   # repo root — same cwd as the chatbot terminal
roomy serve --host 127.0.0.1 --port 8765
# or: roomy serve --db "$PWD/examples/traces.db" ... if you prefer a dedicated DB file
```

**Terminal 2 — React UI**

```bash
cd apps/web
npm install
npm run dev
```

Open the URL Vite prints (e.g. `http://127.0.0.1:5173`). The dev server proxies API calls to port **8765**.

**Terminal 3 — chatbot**

```bash
cd /path/to/Roomy
python examples/web_chatbot.py
```

Use the **same current directory** and the same `ROOMY_DB_PATH` (if you set it) for `roomy serve` and the chatbot so the UI reads the same SQLite file.

### Safety

- `fetch_webpage` is for **local development** only; it fetches arbitrary URLs you ask for. Do not expose this script on the public internet without hardening.
