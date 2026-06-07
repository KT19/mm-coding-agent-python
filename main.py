import asyncio
import os

from agent.factory import AgentConfig, create_agent


async def main():
    os.makedirs("workspace", exist_ok=True)

    task = input("user -> ")
    config = AgentConfig.from_yaml_path("agent_config.yaml")
    agent = create_agent(task, config)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
