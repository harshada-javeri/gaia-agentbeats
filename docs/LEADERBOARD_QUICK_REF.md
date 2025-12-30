# Leaderboard Quick Reference

## 🚀 Quick Setup

```bash
# 1. Install dependencies
pip install -e .

# 2. Initialize database
python scripts/setup_db.py init

# 3. Start API server (Terminal 1)
python -m src.leaderboard_api

# 4. Run benchmark with leaderboard submission
python main.py launch --level 1 --task-ids "0,1,2,3,4,5" --split validation
```

## 📊 API Endpoints

### Get Leaderboard
```bash
curl http://localhost:8000/leaderboard?level=1&split=validation
```

### Get Team Rankings
```bash
curl http://localhost:8000/leaderboard/teams?level=1&split=validation
```

### Submit Results
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
    "total_time_seconds": 69.0
  }'
```

### Get Agent History
```bash
curl http://localhost:8000/agents/my-agent/history
```

### Get Team History
```bash
curl http://localhost:8000/teams/my-team/history
```

### Get Recent Submissions
```bash
curl http://localhost:8000/recent?days=7
```

### Get Stats
```bash
curl http://localhost:8000/stats
```

## 🔧 Database Setup

### SQLite (Default)
```bash
# Already configured in environment
# Auto-creates: agentbeats_leaderboard.db
python scripts/setup_db.py check
```

### PostgreSQL (Production)
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/gaia"
python scripts/setup_db.py init
python scripts/setup_db.py check
```

### View Database Stats
```bash
python scripts/setup_db.py stats
```

## 🔗 GitHub Webhook

### 1. Get Webhook Secret
```bash
# Generate random secret
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Set Environment Variable
```bash
export GITHUB_WEBHOOK_SECRET="your-generated-secret"
```

### 3. Configure in GitHub
- Repo Settings → Webhooks → Add webhook
- URL: `https://your-server.com/webhooks/github`
- Secret: (paste above)
- Events: Pushes, Pull requests

### 4. Submit via Commit
```bash
git commit -m "Results

{
  \"gaia_submission\": {
    \"agent_name\": \"my-agent\",
    \"agent_version\": \"1.0.0\",
    \"team_name\": \"my-team\",
    \"level\": 1,
    \"split\": \"validation\",
    \"accuracy\": 80.0,
    \"correct_tasks\": 24,
    \"total_tasks\": 30,
    \"average_time_per_task\": 2.5,
    \"total_time_seconds\": 75.0
  }
}
"

git push
```

## 📝 Configuration

### scenario.toml
```toml
[config]
level = 1
split = "validation"
task_indices = [0, 1, 2]

# Leaderboard
submit_to_leaderboard = true
agent_name = "my-agent"
agent_version = "1.0.0"
team_name = "my-team"
model_used = "gpt-4o"
```

### .env
```bash
# Database
DATABASE_URL=sqlite:///./agentbeats_leaderboard.db

# Webhook
GITHUB_WEBHOOK_SECRET=your-secret-here

# API
LEADERBOARD_API_HOST=0.0.0.0
LEADERBOARD_API_PORT=8000
```

## 🗄️ Database Queries

### Top 10 Agents for Level 1
```sql
SELECT 
    ROW_NUMBER() OVER (ORDER BY accuracy DESC) as rank,
    agent_name,
    team_name,
    accuracy,
    correct_tasks || '/' || total_tasks as score,
    timestamp
FROM submissions
WHERE level = 1 AND split = 'validation'
ORDER BY accuracy DESC
LIMIT 10;
```

### Best Agent Per Team
```sql
SELECT DISTINCT ON (team_name)
    team_name,
    agent_name,
    accuracy,
    timestamp
FROM submissions
WHERE level = 1
ORDER BY team_name, accuracy DESC;
```

### Recent Submissions Last 7 Days
```sql
SELECT 
    agent_name,
    team_name,
    accuracy,
    timestamp
FROM submissions
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### Agent Improvement Trend
```sql
SELECT 
    agent_version,
    COUNT(*) as submissions,
    AVG(accuracy) as avg_accuracy,
    MAX(accuracy) as best_accuracy
FROM submissions
WHERE agent_name = 'my-agent'
GROUP BY agent_version
ORDER BY agent_version DESC;
```

## 🐛 Troubleshooting

### Database Not Found
```bash
python scripts/setup_db.py check
# If fails, reinitialize:
python scripts/setup_db.py init
```

### Connection Error
```bash
# Check database URL
python -c "import os; print(os.getenv('DATABASE_URL'))"

# Test connection
python scripts/setup_db.py check
```

### Webhook Not Working
1. Check GitHub webhook deliveries
2. Verify `GITHUB_WEBHOOK_SECRET` matches
3. Ensure JSON is valid in commit message
4. Check leaderboard API is running

### Submission Not Appearing
1. Verify `submit_to_leaderboard = true` in config
2. Check database has entries: `python scripts/setup_db.py stats`
3. Refresh leaderboard:
   ```bash
   curl -X POST http://localhost:8000/admin/refresh-leaderboard
   ```

## 📚 Documentation

- **Full Setup Guide**: [docs/LEADERBOARD_SETUP.md](../docs/LEADERBOARD_SETUP.md)
- **Webhook Examples**: [docs/WEBHOOK_EXAMPLES.md](../docs/WEBHOOK_EXAMPLES.md)
- **API Reference**: Run server and visit `http://localhost:8000/docs`

## 🎯 Common Tasks

### Check Leaderboard
```bash
curl http://localhost:8000/leaderboard?level=1 | python -m json.tool
```

### See My Team's Position
```bash
curl http://localhost:8000/leaderboard/teams?level=1 | grep -A 5 '"team_name": "my-team"'
```

### Track Agent Improvements
```bash
curl http://localhost:8000/agents/my-agent/history | python -m json.tool
```

### Get Raw Database Access
```bash
# SQLite
sqlite3 agentbeats_leaderboard.db

# PostgreSQL
psql postgresql://user:password@localhost/gaia
```

## 🚨 Important Notes

- **Result Accuracy**: Verify results are correct before committing
- **Team Name Consistency**: Use same team name across submissions
- **Agent Versioning**: Increment version for new agent changes
- **Database Backups**: Regular backups recommended for production
- **API Security**: Add authentication for public deployments

## 📞 Support

Check logs for debugging:
```bash
# Python logs
python scripts/setup_db.py check
python -m src.leaderboard_api --verbose

# Database logs
tail -f agentbeats_leaderboard.db  # SQLite
tail -f /var/log/postgresql/...   # PostgreSQL
```
