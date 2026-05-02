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

```bash
export ROOMY_DB_PATH="$PWD/examples/traces.db"
python examples/web_chatbot.py
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
export ROOMY_DB_PATH="$PWD/examples/traces.db"
roomy serve --db "$ROOMY_DB_PATH" --host 127.0.0.1 --port 8765
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
export ROOMY_DB_PATH="$PWD/examples/traces.db"
python examples/web_chatbot.py
```

Use the same `ROOMY_DB_PATH` in all three so the UI shows the sessions your chatbot creates.

### Safety

- `fetch_webpage` is for **local development** only; it fetches arbitrary URLs you ask for. Do not expose this script on the public internet without hardening.
