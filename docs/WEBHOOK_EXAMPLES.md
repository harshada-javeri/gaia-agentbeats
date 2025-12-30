# GitHub Webhook Submission Examples

This document provides practical examples for submitting GAIA benchmark results via GitHub webhooks.

## Example 1: Submit via Commit Message

When you push code with evaluation results:

```bash
#!/bin/bash
# eval_and_submit.sh - Run evaluation and submit results

set -e

echo "Running GAIA evaluation..."
python main.py launch --level 1 --task-ids "0,1,2,3,4,5" --split validation

# Capture results from evaluation output
# In a real scenario, you'd parse actual results

AGENT_NAME="my-agent-v2"
AGENT_VERSION="2.0.0"
TEAM_NAME="my-team"
ACCURACY=85.0
CORRECT=25
TOTAL=30
AVG_TIME=2.1
TOTAL_TIME=63.0

# Create config JSON
CONFIG="{
  \"gaia_submission\": {
    \"agent_name\": \"$AGENT_NAME\",
    \"agent_version\": \"$AGENT_VERSION\",
    \"team_name\": \"$TEAM_NAME\",
    \"level\": 1,
    \"split\": \"validation\",
    \"accuracy\": $ACCURACY,
    \"correct_tasks\": $CORRECT,
    \"total_tasks\": $TOTAL,
    \"average_time_per_task\": $AVG_TIME,
    \"total_time_seconds\": $TOTAL_TIME,
    \"model_used\": \"gpt-4o\",
    \"environment\": \"docker\"
  }
}"

# Commit with config in message
git add .
git commit -m "Benchmark evaluation results

$CONFIG
"

git push origin main
```

## Example 2: Submit via Pull Request

Create a PR with results in the description:

```markdown
# Agent Improvement PR

## Changes
- Improved reasoning chain with better tool selection
- Added retry logic for failed web searches
- Optimized prompt templates

## Benchmark Results

```json
{
  "gaia_submission": {
    "agent_name": "improved-agent",
    "agent_version": "2.1.0",
    "team_name": "ml-team",
    "level": 1,
    "split": "validation",
    "accuracy": 88.5,
    "correct_tasks": 26,
    "total_tasks": 30,
    "average_time_per_task": 2.05,
    "total_time_seconds": 61.5,
    "model_used": "gpt-4o",
    "environment": "docker"
  }
}
```

## Performance Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 88.5% |
| Correct Tasks | 26/30 |
| Avg Time/Task | 2.05s |
| Total Time | 61.5s |

Closes #123
```

## Example 3: CI/CD Pipeline Integration (GitHub Actions)

```yaml
# .github/workflows/benchmark.yml
name: GAIA Benchmark Evaluation

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
    
    - name: Run GAIA Benchmark
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
      run: |
        python main.py launch --level 1 --task-ids "0,1,2,3,4,5" --split validation > eval_results.json
    
    - name: Parse results and create submission JSON
      id: parse_results
      run: |
        python - << 'EOF'
        import json
        import os
        
        # Parse evaluation results
        with open('eval_results.json', 'r') as f:
          results = json.load(f)
        
        # Extract metrics
        accuracy = results.get('accuracy', 0)
        correct = results.get('score', 0)
        total = results.get('max_score', 30)
        avg_time = results.get('avg_time', 0)
        total_time = results.get('time_used', 0)
        
        # Create submission
        submission = {
          "gaia_submission": {
            "agent_name": os.getenv("AGENT_NAME", "ci-agent"),
            "agent_version": os.getenv("GITHUB_SHA", "0.0.0")[:7],
            "team_name": "agentbeats-ci",
            "level": 1,
            "split": "validation",
            "accuracy": accuracy,
            "correct_tasks": correct,
            "total_tasks": total,
            "average_time_per_task": avg_time,
            "total_time_seconds": total_time,
            "model_used": "gpt-4o",
            "environment": "github-actions"
          }
        }
        
        # Save to environment variable
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
          f.write(f'submission_json={json.dumps(submission)}\n')
        EOF
      env:
        AGENT_NAME: my-agent
    
    - name: Create Pull Request with results
      if: github.event_name == 'push'
      uses: peter-evans/create-pull-request@v5
      with:
        commit-message: "Benchmark: Automated evaluation results"
        title: "Benchmark Results - ${{ github.sha }}"
        body: |
          ## Automated Benchmark Evaluation
          
          ${{ steps.parse_results.outputs.submission_json }}
        branch: benchmark-results/${{ github.sha }}
    
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const submission = ${{ steps.parse_results.outputs.submission_json }};
          const { gaia_submission: sub } = submission;
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## 📊 Benchmark Results
          
          \`\`\`json
          ${JSON.stringify(submission, null, 2)}
          \`\`\`
          
          **Accuracy**: ${sub.accuracy.toFixed(1)}% (${sub.correct_tasks}/${sub.total_tasks})
          **Avg Time**: ${sub.average_time_per_task.toFixed(2)}s/task
          `
          });
```

## Example 4: Docker Build and Benchmark

```dockerfile
# Dockerfile.benchmark
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV HF_TOKEN=${HF_TOKEN}

# Run benchmark and save results
RUN python main.py launch --level 1 --task-ids "0,1,2,3,4,5" > /app/results.json

# Output results
CMD cat /app/results.json
```

```bash
# Build and run benchmark
docker build --build-arg OPENAI_API_KEY=$OPENAI_API_KEY \
             --build-arg HF_TOKEN=$HF_TOKEN \
             -f Dockerfile.benchmark \
             -t gaia-benchmark .

docker run gaia-benchmark > eval_results.json

# Create submission with results
git add eval_results.json
git commit -m "Benchmark results from Docker

$(python -c "
import json
with open('eval_results.json') as f:
    r = json.load(f)
sub = {
    'gaia_submission': {
        'agent_name': 'docker-agent',
        'agent_version': '1.0.0',
        'level': 1,
        'split': 'validation',
        'accuracy': r['accuracy'],
        'correct_tasks': r['score'],
        'total_tasks': r['max_score'],
        'average_time_per_task': r['avg_time'],
        'total_time_seconds': r['time_used']
    }
}
print(json.dumps(sub, indent=2))
")
"

git push
```

## Example 5: Scheduled Benchmarking

```yaml
# .github/workflows/scheduled-benchmark.yml
name: Scheduled GAIA Benchmark

on:
  schedule:
    # Run every Sunday at 00:00 UTC
    - cron: '0 0 * * 0'
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install -e .
    
    - name: Run full benchmark suite
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
      run: |
        for level in 1 2 3; do
          echo "Running level $level..."
          python main.py launch --level $level --task-ids "0,1,2,3,4,5,6,7,8,9" --split validation
        done
    
    - name: Create release with results
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: benchmark-${{ github.run_number }}
        release_name: Scheduled Benchmark Run ${{ github.run_number }}
        body: |
          # Weekly GAIA Benchmark Results
          
          Results from scheduled benchmark run.
```

## Example 6: Results Parser and Submission Script

```python
#!/usr/bin/env python3
"""
Parse GAIA evaluation results and create GitHub submission.
"""

import json
import subprocess
import sys
from datetime import datetime

def run_benchmark(level=1, num_tasks=10):
    """Run GAIA benchmark and return results."""
    task_ids = ",".join(str(i) for i in range(num_tasks))
    
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "launch",
            "--level", str(level),
            "--task-ids", task_ids,
            "--split", "validation",
        ],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"Benchmark failed: {result.stderr}")
        return None
    
    # Parse JSON output
    try:
        data = json.loads(result.stdout)
        return data
    except json.JSONDecodeError:
        print("Failed to parse benchmark results")
        return None

def create_submission_json(results, agent_name="gaia-agent", team_name="team"):
    """Create submission JSON from results."""
    return {
        "gaia_submission": {
            "agent_name": agent_name,
            "agent_version": datetime.now().strftime("%Y%m%d.%H%M"),
            "team_name": team_name,
            "level": results.get("level", 1),
            "split": results.get("split", "validation"),
            "accuracy": results.get("accuracy", 0),
            "correct_tasks": results.get("score", 0),
            "total_tasks": results.get("max_score", 10),
            "average_time_per_task": results.get("avg_time", 0),
            "total_time_seconds": results.get("time_used", 0),
            "model_used": "gpt-4o",
        }
    }

def commit_and_push(submission_json):
    """Commit results and push to GitHub."""
    message = f"""Benchmark results: {submission_json['gaia_submission']['accuracy']:.1f}%

{json.dumps(submission_json, indent=2)}
"""
    
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)

if __name__ == "__main__":
    print("Running GAIA benchmark...")
    results = run_benchmark(level=1, num_tasks=10)
    
    if results:
        submission = create_submission_json(results)
        print("Submission JSON:")
        print(json.dumps(submission, indent=2))
        
        # Optionally commit and push
        # commit_and_push(submission)
    else:
        sys.exit(1)
```

## Verification

After submitting via webhook, you can verify the submission:

```bash
# Check if webhook was received
curl http://leaderboard-api:8000/webhooks/status

# Get submission details
curl http://leaderboard-api:8000/submissions/{submission_id}

# Check team leaderboard
curl http://leaderboard-api:8000/leaderboard/teams?level=1
```

## Troubleshooting Webhooks

### Check GitHub Webhook Deliveries

In your repository settings → Webhooks, you can see:
- Delivery history
- Response codes
- Payload details
- Retry attempts

### Common Issues

1. **Signature verification failed**
   - Ensure `GITHUB_WEBHOOK_SECRET` matches GitHub settings

2. **No GAIA config found**
   - Check JSON format in commit message/PR description
   - Must be valid JSON wrapped in `{"gaia_submission": {...}}`

3. **Submission not appearing**
   - Check webhook delivery logs in GitHub
   - Verify leaderboard API is running
   - Check database with: `python scripts/setup_db.py stats`
