# Roomy

**Roomy** is a local-first observability toolkit for **LangChain** agents. It records what entered the model (messages, tools, retrievers), **token usage**, **latency**, and **structured traces** in **SQLite**, with a **CLI** and an optional **web UI** for inspection.

## Install

```bash
pip install roomy-observability
```

- **PyPI package:** `roomy-observability`
- **Python import:** `import roomy`
- **CLI:** `roomy` (e.g. `roomy serve`, `roomy sessions list`, `roomy dashboard` to open the web UI in a browser)

Requires **Python 3.11+**.

## Quick start

```python
from roomy import end_session, instrument_langchain

bindings = instrument_langchain(app_name="my-agent", db_path="./traces.db")
result = chain.invoke(
    {"topic": "Hello"},
    config={"callbacks": bindings.callbacks},
)
end_session(bindings.manager)
```

Use `wrap_agent(chain, bindings.manager)` if you prefer binding callbacks on a Runnable.

## Optional extras

| Extra | Purpose |
| ----- | ------- |
| `api` | FastAPI + Uvicorn (`roomy serve` for the inspector API) |
| `openai` | `tiktoken` for better token estimates |
| `examples` | LangGraph + OpenAI + dotenv + httpx (for repo examples under `examples/`) |
| `dev` | Tests, ruff, mypy, build, twine |

```bash
pip install "roomy-observability[api,openai]"
pip install "roomy-observability[api,openai,examples]"   # LangGraph example deps
```

## Documentation & source

Full monorepo (sample agents, web app, architecture docs): **[github.com/Sarang-Pramode/Roomy](https://github.com/Sarang-Pramode/Roomy)**

**Author:** [Sarang Pramode](https://pramode.dev) · **License:** MIT
