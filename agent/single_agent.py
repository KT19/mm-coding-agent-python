from agent.base import BaseAgent
from agent.state import AgentState
from core.engine import OllamaEngine
from tools.tool_registry import ALLOCATED_TOOLS, TOOL_MANIFEST


class SingleAgent(BaseAgent):
    def __init__(self, user_task: str, host: str, model: str, max_steps: int = 5) -> None:
        self.state = AgentState(task=user_task, max_steps=max_steps)
        self.engine = OllamaEngine(host=host, model=model)
        self.tool_list = TOOL_MANIFEST

    def _compile_debugging_directive(self, tool_name: str, error_log: str) -> str:
        """
        Generates a strict systemic directive when a tool execution returns a failure state.
        This forces the model to prioritize fixing the error over starting new tasks.
        """
        return (
            f"SYSTEM ALERT: Tool '{tool_name}' failed during execution.\n"
            f"===RAW ERROR LOG===\n{error_log}\n=========\n"
            f"CRITICAL INSTRUCTION:\n"
            f"1. Analyze the stack trace or error state about immediately.\n"
            f"2. Identify why your previous implementation failed.\n"
            f"3. Do not run the same code unaltered. Use your tools to patch, overwrite, "
            f"or rewrite the necessary files to fix this specific issue."
        )

    async def step(self) -> None:
        print(f"\n[Step {self.state.current_step} / {self.state.max_steps}] Querying Engine...")

        # Ask model for next action
        response = await self.engine.generate_chat(
            messages=self.state.messages, tools=self.tool_list
        )

        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])

        # append assistant response directly to state tracking
        self.state.add_message(role="assistant", content=content, tool_calls=tool_calls)
        if content:
            print(f"Agent Thought: {content}")

        if tool_calls:
            for call in tool_calls:
                func_name = call.function.name
                func_args = call.function.arguments
                print(f"Invoking Native Tool: {func_name}({func_args})")

                if func_name in ALLOCATED_TOOLS:
                    try:
                        observation = ALLOCATED_TOOLS[func_name](**func_args)
                    except Exception as e:
                        observation = f"Error: Tool '{func_name}' raised {type(e).__name__}: {e}"

                    is_sandbox_error = (
                        "Exit Code:" in observation and "Exit Code: 0" not in observation
                    )
                    is_generic_error = observation.startswith("Error:")

                    if is_sandbox_error or is_generic_error:
                        print(
                            "[Self-Correction] Intercepted runtime failure. Applying debugging directive..."
                        )
                        # Wrap the raw observation in our strict correction prompt
                        directive = self._compile_debugging_directive(func_name, observation)
                        self.state.add_tool_response(tool_name=func_name, content=directive)

                    elif isinstance(observation, str) and observation.startswith(
                        "__ATTACH_IMAGE_SIGNAL__"
                    ):
                        # Visual hook
                        image_path = observation.split(":", 1)[1]

                        self.state.add_image_tool_response(
                            tool_name=func_name,
                            content=f"System: Image file '{image_path}' has been successfully rendered and rendered to your optic sensors below.",
                            image_path=image_path,
                        )
                    else:
                        print(f"Tool Observation: {observation}")
                        self.state.add_tool_response(tool_name=func_name, content=observation)
                else:
                    error_msg = f"Error: Tool '{func_name}' is not registered."
                    self.state.add_tool_response(tool_name=func_name, content=error_msg)
        else:
            print("No further actions requested by agent. Wrapping up.")
            self.state.is_complete = True

        self.state.current_step += 1
        if self.state.current_step > self.state.max_steps:
            self.state.is_complete = True

    async def run(self):
        while not self.state.is_complete:
            await self.step()
        print("\n--- MultiModal Coding Agent Execution Finished ---")
