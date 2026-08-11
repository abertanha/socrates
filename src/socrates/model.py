"""Model-provider boundary for Socrates.

Real providers are any LangChain ``BaseChatModel`` or ``provider:model`` string
accepted by ``create_deep_agent``. Tests use ``StubChatModel``.
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

ModelProvider = BaseChatModel | str


class StubChatModel(BaseChatModel):
    """Scripted chat model for orchestration tests.

    Implements ``bind_tools`` as a no-op so deepagents can bind its tool suite
    while responses remain fully determined by ``responses``.
    """

    responses: list[AIMessage]
    _index: int = 0

    @property
    def _llm_type(self) -> str:
        return "socrates-stub"

    def bind_tools(self, tools: Any, *, tool_choice: Any = None, **kwargs: Any) -> StubChatModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self._index >= len(self.responses):
            message = AIMessage(content="(stub exhausted)")
        else:
            message = self.responses[self._index]
            object.__setattr__(self, "_index", self._index + 1)
        return ChatResult(generations=[ChatGeneration(message=message)])
