# GAIA Leaderboard Setup Guide

This guide explains how to set up and use the GAIA Benchmark leaderboard system with GitHub webhook integration.

## Overview

The leaderboard system consists of:

1. **Database**: Stores submissions, rankings, and webhook events
2. **GitHub Webhook Handler**: Automatically processes submissions from GitHub
3. **API Endpoints**: FastAPI REST API for leaderboard queries and submissions
4. **Green Agent Integration**: Automatic submission from evaluation results

## Database Setup

### 1. Initialize Database

```bash
# Initialize SQLite database (default, local development)
python scripts/setup_db.py init

# Or check existing database
python scripts/setup_db.py check

# View statistics
python scripts/setup_db.py stats
```

### 2. Database Configuration

The system uses SQLite by default for local development, or PostgreSQL for production.

**Environment variables:**

```bash
# Use SQLite (default)
export DATABASE_URL="sqlite:///./agentbeats_leaderboard.db"

# Or use PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/gaia_leaderboard"
```

### 3. Database Schema

Three main tables:

#### `submissions`
Stores all benchmark submissions with full details.

```sql
-- Key fields
submission_id (unique)
agent_name
agent_version
team_name
level (1, 2, or 3)
split (validation or test)
accuracy (0-100)
correct_tasks
total_tasks
average_time_per_task
github_repo
github_commit_hash
github_branch
timestamp
is_verified
```

Example query to get top agents:

```sql
SELECT 
    agent_name,
    agent_version,
    team_name,
    accuracy,
    correct_tasks,
    total_tasks,
    timestamp
FROM submissions
WHERE level = 1 AND split = 'validation'
ORDER BY accuracy DESC, average_time_per_task ASC
LIMIT 10;
```

#### `leaderboard`
Materialized view for current rankings (refreshed periodically).

```sql
SELECT 
    rank,
    agent_name,
    team_name,
    accuracy,
    correct_tasks,
    total_tasks,
    submission_timestamp
FROM leaderboard
WHERE level = 1 AND split = 'validation'
ORDER BY rank ASC;
```

#### `webhook_events`
Audit log of all GitHub webhook events for debugging and retry logic.

```sql
SELECT 
    event_type,
    repository,
    commit_hash,
    is_processed,
    error_message,
    timestamp
FROM webhook_events
WHERE is_processed = false;
```

## Running the Leaderboard API

### Start the API Server

```bash
# Local development
python -m src.leaderboard_api

# Or with custom settings
export LEADERBOARD_API_HOST=0.0.0.0
export LEADERBOARD_API_PORT=8000
python -m src.leaderboard_api
```

API runs on `http://localhost:8000`

## API Endpoints

### Get Leaderboard

```bash
# Top agents for level 1, validation split
curl http://localhost:8000/leaderboard?level=1&split=validation

# Response:
{
  "level": 1,
  "split": "validation",
  "count": 5,
  "entries": [
    {
      "rank": 1,
      "agent_name": "my-agent",
      "team_name": "my-team",
      "accuracy": 80.0,
      "correct_tasks": 24,
      "total_tasks": 30,
      "average_time_per_task": 2.5,
      "submission_timestamp": "2024-01-15T10:30:00"
    }
  ]
}
```

### Get Team Leaderboard

```bash
curl http://localhost:8000/leaderboard/teams?level=1&split=validation
```

### Get Submission Details

```bash
curl http://localhost:8000/submissions/{submission_id}
```

### Get Agent History

```bash
curl http://localhost:8000/agents/{agent_name}/history?limit=10
```

### Get Team History

```bash
curl http://localhost:8000/teams/{team_name}/history?limit=20
```

### Get Recent Submissions

```bash
curl http://localhost:8000/recent?days=7&limit=50
```

### Get Statistics

```bash
curl http://localhost:8000/stats

# Response:
{
  "total_submissions": 45,
  "unique_teams": 8,
  "unique_agents": 23,
  "stats_by_level": {
    "level_1": {
      "submissions": 30,
      "average_accuracy": 62.5,
      "best_accuracy": 95.0
    }
  }
}
```

### Create Direct Submission

```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my-agent",
    "agent_version": "1.0.0",
    "team_name": "my-team",
    "level": 1,
    "split": "validation",
    "accuracy": 75.5,
    "correct_tasks": 22,
    "total_tasks": 30,
    "average_time_per_task": 2.3,
    "total_time_seconds": 69.0,
    "model_used": "gpt-4o"
  }'
```

### Refresh Leaderboard Rankings

```bash
curl -X POST http://localhost:8000/admin/refresh-leaderboard
```

## GitHub Webhook Integration

### Setup GitHub Webhook

1. **Get webhook secret** (if not already set):
   ```bash
   export GITHUB_WEBHOOK_SECRET="your-secret-key"
   ```

2. **Configure in GitHub repo settings**:
   - Settings → Webhooks → Add webhook
   - Payload URL: `https://your-server.com/webhooks/github`
   - Content type: `application/json`
   - Secret: (paste your `GITHUB_WEBHOOK_SECRET`)
   - Events: Select "Pushes" and "Pull requests"

### Submit via Commit Message

Include GAIA configuration in your commit message:

```bash
git commit -m "Add improved agent

{
  \"gaia_submission\": {
    \"agent_name\": \"improved-agent\",
    \"agent_version\": \"2.0.0\",
    \"team_name\": \"my-team\",
    \"level\": 1,
    \"split\": \"validation\",
    \"accuracy\": 85.0,
    \"correct_tasks\": 25,
    \"total_tasks\": 30,
    \"average_time_per_task\": 2.1,
    \"total_time_seconds\": 63.0,
    \"model_used\": \"gpt-4o\",
    \"environment\": \"docker\"
  }
}
"
```

### Submit via Pull Request

Include GAIA configuration in PR description:

```markdown
## Changes

- Improved reasoning logic
- Better tool usage

```json
{
  "gaia_submission": {
    "agent_name": "improved-agent",
    "agent_version": "2.0.0",
    "team_name": "my-team",
    "level": 1,
    "split": "validation",
    "accuracy": 85.0,
    "correct_tasks": 25,
    "total_tasks": 30,
    "average_time_per_task": 2.1,
    "total_time_seconds": 63.0
  }
}
```
```

## Agent Integration

### Enable Leaderboard Submission in scenario.toml

```toml
[config]
level = 1
split = "validation"
task_indices = [0, 1, 2]

# Leaderboard settings
submit_to_leaderboard = true
agent_name = "my-agent"
agent_version = "1.0.0"
team_name = "my-team"
model_used = "gpt-4o"
```

### Automatic Submission from Green Agent

When evaluation completes, results are automatically submitted if:

```python
# In scenario.toml or EvalRequest config
submit_to_leaderboard = true  # Default: true
```

Results include:
- Agent name and version
- Team name
- GAIA level and split
- Accuracy percentage
- Correct/total tasks
- Performance metrics
- Task-by-task results

## SQL Query Examples

### Get Best Agent Per Team

```sql
SELECT DISTINCT ON (team_name)
    team_name,
    agent_name,
    agent_version,
    accuracy,
    timestamp
FROM submissions
WHERE level = 1 AND split = 'validation'
ORDER BY team_name, accuracy DESC;
```

### Get Accuracy Trend for an Agent

```sql
SELECT 
    agent_version,
    COUNT(*) as submissions,
    AVG(accuracy) as avg_accuracy,
    MAX(accuracy) as best_accuracy,
    DATE(timestamp) as date
FROM submissions
WHERE agent_name = 'my-agent' AND level = 1
GROUP BY agent_version, DATE(timestamp)
ORDER BY date DESC;
```

### Get Team Leaderboard with Badges

```sql
SELECT 
    ROW_NUMBER() OVER (ORDER BY accuracy DESC) as rank,
    team_name,
    agent_name,
    accuracy,
    correct_tasks || '/' || total_tasks as score,
    CASE 
        WHEN accuracy >= 90 THEN '🥇 Gold'
        WHEN accuracy >= 75 THEN '🥈 Silver'
        WHEN accuracy >= 50 THEN '🥉 Bronze'
        ELSE '📋 Participant'
    END as badge
FROM (
    SELECT DISTINCT ON (team_name)
        team_name, agent_name, accuracy, correct_tasks, total_tasks
    FROM submissions
    WHERE level = 1
    ORDER BY team_name, accuracy DESC
) as best_per_team
ORDER BY accuracy DESC;
```

### Find Recent Submissions without Verification

```sql
SELECT 
    submission_id,
    agent_name,
    team_name,
    accuracy,
    github_repo,
    github_commit_hash,
    timestamp
FROM submissions
WHERE is_verified = false 
    AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

## Monitoring & Maintenance

### View Webhook Errors

```bash
curl http://localhost:8000/admin/webhook-errors
```

### Refresh Leaderboard (if using cached entries)

```bash
curl -X POST http://localhost:8000/admin/refresh-leaderboard
```

### Verify Submission

```bash
# Mark submission as verified
curl -X PATCH http://localhost:8000/submissions/{submission_id}/verify \
  -H "Content-Type: application/json" \
  -d '{"verified": true, "notes": "Manual verification passed"}'
```

## Docker Setup

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=your-key
HF_TOKEN=your-token
DATABASE_URL=postgresql://user:pass@postgres:5432/gaia
GITHUB_WEBHOOK_SECRET=your-webhook-secret
LEADERBOARD_API_HOST=0.0.0.0
LEADERBOARD_API_PORT=8000
```

### docker-compose with Postgres

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gaia
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data

  gaia:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/gaia
      GITHUB_WEBHOOK_SECRET: ${GITHUB_WEBHOOK_SECRET}
    depends_on:
      - postgres
    ports:
      - "9001:9001"
      - "9002:9002"
      - "8000:8000"

  leaderboard:
    build:
      context: .
      dockerfile: Dockerfile.leaderboard
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/gaia
    depends_on:
      - postgres
    ports:
      - "8001:8000"

volumes:
  postgres-data:
```

## Troubleshooting

### Database Connection Error

```python
# Check database URL
import os
print(os.getenv("DATABASE_URL"))

# Test connection
python scripts/setup_db.py check
```

### Webhook Signature Verification Failed

Ensure `GITHUB_WEBHOOK_SECRET` matches the secret in GitHub webhook settings.

### Leaderboard Not Updated After Submission

1. Check if `submit_to_leaderboard = true` in config
2. Verify database is initialized: `python scripts/setup_db.py check`
3. Refresh leaderboard: `curl -X POST http://localhost:8000/admin/refresh-leaderboard`

### PostgreSQL Connection Issues

```bash
# Install psycopg2
pip install psycopg2-binary

# Test connection
psql postgresql://user:password@host:5432/database
```

## Performance Optimization

### Add Database Indexes

For high-volume submissions, ensure indexes are created:

```sql
CREATE INDEX idx_submissions_team_level_split 
  ON submissions(team_name, level, split);

CREATE INDEX idx_submissions_accuracy 
  ON submissions(accuracy DESC);

CREATE INDEX idx_leaderboard_level_rank 
  ON leaderboard(level, rank);
```

### Cache Leaderboard Entries

Configure periodic refresh of materialized leaderboard:

```python
# Every 5 minutes
import schedule
schedule.every(5).minutes.do(
    LeaderboardQueries.refresh_leaderboard, db
)
```

## References

- [GAIA Benchmark](https://huggingface.co/datasets/gaia-benchmark/GAIA)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
