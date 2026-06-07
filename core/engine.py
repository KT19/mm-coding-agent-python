from typing import Any

from ollama import AsyncClient, ChatResponse

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL_NAME = "gemma4:e4b"
_CONTEXT_WINDOW = 131072
_TEMPERATURE = 0.2


class OllamaEngine:
    def __init__(self, host: str = _DEFAULT_HOST, model: str = _DEFAULT_MODEL_NAME) -> None:
        self.host = host
        self.model = model

        if self.host:
            self.client = AsyncClient(host=self.host)
        else:
            self.client = AsyncClient()

    async def generate_chat(
        self, messages: list[dict[str, Any]], tools: list[Any] | None = None
    ) -> ChatResponse:
        try:
            options = {
                "num_ctx": _CONTEXT_WINDOW,
                "temperature": _TEMPERATURE,
            }

            return await self.client.chat(
                model=self.model, messages=messages, tools=tools, options=options, think=False
            )
        except Exception as e:
            raise RuntimeError(f"Engine Error: {e}") from e
