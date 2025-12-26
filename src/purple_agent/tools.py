"""Tool implementations for purple agent."""

import json
from typing import Any, Dict
from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        JSON string with search results
    """
    try:
        print(f"[Tool: web_search] Searching for: {query}")
        results = []

        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)
            for r in search_results:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                )

        return json.dumps({"results": results}, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})


def python_calculator(expression: str) -> str:
    """Evaluate a Python mathematical expression safely.

    Args:
        expression: Python expression to evaluate

    Returns:
        Result of the calculation or error message
    """
    try:
        print(f"[Tool: python_calculator] Evaluating: {expression}")

        # Safe eval with limited scope
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "pow": pow,
            "__builtins__": {},
        }

        # Add math functions
        import math

        for name in dir(math):
            if not name.startswith("_"):
                allowed_names[name] = getattr(math, name)

        result = eval(expression, allowed_names, {})
        return json.dumps({"result": result})

    except Exception as e:
        return json.dumps({"error": f"Calculation failed: {str(e)}"})


# Tool definitions for LiteLLM
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information. Use this when you need "
                "up-to-date facts, statistics, or information not in your training data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "python_calculator",
            "description": (
                "Evaluate a Python mathematical expression. Use this for calculations, "
                "math operations, and numeric processing. Supports basic operators (+, -, *, /, **) "
                "and math functions (sin, cos, sqrt, log, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "Python expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                        ),
                    },
                },
                "required": ["expression"],
            },
        },
    },
]
