from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler, BaseCallbackHandler
from langchain_core.outputs import LLMResult

from roomy.instrumentation.manager import TraceManager


def _rid(run_id: UUID | str | None) -> str | None:
    if run_id is None:
        return None
    return str(run_id)


class RoomyCallbackHandler(BaseCallbackHandler):
    """Synchronous LangChain callback handler for Roomy."""

    def __init__(self, manager: TraceManager) -> None:
        super().__init__()
        self._mgr = manager

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        self._mgr.chain_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
        )

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        self._mgr.chain_end(run_id=_rid(run_id))

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        self._mgr.chain_end(run_id=_rid(run_id))

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        inv = kwargs.get("invocation_params")
        self._mgr.llm_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
            prompts=prompts,
            invocation_params=inv if isinstance(inv, dict) else None,
        )

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> Any:
        self._mgr.llm_end(run_id=_rid(run_id), result=response)

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        self._mgr.llm_error(run_id=_rid(run_id))

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        self._mgr.tool_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
            inputs=inputs if inputs is not None else input_str,
        )

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> Any:
        self._mgr.tool_end(run_id=_rid(run_id), output=output)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        self._mgr.tool_error(run_id=_rid(run_id))

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        self._mgr.retriever_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
            query=query,
        )

    def on_retriever_end(
        self,
        documents: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        self._mgr.retriever_end(run_id=_rid(run_id), documents=documents)

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> Any:
        self._mgr.retriever_error(run_id=_rid(run_id))


class RoomyAsyncCallbackHandler(AsyncCallbackHandler):
    """Async LangChain callback handler for Roomy."""

    def __init__(self, manager: TraceManager) -> None:
        super().__init__()
        self._mgr = manager

    async def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._mgr.chain_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
        )

    async def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._mgr.chain_end(run_id=_rid(run_id))

    async def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._mgr.chain_end(run_id=_rid(run_id))

    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        inv = kwargs.get("invocation_params")
        self._mgr.llm_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
            prompts=prompts,
            invocation_params=inv if isinstance(inv, dict) else None,
        )

    async def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        self._mgr.llm_end(run_id=_rid(run_id), result=response)

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._mgr.llm_error(run_id=_rid(run_id))

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._mgr.tool_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
            inputs=inputs if inputs is not None else input_str,
        )

    async def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        self._mgr.tool_end(run_id=_rid(run_id), output=output)

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._mgr.tool_error(run_id=_rid(run_id))

    async def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._mgr.retriever_start(
            run_id=_rid(run_id),
            parent_run_id=_rid(parent_run_id),
            serialized=serialized,
            query=query,
        )

    async def on_retriever_end(
        self,
        documents: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._mgr.retriever_end(run_id=_rid(run_id), documents=documents)

    async def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._mgr.retriever_error(run_id=_rid(run_id))
