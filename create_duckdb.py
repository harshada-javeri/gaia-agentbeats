#!/usr/bin/env python3
import duckdb
import json
from pathlib import Path

# Create DuckDB database
conn = duckdb.connect('leaderboard.duckdb')

# Create table
conn.execute("""
    CREATE TABLE evaluation_results (
        id INTEGER,
        agent_id VARCHAR,
        task_id VARCHAR,
        overall_score DOUBLE,
        passed BOOLEAN,
        timestamp TIMESTAMP
    )
""")

# Import all JSON results
results_dir = Path('results')
for json_file in results_dir.glob('gaia-result-*.json'):
    with open(json_file) as f:
        data = json.load(f)
    
    agent_id = data["participants"]["agent"]
    
    for result in data["results"]:
        conn.execute(
            "INSERT INTO evaluation_results (agent_id, task_id, overall_score, passed) VALUES (?, ?, ?, ?)",
            [agent_id, str(result["task_id"]), result["score"], result["score"] >= result["max_score"]]
        )

# Verify
print("Data imported:")
print(conn.execute("""
    SELECT agent_id, ROUND(AVG(overall_score), 3) AS overall_score, 
           COUNT(*) AS total_tasks, 
           SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS tasks_passed
    FROM evaluation_results 
    GROUP BY agent_id 
    ORDER BY overall_score DESC
""").fetchall())

conn.close()
print("\nCreated leaderboard.duckdb")
