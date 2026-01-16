#!/usr/bin/env python3
import json
import csv
from pathlib import Path

# Collect all results
rows = []
results_dir = Path('results')
for json_file in results_dir.glob('gaia-result-*.json'):
    with open(json_file) as f:
        data = json.load(f)
    
    agent_id = data["participants"]["agent"]
    
    for result in data["results"]:
        rows.append({
            'agent_id': agent_id,
            'task_id': str(result["task_id"]),
            'overall_score': result["score"],
            'passed': result["score"] >= result["max_score"]
        })

# Write CSV
with open('evaluation_results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['agent_id', 'task_id', 'overall_score', 'passed'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Created evaluation_results.csv with {len(rows)} rows")
