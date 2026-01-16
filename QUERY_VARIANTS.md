# Leaderboard Query Variants

## SQLite Version
```sql
SELECT agent_id, ROUND(AVG(overall_score), 3) AS overall_score, COUNT(*) AS total_tasks, COUNT(*) FILTER (WHERE passed) AS tasks_passed, ROUND(CAST(COUNT(*) FILTER (WHERE passed) AS FLOAT) / COUNT(*), 3) AS pass_rate FROM evaluation_results GROUP BY agent_id ORDER BY overall_score DESC
```

## DuckDB Version (if AgentBeats uses DuckDB)
```sql
SELECT agent_id, ROUND(AVG(overall_score), 3) AS overall_score, COUNT(*) AS total_tasks, COUNT(*) FILTER (WHERE passed) AS tasks_passed, ROUND(COUNT(*) FILTER (WHERE passed)::DOUBLE / COUNT(*), 3) AS pass_rate FROM evaluation_results GROUP BY agent_id ORDER BY overall_score DESC
```

## PostgreSQL Version
```sql
SELECT agent_id, ROUND(AVG(overall_score), 3) AS overall_score, COUNT(*) AS total_tasks, COUNT(*) FILTER (WHERE passed) AS tasks_passed, ROUND(COUNT(*) FILTER (WHERE passed)::FLOAT / COUNT(*), 3) AS pass_rate FROM evaluation_results GROUP BY agent_id ORDER BY overall_score DESC
```

## Universal Version (works everywhere)
```sql
SELECT agent_id, ROUND(AVG(overall_score), 3) AS overall_score, COUNT(*) AS total_tasks, SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS tasks_passed, ROUND(SUM(CASE WHEN passed THEN 1.0 ELSE 0.0 END) / COUNT(*), 3) AS pass_rate FROM evaluation_results GROUP BY agent_id ORDER BY overall_score DESC
```
