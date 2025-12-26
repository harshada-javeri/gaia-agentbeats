"""CLI entry point for agentbeats-gaia."""

import typer
import asyncio

from src.green_agent import start_green_agent
from src.purple_agent import start_purple_agent
from src.launcher import launch_evaluation

app = typer.Typer(help="GAIA Benchmark on AgentBeats - General AI Assistants evaluation framework")


@app.command()
def green():
    """Start the green agent (GAIA evaluation orchestrator)."""
    start_green_agent()


@app.command()
def purple():
    """Start the purple agent (GAIA task executor with tools)."""
    start_purple_agent()


@app.command()
def launch(
    level: int = typer.Option(1, help="GAIA difficulty level (1, 2, or 3)"),
    task_ids: str = typer.Option("0", help="Comma-separated task IDs to evaluate"),
    split: str = typer.Option("validation", help="Dataset split: validation or test"),
):
    """Launch the complete GAIA evaluation workflow."""
    task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
    asyncio.run(launch_evaluation(level=level, task_ids=task_id_list, split=split))


if __name__ == "__main__":
    app()
