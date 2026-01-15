#!/usr/bin/env python3
"""
Quick test submission script for AgentBeats leaderboard.

This script generates a sample GAIA result JSON and prepares it for pushing
to your leaderboard repository.
"""

import json
from datetime import datetime
import uuid

def create_sample_gaia_result():
    """Create a sample GAIA benchmark result JSON."""
    
    # Generate unique IDs for this submission
    agent_id = str(uuid.uuid4())
    submission_id = str(uuid.uuid4())
    
    result = {
        "submission_id": submission_id,
        "timestamp": datetime.now().isoformat(),
        "participants": {
            "agent": agent_id
        },
        "config": {
            "level": 1,
            "split": "validation",
            "domain": "benchmark"
        },
        "results": [
            {
                "task_id": 0,
                "status": "completed",
                "score": 1.0,
                "time_used": 2.5,
                "max_score": 1
            },
            {
                "task_id": 1,
                "status": "completed",
                "score": 1.0,
                "time_used": 3.1,
                "max_score": 1
            },
            {
                "task_id": 2,
                "status": "completed",
                "score": 0.5,
                "time_used": 4.2,
                "max_score": 1
            }
        ],
        "summary": {
            "total_tasks": 3,
            "completed_tasks": 3,
            "passed_tasks": 2,
            "accuracy": 0.667,
            "total_time": 9.8,
            "average_time_per_task": 3.27
        }
    }
    
    return result

if __name__ == "__main__":
    # Generate the result
    result = create_sample_gaia_result()
    
    # Print as JSON
    print("Sample GAIA Result JSON:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print("=" * 60)
    
    print("\n📋 Steps to push this result to your leaderboard:")
    print("""
1. Create/locate your leaderboard repository (gaia-benchmark-leaderboard)
   https://github.com/yourusername/gaia-benchmark-leaderboard

2. Create the results directory if it doesn't exist:
   mkdir -p results

3. Save this JSON to: results/<timestamp>.json
   Example: results/2026-01-16-test-result.json

4. Commit and push:
   git add results/
   git commit -m "Test GAIA benchmark result submission"
   git push origin main

5. Verify:
   - Check GitHub webhook delivery logs
   - Visit AgentBeats leaderboard page after 30 seconds
   - Your result should appear on the leaderboard
    """)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"results/gaia-result-{timestamp}.json"
    
    import os
    os.makedirs("results", exist_ok=True)
    
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Sample result saved to: {filename}")
    print(f"📁 Ready to commit and push to your leaderboard repo!")
