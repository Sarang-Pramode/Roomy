# Roomy

**Roomy** is a local-first observability toolkit for LangChain agents: capture what entered model context, token usage, latency, and structured traces in SQLite, then inspect them via CLI or a minimal web UI.

The PyPI distribution is **`roomy-observability`** (the bare name `roomy` is often taken). After install you still **`import roomy`** and run the **`roomy`** CLI.

## Quick start

```bash
cd packages/roomy
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api,openai]"
```

Run a sample agent (from repo root, with the package installed editable from `packages/roomy`):

```bash
export ROOMY_DB_PATH="$PWD/traces.db"
python agents/minimal_chain.py
roomy sessions list --db "$ROOMY_DB_PATH"
```

The agent uses `bindings = instrument_langchain(...)` and passes `config={"callbacks": bindings.callbacks}` to LangChain.

Start the API and UI:

```bash
roomy serve --db traces.db --host 127.0.0.1 --port 8765
cd apps/web && npm install && npm run dev
```

Open the UI at the URL Vite prints (API proxied to `http://127.0.0.1:8765`).

## Examples

- [LangGraph + OpenAI web chatbot](examples/README.md) (`examples/web_chatbot.py`) — `.env` for API keys, `fetch_webpage` tool, auto `examples/traces.db`, `roomy dashboard` / `--open-dashboard`.

## Docs

- [Status & roadmap checklist](docs/STATUS.md)
- [Design](docs/DESIGN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)

## Contributors

- [Sarang Pramode](https://pramode.dev)

## License

MIT
