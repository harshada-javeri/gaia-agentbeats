"""Launcher module - initiates and coordinates GAIA evaluation."""

import multiprocessing
import json
from typing import List

from src.green_agent.agent import start_green_agent
from src.purple_agent.agent import start_purple_agent
from src.utils import a2a_helpers


async def launch_evaluation(level: int = 1, task_ids: List[int] = None, split: str = "validation"):
    """Launch complete GAIA evaluation workflow.

    Args:
        level: GAIA difficulty level (1, 2, or 3)
        task_ids: List of task indices to evaluate (default: [0])
        split: Dataset split ('validation' or 'test')
    """
    if task_ids is None:
        task_ids = [0]

    print("=" * 60)
    print("GAIA Benchmark Evaluation on AgentBeats")
    print("=" * 60)

    # Start green agent (evaluation orchestrator)
    print("\n[Launcher] Starting green agent...")
    green_address = ("localhost", 9001)
    green_url = f"http://{green_address[0]}:{green_address[1]}"
    p_green = multiprocessing.Process(
        target=start_green_agent, args=("gaia_green_agent", *green_address)
    )
    p_green.start()

    if not await a2a_helpers.wait_agent_ready(green_url, timeout=15):
        print("[Launcher] ERROR: Green agent not ready in time")
        p_green.terminate()
        p_green.join()
        return

    print("[Launcher] ✅ Green agent ready")

    # Start purple agent (task executor)
    print("\n[Launcher] Starting purple agent...")
    purple_address = ("localhost", 9002)
    purple_url = f"http://{purple_address[0]}:{purple_address[1]}"
    p_purple = multiprocessing.Process(
        target=start_purple_agent, args=("gaia_purple_agent", *purple_address)
    )
    p_purple.start()

    if not await a2a_helpers.wait_agent_ready(purple_url, timeout=15):
        print("[Launcher] ERROR: Purple agent not ready in time")
        p_green.terminate()
        p_green.join()
        p_purple.terminate()
        p_purple.join()
        return

    print("[Launcher] ✅ Purple agent ready")

    # Send evaluation task to green agent
    print(f"\n[Launcher] Configuring evaluation:")
    print(f"  Level: {level}")
    print(f"  Split: {split}")
    print(f"  Task IDs: {task_ids}")

    eval_config = {
        "level": level,
        "split": split,
        "task_indices": task_ids,
    }

    task_text = f"""
<purple_agent_url>
{purple_url}
</purple_agent_url>
<eval_config>
{json.dumps(eval_config, indent=2)}
</eval_config>
    """

    print("\n[Launcher] Sending evaluation request to green agent...")
    try:
        response = await a2a_helpers.send_message(green_url, task_text)
        print("\n[Launcher] Evaluation response:")
        print("=" * 60)
        print(response)
        print("=" * 60)
    except Exception as e:
        print(f"\n[Launcher] ERROR during evaluation: {e}")

    # Cleanup
    print("\n[Launcher] Terminating agents...")
    p_green.terminate()
    p_green.join()
    p_purple.terminate()
    p_purple.join()
    print("[Launcher] ✅ Agents terminated")
    print("\n" + "=" * 60)
    print("GAIA Evaluation Complete")
    print("=" * 60)
