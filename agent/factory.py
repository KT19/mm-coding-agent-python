from dataclasses import dataclass
from typing import Literal

import yaml

from agent.base import BaseAgent
from agent.multi_agent import MultiAgent
from agent.single_agent import SingleAgent


@dataclass
class AgentConfig:
    mode: Literal["single", "multi"] = "single"
    host: str = "localhost:11434"
    model: str = "gemma4:e4b"
    max_steps: int = 5
    max_agent_turns: int = 5

    @classmethod
    def from_yaml_path(cls, yaml_path: str) -> "AgentConfig":
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        return cls(**config)


def create_agent(task: str, config: AgentConfig) -> BaseAgent:
    if config.mode == "single":
        return SingleAgent(
            user_task=task, host=config.host, model=config.model, max_steps=config.max_steps
        )
    elif config.mode == "multi":
        return MultiAgent(
            user_task=task,
            host=config.host,
            model=config.model,
            max_steps=config.max_steps,
            max_agent_turns=config.max_agent_turns,
        )

    raise ValueError(f"Unknown agent mode: {config.mode}")
