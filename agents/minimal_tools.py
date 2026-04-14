"""Example with a simple tool to populate tool_calls rows."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "packages" / "roomy" / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from roomy import end_session, instrument_langchain


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def main() -> None:
    db = os.environ.get("ROOMY_DB_PATH", str(_ROOT / "traces.db"))
    bindings = instrument_langchain(app_name="minimal-tools", db_path=db)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You have access to tools when needed."),
            ("human", "{q}"),
        ]
    )
    llm = FakeListChatModel(responses=["I will use the tool.", "The sum is 3."])
    # Bind tool so LC emits tool events when using a tool-capable path; FakeListChatModel may not call tools.
    # Still run a direct tool invocation trace via RunnableSequence for demonstration:
    _ = (prompt | llm).invoke({"q": "What is 1+2?"}, config={"callbacks": bindings.callbacks})
    _ = add.invoke({"a": 1, "b": 2}, config={"callbacks": bindings.callbacks})
    print("Roomy session:", bindings.manager.session_id)
    end_session(bindings.manager)


if __name__ == "__main__":
    main()
