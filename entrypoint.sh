#!/usr/bin/env bash

set -e

echo "==================================================="
echo "GAIA Benchmark on AgentBeats - Starting..."
echo "==================================================="

# Parse scenario.toml to get first launcher_port and set it to HEALTHCHECK_PORT
export HEALTHCHECK_PORT=$(python - <<'PY'
import tomllib, os, pathlib, sys
scenario_path = os.path.join(os.environ['SCENARIO_ROOT'], '.scenario', 'scenario.toml')
if os.path.exists(scenario_path):
    data = tomllib.load(open(scenario_path, 'rb'))
    print(data['agents'][0]['launcher_port'])
else:
    print(9001)  # default to green agent port
PY
)

echo "Health check port: $HEALTHCHECK_PORT"

# Install custom requirements if present
if [ -f /workspace/requirements.txt ]; then
  echo "Installing additional requirements..."
  pip install -r /workspace/requirements.txt
fi

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
  echo "WARNING: OPENAI_API_KEY not set. Agent may not function properly."
fi

if [ -z "$HF_TOKEN" ]; then
  echo "WARNING: HF_TOKEN not set. GAIA dataset loading will fail."
  echo "Get access at: https://huggingface.co/datasets/gaia-benchmark/GAIA"
fi

# Load scenario using AgentBeats CLI
echo "Loading GAIA scenario..."
exec ab load_scenario "$SCENARIO_ROOT/.scenario"
