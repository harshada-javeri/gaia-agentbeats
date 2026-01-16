# AgentBeats Leaderboard Setup

## Database: evaluation_results.db

This database tracks GAIA benchmark evaluation results for the g-agent.

### Schema

```sql
CREATE TABLE evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    overall_score REAL NOT NULL,
    passed BOOLEAN NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Leaderboard Query

```sql
SELECT 
    agent_id, 
    ROUND(AVG(overall_score), 3) AS overall_score, 
    COUNT(*) AS total_tasks, 
    COUNT(*) FILTER (WHERE passed) AS tasks_passed, 
    ROUND(CAST(COUNT(*) FILTER (WHERE passed) AS FLOAT) / COUNT(*), 3) AS pass_rate 
FROM evaluation_results 
GROUP BY agent_id 
ORDER BY overall_score DESC
```

### Importing Results

To import new evaluation results from JSON:

```bash
python import_results.py results/gaia-result-YYYYMMDD-HHMMSS.json
```

### Webhook Integration

Webhook URL: `https://agentbeats.dev/api/hook/v2/019bc329-1da3-79a0-bed1-e0ae23d15225`

Configure in GitHub repository settings:
- Settings → Webhooks → Add webhook
- Payload URL: (webhook URL above)
- Content type: `application/json`
- Events: Push events

After pushing updates to the database, AgentBeats will automatically refresh the leaderboard.
