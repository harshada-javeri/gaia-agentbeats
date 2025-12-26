"""Purple agent implementation - GAIA task executor with web search and tool use."""

import uvicorn
import dotenv
import json
from typing import List, Dict, Any

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from a2a.utils import new_agent_text_message
from litellm import completion

from .tools import web_search, python_calculator, TOOL_DEFINITIONS

dotenv.load_dotenv()


def prepare_purple_agent_card(url: str) -> AgentCard:
    """Create agent card for purple (task executor) agent.

    Args:
        url: Agent's URL

    Returns:
        Configured AgentCard
    """
    skill = AgentSkill(
        id="gaia_task_execution",
        name="GAIA Task Execution",
        description=(
            "Executes GAIA benchmark tasks requiring multi-step reasoning, "
            "web search, calculation, and file analysis"
        ),
        tags=["gaia", "reasoning", "tools", "multimodal"],
        examples=[
            "Search the web for current information",
            "Perform calculations on numerical data",
            "Reason through multi-step problems",
        ],
    )

    card = AgentCard(
        name="gaia_purple_agent",
        description=(
            "Purple agent for GAIA benchmark - executes complex tasks "
            "with web search, calculation, and reasoning capabilities"
        ),
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
    )
    return card


def execute_tool_call(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Execute a tool call and return results.

    Args:
        tool_name: Name of the tool to call
        tool_args: Arguments for the tool

    Returns:
        Tool execution result as string
    """
    if tool_name == "web_search":
        return web_search(**tool_args)
    elif tool_name == "python_calculator":
        return python_calculator(**tool_args)
    else:
        return f"Error: Unknown tool '{tool_name}'"


class PurpleAgentExecutor(AgentExecutor):
    """Executor for purple agent with tool-calling capabilities."""

    def __init__(self, model: str = "openai/gpt-4o", temperature: float = 0.0):
        """Initialize purple agent executor.

        Args:
            model: LLM model to use
            temperature: Sampling temperature
        """
        self.model = model
        self.temperature = temperature
        self.ctx_id_to_messages: Dict[str, List[Dict[str, Any]]] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute a GAIA task with tool use.

        Args:
            context: Request context
            event_queue: Event queue for responses
        """
        user_input = context.get_user_input()
        ctx_id = context.context_id

        # Initialize conversation history for this context
        if ctx_id not in self.ctx_id_to_messages:
            self.ctx_id_to_messages[ctx_id] = []

        messages = self.ctx_id_to_messages[ctx_id]
        messages.append({"role": "user", "content": user_input})

        # Multi-turn tool calling loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM with tools
            response = completion(
                messages=messages,
                model=self.model,
                custom_llm_provider="openai",
                temperature=self.temperature,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message  # type: ignore
            messages.append(assistant_message.model_dump())

            # Check if tool calls are needed
            tool_calls = getattr(assistant_message, "tool_calls", None)

            if not tool_calls:
                # No more tool calls, return final answer
                final_content = assistant_message.content or ""
                await event_queue.enqueue_event(
                    new_agent_text_message(final_content, context_id=ctx_id)
                )
                break

            # Execute all tool calls
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"[Purple Agent] Calling tool: {tool_name}")
                print(f"[Purple Agent] Arguments: {tool_args}")

                # Execute the tool
                tool_result = execute_tool_call(tool_name, tool_args)

                print(f"[Purple Agent] Result: {tool_result[:200]}...")

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result,
                    }
                )

        if iteration >= max_iterations:
            await event_queue.enqueue_event(
                new_agent_text_message(
                    "Maximum iterations reached. Unable to complete task.",
                    context_id=ctx_id,
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not implemented)."""
        raise NotImplementedError


def start_purple_agent(
    agent_name: str = "gaia_purple_agent", host: str = "localhost", port: int = 9002
):
    """Start the purple agent server.

    Args:
        agent_name: Name of the agent
        host: Host to bind to
        port: Port to bind to
    """
    print(f"Starting purple agent on {host}:{port}...")
    url = f"http://{host}:{port}"
    card = prepare_purple_agent_card(url)

    request_handler = DefaultRequestHandler(
        agent_executor=PurpleAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
