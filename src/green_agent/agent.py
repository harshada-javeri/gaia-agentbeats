"""Green agent implementation - GAIA evaluation orchestrator."""

import uvicorn
import tomllib
import dotenv
import json
import time
from typing import Dict, Any

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message, get_text_parts

from src.utils.parse_tags import parse_tags
from src.utils import a2a_helpers
from src.utils.gaia_loader import GAIADatasetLoader

dotenv.load_dotenv()


def load_agent_card_toml(agent_name: str) -> Dict[str, Any]:
    """Load agent card from TOML file.

    Args:
        agent_name: Name of the agent

    Returns:
        Agent card dictionary
    """
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)


def normalize_answer(answer: str) -> str:
    """Normalize an answer for comparison.

    Args:
        answer: Answer string

    Returns:
        Normalized answer (lowercase, stripped)
    """
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


async def evaluate_purple_agent_on_task(
    purple_agent_url: str, task: Dict[str, Any], max_turns: int = 5
) -> Dict[str, Any]:
    """Evaluate purple agent on a GAIA task.

    Args:
        purple_agent_url: URL of the purple agent
        task: GAIA task dictionary
        max_turns: Maximum conversation turns

    Returns:
        Evaluation results dictionary
    """
    question = task["Question"]
    ground_truth = task.get("Final answer", None)
    task_id = task.get("task_id", "unknown")

    print(f"\n[Green Agent] Evaluating task {task_id}")
    print(f"[Green Agent] Question: {question}")

    # Prepare task message for purple agent
    task_message = f"""You are solving a GAIA benchmark task. Provide your final answer clearly.

Question: {question}

Use the available tools (web_search, python_calculator) as needed to solve this task.
Once you have the answer, provide it in this format:
<answer>YOUR_ANSWER_HERE</answer>"""

    # Send to purple agent
    print(f"[Green Agent] Sending task to purple agent at {purple_agent_url}")
    start_time = time.time()

    try:
        response = await a2a_helpers.send_message(purple_agent_url, task_message)
        elapsed_time = time.time() - start_time

        # Extract response
        res_root = response.root
        assert isinstance(res_root, SendMessageSuccessResponse)
        res_result = res_root.result
        assert isinstance(res_result, Message)

        text_parts = get_text_parts(res_result.parts)
        assert len(text_parts) > 0, "No text response from purple agent"

        purple_response = text_parts[0]
        print(f"[Green Agent] Purple agent response: {purple_response[:200]}...")

        # Extract answer
        tags = parse_tags(purple_response)
        predicted_answer = tags.get("answer", purple_response)

        # Check correctness (if ground truth available)
        is_correct = None
        if ground_truth:
            is_correct = check_answer_correctness(predicted_answer, ground_truth)
            print(f"[Green Agent] Correctness: {is_correct}")
            print(f"[Green Agent] Predicted: {predicted_answer}")
            print(f"[Green Agent] Ground truth: {ground_truth}")

        return {
            "task_id": task_id,
            "question": question,
            "predicted_answer": predicted_answer,
            "ground_truth": ground_truth,
            "is_correct": is_correct,
            "elapsed_time": elapsed_time,
            "full_response": purple_response,
        }

    except Exception as e:
        print(f"[Green Agent] Error evaluating task: {e}")
        return {
            "task_id": task_id,
            "question": question,
            "error": str(e),
            "is_correct": False,
            "elapsed_time": time.time() - start_time,
        }


class GAIAGreenAgentExecutor(AgentExecutor):
    """Executor for green agent - orchestrates GAIA evaluation."""

    def __init__(self):
        self.loader = GAIADatasetLoader()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute GAIA evaluation workflow.

        Expected user input format:
        <purple_agent_url>http://localhost:9002</purple_agent_url>
        <eval_config>
        {
            "level": 1,
            "split": "validation",
            "task_indices": [0, 1, 2]
        }
        </eval_config>
        """
        print("[Green Agent] Received evaluation request")
        user_input = context.get_user_input()

        # Parse task configuration
        tags = parse_tags(user_input)
        purple_agent_url = tags["purple_agent_url"]
        eval_config_str = tags["eval_config"]
        eval_config = json.loads(eval_config_str)

        level = eval_config["level"]
        split = eval_config["split"]
        task_indices = eval_config["task_indices"]

        print(f"[Green Agent] Configuration:")
        print(f"  Level: {level}")
        print(f"  Split: {split}")
        print(f"  Task indices: {task_indices}")

        # Load tasks
        print("[Green Agent] Loading GAIA tasks...")
        tasks = self.loader.get_task_batch(level, split, task_indices)
        print(f"[Green Agent] Loaded {len(tasks)} tasks")

        # Evaluate each task
        results = []
        for task in tasks:
            result = await evaluate_purple_agent_on_task(purple_agent_url, task)
            results.append(result)

        # Compute metrics
        total_tasks = len(results)
        correct_tasks = sum(1 for r in results if r.get("is_correct") is True)
        error_tasks = sum(1 for r in results if "error" in r)
        avg_time = sum(r.get("elapsed_time", 0) for r in results) / max(
            total_tasks, 1
        )

        accuracy = correct_tasks / total_tasks if total_tasks > 0 else 0.0

        # Prepare summary
        summary = {
            "level": level,
            "split": split,
            "total_tasks": total_tasks,
            "correct": correct_tasks,
            "errors": error_tasks,
            "accuracy": accuracy,
            "avg_time_seconds": avg_time,
            "results": results,
        }

        print("\n[Green Agent] ===== EVALUATION COMPLETE =====")
        print(f"Accuracy: {accuracy:.2%} ({correct_tasks}/{total_tasks})")
        print(f"Errors: {error_tasks}")
        print(f"Average time: {avg_time:.2f}s")

        # Send results
        summary_text = f"""GAIA Evaluation Complete ✅

Level: {level}
Split: {split}
Tasks evaluated: {total_tasks}
Correct: {correct_tasks}
Accuracy: {accuracy:.2%}
Errors: {error_tasks}
Average time: {avg_time:.2f}s

Detailed results:
{json.dumps(summary, indent=2)}
"""

        await event_queue.enqueue_event(new_agent_text_message(summary_text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not implemented)."""
        raise NotImplementedError


def start_green_agent(
    agent_name: str = "gaia_green_agent", host: str = "localhost", port: int = 9001
):
    """Start the green agent server.

    Args:
        agent_name: Name of the agent
        host: Host to bind to
        port: Port to bind to
    """
    print(f"Starting green agent on {host}:{port}...")
    agent_card_dict = load_agent_card_toml(agent_name)
    url = f"http://{host}:{port}"
    agent_card_dict["url"] = url

    request_handler = DefaultRequestHandler(
        agent_executor=GAIAGreenAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
