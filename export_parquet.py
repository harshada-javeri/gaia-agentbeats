#!/usr/bin/env python3
import duckdb

conn = duckdb.connect()
conn.execute("""
    COPY (
        SELECT agent_id, task_id, overall_score, passed
        FROM read_csv_auto('evaluation_results.csv')
    ) TO 'evaluation_results.parquet' (FORMAT PARQUET)
""")
print("Created evaluation_results.parquet")
