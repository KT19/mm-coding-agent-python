from typing import Any

from agent.base import BaseAgent
from agent.personas import CODER_SYSTEM_PROMPT, PM_SYSTEM_PROMPT, QA_SYSTEM_PROMPT
from agent.state import AgentState
from core.engine import OllamaEngine
from tools.tool_registry import ALLOCATED_TOOLS, TOOL_MANIFEST


class MultiAgent(BaseAgent):
    def __init__(
        self, user_task: str, host: str, model: str, max_steps: int = 5, max_agent_turns: int = 5
    ) -> None:
        self.user_task = user_task
        self.engine = OllamaEngine(host=host, model=model)
        self.workspace_state = AgentState(task=user_task, max_steps=max_steps)
        self.tool_list = TOOL_MANIFEST
        self.max_agent_turns = max_agent_turns

    async def run_pm_phase(self) -> str:
        print("\n--- Product Manager Phase ---")
        messages = [
            {"role": "system", "content": PM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Analyze this request and generate a clear code specification: {self.user_task}",
            },
        ]
        response = await self.engine.generate_chat(messages=messages)
        spec = response["message"]["content"]
        print(f"\n [PM Specification Generated]: \n{spec}\n")

        return spec

    async def execute_agent_turn(
        self,
        persona_prompt: str,
        contextual_instruction: str,
        allowed_tools: list[Any] | None = None,
    ) -> str:
        """Helper to run a clean ReAct execution step for a specific agent persona."""
        # Dynamically inject the persona's system instruction
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": persona_prompt},
            {"role": "user", "content": contextual_instruction},
        ]

        for msg in self.workspace_state.messages:
            if msg["role"] in ["assistant", "tool"]:
                messages.append(msg)

        latest_content = ""

        for _ in range(self.max_agent_turns):
            response = await self.engine.generate_chat(messages=messages, tools=allowed_tools)

            message = response.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            latest_content = content

            self.workspace_state.add_message(
                role="assistant", content=content, tool_calls=tool_calls
            )
            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})

            if content:
                print(f"Agent output: {content}")

            if not tool_calls:
                return content

            for call in tool_calls:
                func_name = call.function.name
                func_args = call.function.arguments
                print(f"Executing Tool Call: {func_name}({func_args})")

                if func_name not in ALLOCATED_TOOLS:
                    observation = f"Error: Tool '{func_name}' is not registered."
                    self.workspace_state.add_tool_response(tool_name=func_name, content=observation)
                    messages.append(
                        {"role": "tool", "content": observation, "tool_name": func_name}
                    )
                    continue

                try:
                    observation = ALLOCATED_TOOLS[func_name](**func_args)
                except Exception:
                    observation = f"Error: Tool '{func_name}'"

                if isinstance(observation, str) and observation.startswith(
                    "__ATTACH_IMAGE_SIGNAL__"
                ):
                    image_path = observation.split(":", 1)[1]
                    tool_content = f"System: Image file '{image_path}' has been successfully rendered and rendered to your optic sensors below."

                    self.workspace_state.add_image_tool_response(
                        tool_name=func_name,
                        content=tool_content,
                        image_path=image_path,
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": tool_content,
                            "tool_name": func_name,
                            "images": [image_path],
                        }
                    )
                else:
                    self.workspace_state.add_tool_response(tool_name=func_name, content=observation)
                    messages.append(
                        {"role": "tool", "content": observation, "tool_name": func_name}
                    )

        return latest_content

    async def run(self) -> None:
        # PM creates the blueprint
        code_spec = await self.run_pm_phase()

        current_iteration = 1
        qa_feedback = f"Initial Task Blueprint established by PM:\n{code_spec}"

        while current_iteration <= self.workspace_state.max_steps:
            print(f"\n--- [ Iteration {current_iteration} ] ---")

            # Run Coder Turn
            print("\n -> [Coding Agent Turn] Building/Patching Assets")
            coder_instruction = (
                f"Based on this feedback, use tools to write or fix the code:\n{qa_feedback}"
            )
            await self.execute_agent_turn(
                persona_prompt=CODER_SYSTEM_PROMPT,
                contextual_instruction=coder_instruction,
                allowed_tools=[
                    ALLOCATED_TOOLS["write_workspace_file"],
                    ALLOCATED_TOOLS["make_workspace_directory"],
                    ALLOCATED_TOOLS["read_workspace_file"],
                    ALLOCATED_TOOLS["list_workspace_files"],
                ],
            )

            # Run QA Turn
            print("\n -> [QA Agent Turn] Testing & Validating...")
            qa_instruction = "Verify the codebase using sandboxed execution tools and image inspectors. If bugs exist, report them. If clean, reply 'TASK PASSED'."
            qa_feedback = await self.execute_agent_turn(
                persona_prompt=QA_SYSTEM_PROMPT,
                contextual_instruction=qa_instruction,
                allowed_tools=[
                    ALLOCATED_TOOLS["execute_python_script"],
                    ALLOCATED_TOOLS["inspect_image_workspace"],
                    ALLOCATED_TOOLS["read_workspace_file"],
                ],
            )

            if "TASK PASSED" in qa_feedback:
                print(
                    "\nSuccess! The QA Agent verified the engineering solution. Pipeline complete."
                )
                break

            current_iteration += 1
        else:
            print("\nMax iterations reached.")
