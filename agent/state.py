from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    task: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 1
    max_steps: int = 5
    is_complete: bool = False

    # Context control
    max_retained_image: int = 1

    def __post_init__(self) -> None:
        system_instruction = "You are a professional, autonomous software engineering agent for Python. Follow instructions strictly and use tools to accomplish your task."
        self.messages.append({"role": "system", "content": system_instruction})
        self.messages.append({"role": "user", "content": f"Task: {self.task}"})

    def add_message(self, role: str, content: str, tool_calls: list[Any] | None = None) -> None:
        msg: dict[str, Any] = {"role": role, "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls

        self.messages.append(msg)
        self._optimize_context_window()

    def add_tool_response(self, tool_name: str, content: str) -> None:
        self.messages.append({"role": "tool", "content": content, "tool_name": tool_name})
        self._optimize_context_window()

    def add_image_tool_response(self, tool_name: str, content: str, image_path: str) -> None:
        self.messages.append(
            {
                "role": "tool",
                "content": content,
                "tool_name": tool_name,
                "images": [image_path],
            }
        )
        self._optimize_context_window()

    def _optimize_context_window(self) -> None:
        """
        Enforces memory pruning optimization rules.
        Traverses historical turns to evict old image payloads, converting them into simple text logs once they pass out of the immediate attention window.
        """
        image_count = 0

        # Traverse history backwards
        for message in reversed(self.messages):
            if "images" in message and message["images"]:
                image_count += 1

                if image_count > self.max_retained_image:
                    print(
                        f"[Memory Manager] Evicting heavy visual tokens from historical '{message.get('tool_name')}' turn."
                    )
                    # Append a permanent textual note
                    message["content"] += (
                        "\n[System Note: Raw visual pixels evicted from history to optimize context window]"
                    )

                    del message["images"]
