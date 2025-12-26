# GAIA Benchmark on AgentBeats

**General AI Assistants Benchmark** - Evaluating AI agents on real-world questions requiring multi-step reasoning, tool use, and web search.

## Overview

This is an **agentified** implementation of the [GAIA Benchmark](https://huggingface.co/gaia-benchmark) on the [AgentBeats](https://agentbeats.org) platform. GAIA proposes 450+ real-world questions that require fundamental abilities such as:

- 🧠 Multi-step reasoning
- 🔍 Web browsing and search
- 🧮 Mathematical calculations
- 📄 Multimodal processing (text, images, documents, audio)
- 🛠️ Tool use proficiency

### Why GAIA?

GAIA questions are **conceptually simple for humans yet challenging for most advanced AIs**:
- Human respondents: **92% accuracy**
- GPT-4 with plugins: **15% accuracy**

This benchmark provides a realistic evaluation of general AI assistant capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Green Agent (Evaluation Orchestrator)                  │
│  - Loads GAIA tasks from Hugging Face                   │
│  - Sends tasks to purple agent                          │
│  - Scores responses against ground truth                │
│  - Computes accuracy metrics                            │
└────────────────┬────────────────────────────────────────┘
                 │ A2A Protocol
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Purple Agent (Task Executor)                           │
│  - Receives GAIA task questions                         │
│  - Uses tools: web_search, python_calculator            │
│  - Performs multi-step reasoning                        │
│  - Returns final answer                                 │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

1. **OpenAI API Key** - for agent reasoning (GPT-4o)
2. **Hugging Face Token** - for GAIA dataset access
   - Get access at: https://huggingface.co/datasets/gaia-benchmark/GAIA
   - Create token at: https://huggingface.co/settings/tokens

### Option 1: Docker (Recommended for Competition)

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your API keys

# 2. Build and run
docker-compose up --build

# The agents will start on:
# - Green agent: http://localhost:9001
# - Purple agent: http://localhost:9002
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip install -e .

# Or with uv (faster):
uv sync

# 2. Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export HF_TOKEN="your-huggingface-token"

# 3. Launch complete evaluation
python main.py launch --level 1 --task-ids "0,1,2" --split validation

# Or run agents separately:
python main.py green    # Terminal 1: Start green agent
python main.py purple   # Terminal 2: Start purple agent
```

## Usage Examples

### Evaluate Specific Tasks

```bash
# Evaluate first 3 tasks from Level 1 validation set
python main.py launch --level 1 --task-ids "0,1,2" --split validation

# Evaluate single task from Level 2
python main.py launch --level 2 --task-ids "5" --split validation

# Evaluate harder tasks (Level 3)
python main.py launch --level 3 --task-ids "0,1" --split validation
```

### Using the Python API

```python
from src.launcher import launch_evaluation

# Launch evaluation programmatically
await launch_evaluation(
    level=1,
    task_ids=[0, 1, 2, 3, 4],
    split="validation"
)
```

## GAIA Dataset Structure

### Difficulty Levels

- **Level 1**: Solvable by "very good LLMs" (most tasks require 1-2 steps)
- **Level 2**: Moderate complexity (multi-step reasoning required)
- **Level 3**: Strong jump in model capabilities needed (complex tool orchestration)

### Task Fields

Each GAIA task contains:

```json
{
  "task_id": "unique_identifier",
  "Question": "The question to answer",
  "Level": "1, 2, or 3",
  "Final answer": "Ground truth answer",
  "file_name": "optional_file.pdf",
  "file_path": "path/to/file",
  "Annotator Metadata": {...}
}
```

## Purple Agent Tools

The purple agent has access to:

### 1. Web Search (`web_search`)

Search the web using DuckDuckGo for current information.

```python
# Example usage in agent
web_search(query="current GDP of France", max_results=5)
```

### 2. Python Calculator (`python_calculator`)

Evaluate mathematical expressions safely.

```python
# Example usage in agent
python_calculator(expression="sqrt(144) + log(100)")
```

## Evaluation Metrics

The green agent computes:

- **Accuracy**: % of correct answers
- **Total Tasks**: Number of tasks evaluated
- **Correct**: Number of correctly answered tasks
- **Errors**: Number of tasks that failed
- **Average Time**: Mean time per task (seconds)

### Answer Matching

Answers are normalized and compared:
- Exact string match (case-insensitive)
- Numeric match (with tolerance of 0.01)

## Project Structure

```
gaia/
├── .scenario/                    # AgentBeats scenario metadata
│   ├── scenario.toml            # Scenario configuration
│   ├── green_agent_card.toml    # Green agent card
│   └── purple_agent_card.toml   # Purple agent card
├── src/
│   ├── green_agent/             # Evaluation orchestrator
│   │   ├── agent.py
│   │   └── gaia_green_agent.toml
│   ├── purple_agent/            # Task executor with tools
│   │   ├── agent.py
│   │   └── tools.py
│   ├── utils/                   # Shared utilities
│   │   ├── a2a_helpers.py       # A2A protocol helpers
│   │   ├── gaia_loader.py       # Dataset loading
│   │   └── parse_tags.py        # XML tag parsing
│   └── launcher.py              # Evaluation coordinator
├── main.py                       # CLI entry point
├── pyproject.toml               # Python dependencies
├── Dockerfile                    # Docker build config
├── docker-compose.yml           # Docker orchestration
├── entrypoint.sh                # Docker entrypoint
├── requirements.txt             # Additional dependencies
└── README.md                     # This file
```

## Development

### Adding New Tools

1. Define tool function in `src/purple_agent/tools.py`:

```python
def my_new_tool(param: str) -> str:
    """Tool description."""
    # Implementation
    return result
```

2. Add tool definition to `TOOL_DEFINITIONS`:

```python
TOOL_DEFINITIONS.append({
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "What this tool does",
        "parameters": {...}
    }
})
```

3. Update `execute_tool_call()` in `purple_agent/agent.py`

### Customizing Evaluation

Modify `src/green_agent/agent.py`:

- `check_answer_correctness()` - Answer matching logic
- `evaluate_purple_agent_on_task()` - Task evaluation workflow
- `GAIAGreenAgentExecutor.execute()` - Overall orchestration

## Troubleshooting

### HF_TOKEN Error

```
ValueError: HF_TOKEN environment variable required
```

**Solution**: Get dataset access at https://huggingface.co/datasets/gaia-benchmark/GAIA and set your token.

### Web Search Fails

```
{"error": "Search failed: ..."}
```

**Solution**: DuckDuckGo may be rate-limiting. Wait a few seconds between searches.

### Import Errors

```
ModuleNotFoundError: No module named 'a2a'
```

**Solution**: Install dependencies: `pip install -e .` or `uv sync`

## Performance Tips

1. **Use GPT-4o or better** - Smaller models struggle with GAIA tasks
2. **Enable tool use** - Most tasks require web search or calculations
3. **Increase max_iterations** - Complex tasks may need >10 tool calls
4. **Cache dataset** - First load downloads ~100MB, subsequent loads are cached

## Citation

If you use GAIA benchmark, please cite:

```bibtex
@article{gaia2023,
  title={GAIA: a benchmark for General AI Assistants},
  author={Mialon, Grégoire and others},
  journal={arXiv preprint arXiv:2311.12983},
  year={2023}
}
```

## Resources

- **GAIA Benchmark**: https://huggingface.co/datasets/gaia-benchmark/GAIA
- **GAIA Leaderboard**: https://huggingface.co/spaces/gaia-benchmark/leaderboard
- **AgentBeats Platform**: https://agentbeats.org
- **A2A Protocol**: https://github.com/agentbeats/a2a-sdk

## License

This implementation follows AgentBeats licensing. GAIA dataset has its own license terms.

## Contributing

Contributions welcome! Key areas:

- [ ] Add more tools (file reading, image analysis)
- [ ] Improve answer matching logic
- [ ] Support test split evaluation
- [ ] Add multimodal capabilities
- [ ] Optimize for AgentX-AgentBeats competition

---

Built with ❤️ for the AgentX-AgentBeats Competition by Berkeley RDI
