"""
GAIA Evaluator - Green agent that runs GAIA benchmark evaluation on purple agents.

This agent:
1. Loads GAIA tasks from Hugging Face
2. Sends questions to the purple agent (the agent being tested)
3. Parses responses and extracts answers
4. Scores against ground truth and collects metrics
"""
import argparse
import asyncio
import json
import logging
import time
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    DataPart,
    Part,
    TaskState,
    TextPart,
)
from a2a.utils import new_agent_text_message

from agentbeats.green_executor import GreenAgent, GreenExecutor
from agentbeats.models import EvalRequest
from agentbeats.tool_provider import ToolProvider

from src.utils.parse_tags import parse_tags
from src.utils.gaia_loader import GAIADatasetLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gaia_evaluator")


def normalize_answer(answer: str) -> str:
    """Normalize an answer for comparison."""
    return answer.strip().lower()


def check_answer_correctness(
    predicted: str, ground_truth: str, tolerance: float = 0.01
) -> bool:
    """Check if predicted answer matches ground truth.

    Args:
        predicted: Predicted answer
        ground_truth: Ground truth answer
        tolerance: Numeric tolerance for floating point comparison

    Returns:
        True if answers match
    """
    pred_norm = normalize_answer(predicted)
    gt_norm = normalize_answer(ground_truth)

    # Exact match
    if pred_norm == gt_norm:
        return True

    # Try numeric comparison
    try:
        pred_num = float(pred_norm)
        gt_num = float(gt_norm)
        return abs(pred_num - gt_num) <= tolerance
    except (ValueError, TypeError):
        pass

    return False


class GAIAEvaluator(GreenAgent):
    """Green agent that evaluates purple agents using GAIA benchmark."""

    def __init__(self):
        self._required_roles = ["executor"]  # The purple agent being tested
        self._required_config_keys = ["level", "split"]
        self._tool_provider = ToolProvider()
        self._loader = GAIADatasetLoader()

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        missing_roles = set(self._required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Missing roles: {missing_roles}"
        missing_config_keys = set(self._required_config_keys) - set(request.config.keys())
        if missing_config_keys:
            return False, f"Missing config keys: {missing_config_keys}"
        return True, "ok"

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        logger.info(f"Starting GAIA evaluation: {req}")
        start_time = time.time()

        level = req.config["level"]
        split = req.config["split"]
        task_indices = req.config.get("task_indices", [0])

        # Get the purple agent URL
        executor_url = str(req.participants["executor"])

        logger.info(f"Evaluating {len(task_indices)} tasks - Level {level}, Split: {split}")

        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                f"Starting GAIA evaluation: Level {level}, {len(task_indices)} tasks"
            )
        )

        metrics: Dict[str, Any] = {"tasks": {}}

        try:
            # Load tasks
            tasks = self._loader.get_task_batch(level, split, task_indices)
            logger.info(f"Loaded {len(tasks)} tasks from GAIA dataset")

            for task in tasks:
                task_id = task.get("task_id", "unknown")
                logger.info(f"Running task {task_id}...")
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"Running task {task_id}...")
                )

                try:
                    result = await self._run_single_task(
                        executor_url=executor_url,
                        task=task,
                    )
                    metrics["tasks"][task_id] = result
                    logger.info(f"Task {task_id} completed: {result.get('is_correct')}")
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    metrics["tasks"][task_id] = {
                        "task_id": task_id,
                        "error": str(e),
                        "is_correct": False,
                    }

            # Compute final metrics
            time_used = time.time() - start_time
            total_tasks = len(metrics["tasks"])
            correct_tasks = sum(
                1 for r in metrics["tasks"].values() if r.get("is_correct") is True
            )
            error_tasks = sum(
                1 for r in metrics["tasks"].values() if "error" in r
            )
            accuracy = (correct_tasks / total_tasks * 100) if total_tasks > 0 else 0
            avg_time = time_used / total_tasks if total_tasks > 0 else 0

            result_data = {
                "level": level,
                "split": split,
                "score": correct_tasks,
                "max_score": total_tasks,
                "accuracy": accuracy,
                "errors": error_tasks,
                "task_results": metrics["tasks"],
                "time_used": time_used,
                "avg_time": avg_time,
            }

            # Format task results for display
            task_results_str = "\n".join(
                f"  {task_id}: {'✓' if result.get('is_correct') else '✗'}"
                for task_id, result in metrics["tasks"].items()
            )

            summary = f"""GAIA Benchmark Results
Level: {level}
Split: {split}
Tasks: {total_tasks}
Accuracy: {accuracy:.1f}% ({correct_tasks}/{total_tasks})
Errors: {error_tasks}
Time: {time_used:.1f}s (avg: {avg_time:.1f}s/task)

Task Results:
{task_results_str}"""

            await updater.add_artifact(
                parts=[
                    Part(root=TextPart(text=summary)),
                    Part(root=DataPart(data=result_data)),
                ],
                name="Result",
            )

        finally:
            self._tool_provider.reset()

    async def _run_single_task(
        self,
        executor_url: str,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a single GAIA task and return the result."""

        question = task["Question"]
        ground_truth = task.get("Final answer", None)
        task_id = task.get("task_id", "unknown")

        logger.info(f"Task {task_id}: {question[:100]}...")

        # Build task prompt for purple agent
        task_prompt = f"""You are solving a GAIA benchmark task. Provide your final answer clearly.

Question: {question}

Use the available tools (web_search, python_calculator) as needed to solve this task.
Once you have the answer, provide it in this format:
<answer>YOUR_ANSWER_HERE</answer>"""

        # Send to purple agent
        start_time = time.time()

        try:
            response = await self._tool_provider.talk_to_agent(
                message=task_prompt,
                url=executor_url,
                new_conversation=True,  # Each task is a fresh conversation
            )

            elapsed_time = time.time() - start_time

            logger.debug(f"Purple agent response: {response[:200]}...")

            # Extract answer from <answer>...</answer> tags
            tags = parse_tags(response)
            predicted_answer = tags.get("answer", response)

            # Check correctness
            is_correct = None
            if ground_truth:
                is_correct = check_answer_correctness(predicted_answer, ground_truth)
                logger.info(f"Predicted: {predicted_answer}, Ground truth: {ground_truth}, Correct: {is_correct}")

            return {
                "task_id": task_id,
                "question": question,
                "predicted_answer": predicted_answer,
                "ground_truth": ground_truth,
                "is_correct": is_correct,
                "elapsed_time": elapsed_time,
                "full_response": response,
            }

        except Exception as e:
            logger.error(f"Error evaluating task: {e}")
            return {
                "task_id": task_id,
                "question": question,
                "error": str(e),
                "is_correct": False,
                "elapsed_time": time.time() - start_time,
            }


def gaia_evaluator_agent_card(name: str, url: str) -> AgentCard:
    """Create the agent card for the GAIA evaluator."""
    skill = AgentSkill(
        id="gaia_evaluation",
        name="GAIA Benchmark Evaluation",
        description="Evaluates agents on GAIA (General AI Assistants) benchmark tasks requiring multi-step reasoning, web search, and tool use",
        tags=["benchmark", "evaluation", "gaia", "reasoning"],
        examples=[
            '{"participants": {"executor": "http://localhost:9002"}, "config": {"level": 1, "split": "validation", "task_indices": [0, 1, 2]}}'
        ],
    )
    return AgentCard(
        name=name,
        description="GAIA benchmark evaluator - tests agents on general AI assistant tasks",
        url=url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )


async def main():
    parser = argparse.ArgumentParser(description="Run the GAIA evaluator agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9001, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="External URL for the agent card")
    args = parser.parse_args()

    agent_url = args.card_url or f"http://{args.host}:{args.port}/"

    agent = GAIAEvaluator()
    executor = GreenExecutor(agent)
    agent_card = gaia_evaluator_agent_card("GAIAEvaluator", agent_url)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn_config = uvicorn.Config(server.build(), host=args.host, port=args.port)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
