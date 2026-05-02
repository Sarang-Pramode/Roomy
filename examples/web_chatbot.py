"""
LangGraph ReAct agent: OpenAI chat + optional fetch_webpage tool for URL-grounded answers.

Run from repo root (with roomy + examples extras installed):

  cp examples/.env.example examples/.env   # then edit OPENAI_API_KEY
  export ROOMY_DB_PATH="$PWD/examples/traces.db"
  python examples/web_chatbot.py

Type messages at the prompt. Use /quit to exit.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "packages" / "roomy" / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

load_dotenv(_ROOT / "examples" / ".env")

from roomy import end_session, instrument_langchain  # noqa: E402


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@tool
def fetch_webpage(url: str) -> str:
    """Fetch a public http(s) page and return readable plain text (truncated). Use when the user gives a URL or asks what a site says."""
    import httpx

    u = url.strip()
    if not u.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"
    try:
        with httpx.Client(
            timeout=20.0,
            follow_redirects=True,
            headers={"User-Agent": "RoomyExamples/1.0 (+https://github.com/Sarang-Pramode/Roomy)"},
        ) as client:
            r = client.get(u)
            r.raise_for_status()
            ct = (r.headers.get("content-type") or "").lower()
            if "text/html" not in ct and "text/plain" not in ct and "application/json" not in ct:
                return f"Unsupported content-type: {ct or 'unknown'}"
            raw = r.text if isinstance(r.text, str) else r.content.decode("utf-8", errors="replace")
            body = _strip_html(raw) if "html" in ct else raw
            if len(body) > 14_000:
                body = body[:14_000] + "\n…(truncated)"
            return body or "(empty body)"
    except Exception as e:
        return f"Error fetching page: {e}"


def _print_reply(messages: list[BaseMessage]) -> None:
    last = messages[-1]
    if isinstance(last, AIMessage):
        if last.content:
            print("\nAssistant:", last.content)
        elif last.tool_calls:
            print("\nAssistant: (calling tools…)")
        else:
            print("\nAssistant:", last)
    else:
        print("\nAssistant:", last)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY. Copy examples/.env.example to examples/.env and set your key.", file=sys.stderr)
        sys.exit(1)

    db = os.environ.get("ROOMY_DB_PATH", str(_ROOT / "examples" / "traces.db"))
    os.environ.setdefault("ROOMY_DB_PATH", db)
    Path(db).parent.mkdir(parents=True, exist_ok=True)

    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    graph = create_react_agent(llm, tools=[fetch_webpage])

    bindings = instrument_langchain(app_name="examples-web-chatbot", db_path=db)
    cfg = {"callbacks": bindings.callbacks}

    print("Web-aware chatbot (LangGraph + OpenAI). Commands: /quit, /new")
    print("Roomy session:", bindings.manager.session_id)
    print("Tip: ask about a page, e.g. “Summarize https://example.com”\n")

    messages: list[BaseMessage] = []
    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("/quit", "/exit", "quit", "exit"):
            break
        if line.lower() == "/new":
            messages = []
            print("(conversation cleared)")
            continue
        messages.append(HumanMessage(content=line))
        try:
            result = graph.invoke({"messages": messages}, config=cfg)
        except Exception as e:
            print("Error:", e, file=sys.stderr)
            messages.pop()
            continue
        messages = list(result["messages"])
        # Log tool outputs briefly for terminal UX
        for m in messages[-4:]:
            if isinstance(m, ToolMessage):
                prev = m.content[:200] + ("…" if len(str(m.content)) > 200 else "")
                print(f"  [tool {m.name}] {prev}")
        _print_reply(messages)

    end_session(bindings.manager)
    print("Goodbye. Inspect traces with: roomy sessions list --db", repr(db))


if __name__ == "__main__":
    main()
