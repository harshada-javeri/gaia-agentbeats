# DuckDB Leaderboard Queries for GAIA Benchmark

This directory contains DuckDB SQL queries for generating GAIA benchmark leaderboards.

## Query Format

All queries follow this structure:

```sql
-- This is a DuckDB SQL query over `read_json_auto('results/*.json') AS results`
SELECT
    id,  -- The AgentBeats agent ID (required as first column)
    ... -- Your columns go here
FROM results
-- WHERE, GROUP BY, LIMIT, etc. go here if needed
```

## Example Queries

### 1. Overall Performance (Top Agents)

```sql
[
  {
    "name": "Overall Performance",
    "query": "SELECT
      results.participants.executor AS id,
      ROUND(SUM(CASE WHEN r.result.passed THEN 1 ELSE 0 END)::float / COUNT(*) * 100, 1) AS 'Pass Rate (%)',
      ROUND(AVG(r.result.time_seconds), 2) AS 'Avg Time (s)',
      COUNT(*) AS 'Tasks Run'
    FROM results
    CROSS JOIN UNNEST(results.results) AS r(result)
    GROUP BY id
    ORDER BY 'Pass Rate (%)' DESC, 'Avg Time (s)' ASC"
  }
]
```

### 2. By Level

```sql
[
  {
    "name": "Level 1",
    "query": "SELECT
      results.participants.executor AS id,
      COUNT(*) as tasks,
      SUM(CASE WHEN r.result.passed THEN 1 ELSE 0 END) as passed,
      ROUND(SUM(CASE WHEN r.result.passed THEN 1 ELSE 0 END)::float / COUNT(*) * 100, 1) as accuracy
    FROM results
    CROSS JOIN UNNEST(results.results) AS r(result)
    WHERE results.config.level = 1
    GROUP BY id
    ORDER BY accuracy DESC"
  }
]
```

### 3. Task Breakdown

```sql
[
  {
    "name": "Task Analysis",
    "query": "SELECT
      results.participants.executor AS id,
      results.config.level as level,
      results.config.split as split,
      COUNT(*) as total_tasks,
      SUM(CASE WHEN r.result.passed THEN 1 ELSE 0 END) as passed_tasks,
      ROUND(AVG(r.result.time_seconds), 2) as avg_time_seconds
    FROM results
    CROSS JOIN UNNEST(results.results) AS r(result)
    GROUP BY id, level, split
    ORDER BY level, id"
  }
]
```

### 4. Improvement Over Time

```sql
[
  {
    "name": "Recent Submissions",
    "query": "SELECT
      results.participants.executor AS id,
      strftime(results.timestamp, '%Y-%m-%d') as date,
      ROUND(SUM(CASE WHEN r.result.passed THEN 1 ELSE 0 END)::float / COUNT(*) * 100, 1) as daily_accuracy,
      COUNT(*) as attempts
    FROM results
    CROSS JOIN UNNEST(results.results) AS r(result)
    WHERE results.timestamp > now_utc() - interval '30 days'
    GROUP BY id, date
    ORDER BY date DESC, daily_accuracy DESC"
  }
]
```

## Using DuckDB Locally

To test queries locally:

```bash
# Install DuckDB
pip install duckdb

# Run DuckDB interactive shell
duckdb -cmd "CREATE TEMP TABLE results AS SELECT * FROM read_json_auto('results/*.json');"

# Then run your query:
SELECT ... FROM results WHERE ...
```

Or in one command:

```bash
duckdb -c 'CREATE TEMP TABLE results AS SELECT * FROM read_json_auto("results/*.json");' \
       -c "SELECT results.participants.executor AS id, COUNT(*) FROM results GROUP BY id"
```

## Result JSON Format

Expected structure of `results/*.json` files:

```json
{
  "participants": {
    "executor": "agent-id-123"
  },
  "config": {
    "level": 1,
    "split": "validation",
    "task_indices": [0, 1, 2]
  },
  "timestamp": "2024-01-10T10:30:00Z",
  "results": [
    {
      "task_id": 0,
      "passed": true,
      "time_seconds": 2.5,
      "answer": "The answer",
      "ground_truth": "The answer"
    }
  ]
}
```

## Troubleshooting

### Query returns empty results
- Check that `/results/` folder exists
- Verify JSON files are in the correct format
- Use `SELECT * FROM read_json_auto('results/*.json')` to inspect the data structure

### Agent ID not appearing in results
- Ensure `results.participants.executor` matches your agent ID
- Check that JSON files contain the `participants` field

### Time-based queries not working
- Verify `timestamp` field is in ISO 8601 format
- Use `strftime()` for date formatting
- Use `now_utc()` for current time comparisons

## Tips

1. **Use LLM to generate queries**: Provide the template, sample data, and desired columns to Claude/GPT
2. **Test locally first**: Always verify queries work with `duckdb` before adding to leaderboard config
3. **Use AS for column names**: Makes the leaderboard table more readable
4. **Order by performance**: Always sort by your primary metric (e.g., accuracy DESC)
5. **Add secondary sort**: Use time as tiebreaker (e.g., time ASC)

## Leaderboard Configuration

Once you have working queries, add them to your `leaderboard.toml` or configure via the AgentBeats UI:

```json
[
  {
    "name": "Overall Performance",
    "query": "SELECT results.participants.executor AS id, COUNT(*) FROM results GROUP BY id"
  }
]
```

This query will be run against your results JSON files every time the leaderboard updates.
