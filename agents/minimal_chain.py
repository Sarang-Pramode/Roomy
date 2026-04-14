"""Golden-path example: LCEL chain + FakeListChatModel (no API keys)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from repo root without installing roomy (optional dev hack)
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "packages" / "roomy" / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate

from roomy import end_session, instrument_langchain


def main() -> None:
    db = os.environ.get("ROOMY_DB_PATH", str(_ROOT / "traces.db"))
    os.environ.setdefault("ROOMY_DB_PATH", db)

    bindings = instrument_langchain(app_name="minimal-chain", db_path=db)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a concise assistant."),
            ("human", "{topic}"),
        ]
    )
    llm = FakeListChatModel(responses=["hello from roomy"])
    chain = prompt | llm
    out = chain.invoke({"topic": "Say hi."}, config={"callbacks": bindings.callbacks})
    print("LLM output:", out)
    print("Roomy session:", bindings.manager.session_id)
    end_session(bindings.manager)


if __name__ == "__main__":
    main()
