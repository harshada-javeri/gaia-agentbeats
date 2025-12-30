# Leaderboard Setup - Implementation Summary

## Overview

A complete leaderboard system has been implemented for the GAIA Benchmark on AgentBeats, enabling:

1. **Automatic submission** of evaluation results to a database
2. **GitHub webhook integration** for automated submissions via commits/PRs
3. **REST API** for querying leaderboard rankings and submission history
4. **Database persistence** with support for both SQLite and PostgreSQL
5. **SQL-based ranking** system with proper indexing for performance

## Files Created

### Core Database Layer

**`src/agentbeats/database.py`** - SQLAlchemy models and database configuration
- `Submission` model: Stores all benchmark submissions
- `LeaderboardEntry` model: Materialized view for current rankings
- `WebhookEvent` model: Audit log for GitHub webhook events
- Database initialization and session management

Key fields in Submission:
```python
submission_id, agent_name, agent_version, team_name
level (1-3), split (validation/test)
accuracy, correct_tasks, total_tasks
average_time_per_task, total_time_seconds
github_repo, github_commit_hash, github_branch
task_results (JSON), is_verified, timestamp
```

### Query Layer

**`src/utils/leaderboard_queries.py`** - SQL query utilities
- `get_leaderboard()`: Top agents for level/split with proper ordering
- `get_team_leaderboard()`: Best agent per team
- `get_agent_history()`: Submission history for an agent
- `get_team_history()`: All submissions from a team
- `get_submission_by_id()`: Detailed submission info
- `get_recent_submissions()`: Submissions from last N days
- `get_stats()`: Overall statistics
- `refresh_leaderboard()`: Materialize rankings from recent submissions

All queries use SQLAlchemy ORM with proper indexing for performance.

### Webhook Integration

**`src/agentbeats/github_webhook.py`** - GitHub webhook handler
- `verify_signature()`: HMAC-SHA256 signature verification
- `extract_gaia_config()`: Parse JSON from commits/PRs
- `process_push_event()`: Handle GitHub push events
- `process_pull_request_event()`: Handle PR events
- `store_webhook_event()`: Audit trail logging

Supports extracting submission data from:
- Commit message: `{"gaia_submission": {...}}`
- PR description: Same JSON format

### REST API

**`src/leaderboard_api.py`** - FastAPI application with full CRUD operations

Endpoints:
- `GET /leaderboard` - Get top agents
- `GET /leaderboard/teams` - Team rankings
- `GET /submissions/{id}` - Submission details
- `GET /agents/{name}/history` - Agent history
- `GET /teams/{name}/history` - Team history
- `GET /recent` - Recent submissions
- `GET /stats` - Statistics
- `POST /submissions` - Direct submission
- `POST /webhooks/github` - GitHub webhook receiver
- `POST /admin/refresh-leaderboard` - Refresh rankings

All endpoints return JSON with proper HTTP status codes.

### Green Agent Integration

**`src/green_agent/agent.py`** - Modified to submit results
- `_submit_to_leaderboard()`: New async method
- Extracts metrics from evaluation results
- Creates Submission records in database
- Automatically refreshes leaderboard rankings
- Supports all submission metadata (GitHub info, team, etc.)

### Database Setup

**`scripts/setup_db.py`** - Database initialization utility
- `init_database()` - Create all tables
- `check_database()` - Verify connectivity and schema
- `show_stats()` - Display statistics

Commands:
```bash
python scripts/setup_db.py init      # Initialize DB
python scripts/setup_db.py check     # Check DB health
python scripts/setup_db.py stats     # Show stats
python scripts/setup_db.py init --force  # Reset DB
```

### Configuration Files

**`scenario.toml`** - Updated with leaderboard configuration
```toml
submit_to_leaderboard = true
agent_name = "gaia-benchmark-agent"
agent_version = "1.0.0"
team_name = "agentbeats"
model_used = "gpt-4o"
```

**`pyproject.toml`** - Added dependencies
```
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.9
fastapi>=0.104.0
pydantic>=2.0.0
```

**`.env.example`** - Added environment variables
```
DATABASE_URL=sqlite:///./agentbeats_leaderboard.db
GITHUB_WEBHOOK_SECRET=your-webhook-secret-here
LEADERBOARD_API_HOST=0.0.0.0
LEADERBOARD_API_PORT=8000
```

### Documentation

**`docs/LEADERBOARD_SETUP.md`** - Comprehensive setup and usage guide (800+ lines)
- Database initialization and configuration
- API endpoint documentation with examples
- GitHub webhook setup instructions
- SQL query examples
- Docker integration
- Troubleshooting guide
- Performance optimization tips

**`docs/WEBHOOK_EXAMPLES.md`** - Practical examples (600+ lines)
- Commit message submission example
- PR submission example
- GitHub Actions CI/CD workflow
- Docker build and benchmark
- Scheduled benchmarking
- Results parser script

**`docs/LEADERBOARD_QUICK_REF.md`** - Quick reference guide
- Quick setup (4 steps)
- API endpoint reference table
- Database setup for SQLite/PostgreSQL
- GitHub webhook configuration
- Common SQL queries
- Troubleshooting checklist
- Important notes and best practices

## Database Schema

### Submission Table
```sql
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    submission_id VARCHAR(255) UNIQUE,
    agent_name VARCHAR(255),
    agent_version VARCHAR(50),
    team_name VARCHAR(255),
    level INTEGER,
    split VARCHAR(50),
    accuracy FLOAT,
    correct_tasks INTEGER,
    total_tasks INTEGER,
    average_time_per_task FLOAT,
    total_time_seconds FLOAT,
    task_results JSON,
    github_repo VARCHAR(255),
    github_commit_hash VARCHAR(40),
    github_branch VARCHAR(255),
    timestamp DATETIME,
    is_verified BOOLEAN,
    -- Indexes on frequently queried columns
    INDEX idx_team_level_split (team_name, level, split),
    INDEX idx_agent_timestamp (agent_name, timestamp),
    INDEX idx_github_repo (github_repo)
);
```

### Leaderboard Table
```sql
CREATE TABLE leaderboard (
    id INTEGER PRIMARY KEY,
    rank INTEGER,
    level INTEGER,
    split VARCHAR(50),
    agent_name VARCHAR(255),
    team_name VARCHAR(255),
    accuracy FLOAT,
    correct_tasks INTEGER,
    total_tasks INTEGER,
    best_submission_id VARCHAR(255),
    submission_timestamp DATETIME,
    last_updated DATETIME,
    -- Indexes for ranking queries
    INDEX idx_leaderboard_level_rank (level, rank),
    INDEX idx_leaderboard_team (level, team_name)
);
```

### Webhook Events Table
```sql
CREATE TABLE webhook_events (
    id INTEGER PRIMARY KEY,
    event_type VARCHAR(50),
    event_id VARCHAR(255) UNIQUE,
    payload JSON,
    is_processed BOOLEAN,
    error_message TEXT,
    repository VARCHAR(255),
    commit_hash VARCHAR(40),
    timestamp DATETIME,
    -- Indexes for webhook processing
    INDEX idx_webhook_repo_event (repository, event_type),
    INDEX idx_webhook_unprocessed (is_processed, timestamp)
);
```

## Key SQL Queries

### Get Top 10 Agents for Level 1
```sql
SELECT 
    ROW_NUMBER() OVER (ORDER BY accuracy DESC) as rank,
    agent_name, team_name, accuracy,
    correct_tasks || '/' || total_tasks as score
FROM submissions
WHERE level = 1 AND split = 'validation'
ORDER BY accuracy DESC
LIMIT 10;
```

### Get Best Agent Per Team
```sql
SELECT DISTINCT ON (team_name)
    team_name, agent_name, agent_version, accuracy, timestamp
FROM submissions
WHERE level = 1
ORDER BY team_name, accuracy DESC;
```

### Get Agent Improvement Trend
```sql
SELECT 
    agent_version,
    COUNT(*) as submissions,
    AVG(accuracy) as avg_accuracy,
    MAX(accuracy) as best_accuracy,
    DATE(timestamp) as date
FROM submissions
WHERE agent_name = 'my-agent'
GROUP BY agent_version, DATE(timestamp)
ORDER BY date DESC;
```

## How It Works

### Submission Flow

1. **Evaluation Completes** → Green agent finishes running GAIA tasks
2. **Results Computed** → Accuracy, timing, and per-task metrics calculated
3. **Check Config** → If `submit_to_leaderboard = true`
4. **Create Submission** → Generate submission record with:
   - Agent name/version
   - Team name
   - Level, split, accuracy
   - Performance metrics
   - Task results JSON
   - Timestamp
5. **Save to Database** → INSERT into submissions table
6. **Refresh Rankings** → Recalculate leaderboard entries
7. **Return Results** → Results shown in evaluation summary

### GitHub Webhook Flow

1. **Code Push** → Developer pushes with GAIA config in commit message
2. **GitHub Sends Webhook** → POST to `/webhooks/github` endpoint
3. **Verify Signature** → HMAC-SHA256 validation against secret
4. **Extract Config** → Parse JSON from message/PR description
5. **Create Submission** → Instantiate Submission object
6. **Store Event** → Log webhook for audit trail
7. **Save Submission** → Persist to database
8. **Refresh Rankings** → Update leaderboard entries
9. **Return Status** → Return success/failure response

## API Response Examples

### Leaderboard Response
```json
{
  "level": 1,
  "split": "validation",
  "count": 5,
  "entries": [
    {
      "rank": 1,
      "agent_name": "improved-agent",
      "team_name": "ml-team",
      "accuracy": 88.5,
      "correct_tasks": 26,
      "total_tasks": 30,
      "average_time_per_task": 2.05,
      "submission_timestamp": "2024-01-15T10:30:00"
    }
  ]
}
```

### Submission Details Response
```json
{
  "submission_id": "eval-a1b2c3d4e5f6",
  "agent_name": "my-agent",
  "team_name": "my-team",
  "accuracy": 75.5,
  "correct_tasks": 22,
  "total_tasks": 30,
  "average_time_per_task": 2.3,
  "github_commit_hash": "abc123def456",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Testing

### Test Database Setup
```bash
python scripts/setup_db.py init
python scripts/setup_db.py check
python scripts/setup_db.py stats
```

### Test API
```bash
# Start API
python -m src.leaderboard_api

# In another terminal
curl http://localhost:8000/stats
curl http://localhost:8000/leaderboard?level=1
```

### Test Submission
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test-agent",
    "agent_version": "1.0.0",
    "level": 1,
    "split": "validation",
    "accuracy": 75.0,
    "correct_tasks": 22,
    "total_tasks": 30,
    "average_time_per_task": 2.3,
    "total_time_seconds": 69.0
  }'
```

## Production Deployment

### Using PostgreSQL
```bash
export DATABASE_URL="postgresql://user:password@host:5432/gaia"
python scripts/setup_db.py init
python -m src.leaderboard_api
```

### Docker Compose
See `LEADERBOARD_SETUP.md` for complete docker-compose.yml with PostgreSQL service.

### Environment Variables
```bash
DATABASE_URL=postgresql://...
GITHUB_WEBHOOK_SECRET=...
LEADERBOARD_API_HOST=0.0.0.0
LEADERBOARD_API_PORT=8000
```

## Summary

This implementation provides a production-ready leaderboard system that:

✅ Automatically captures benchmark results  
✅ Integrates with GitHub for easy submission  
✅ Provides REST API for queries and rankings  
✅ Supports both SQLite (local) and PostgreSQL (production)  
✅ Includes comprehensive documentation and examples  
✅ Has proper indexing and query optimization  
✅ Logs all webhook events for audit trail  
✅ Allows verification and manual review of submissions  

The system is fully integrated with the green agent and can be deployed immediately.
