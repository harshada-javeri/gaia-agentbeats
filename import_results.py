#!/usr/bin/env python3
import json
import sqlite3
import sys
from pathlib import Path

def import_json_to_db(json_path: str, db_path: str = "evaluation_results.db"):
    with open(json_path) as f:
        data = json.load(f)
    
    agent_id = data["participants"]["agent"]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for result in data["results"]:
        cursor.execute(
            "INSERT INTO evaluation_results (agent_id, task_id, overall_score, passed) VALUES (?, ?, ?, ?)",
            (agent_id, str(result["task_id"]), result["score"], result["score"] >= result["max_score"])
        )
    
    conn.commit()
    conn.close()
    print(f"Imported {len(data['results'])} results for agent {agent_id}")

if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else "results/gaia-result-20260116-011540.json"
    import_json_to_db(json_file)
