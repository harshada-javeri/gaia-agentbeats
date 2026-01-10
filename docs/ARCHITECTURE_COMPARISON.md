# Architecture Comparison: Custom vs Official AgentBeats

## Quick Comparison

| Aspect | Custom Implementation | Official AgentBeats |
|--------|----------------------|-------------------|
| **Leaderboard** | FastAPI + SQLAlchemy | GitHub + DuckDB |
| **Storage** | PostgreSQL/SQLite | JSON in `/results/` |
| **Queries** | Custom ORM + REST API | DuckDB SQL |
| **Workflow** | Manual submission | GitHub Actions |
| **Hosting** | Self-hosted | agentbeats.dev |
| **Visibility** | Private/Internal | Public/Community |
| **Setup Time** | 30 mins | 10 mins |
| **Maintenance** | Database ops | Git ops |
| **Infrastructure** | Server required | GitHub only |
| **Cost** | Hosting fees | Free (GitHub) |

## When to Use Each Approach

### ✅ Use Custom Implementation For:

1. **Private Leaderboards**
   - Internal company benchmarks
   - Proprietary evaluation systems
   - Non-public research

2. **Advanced Analytics**
   - Complex SQL queries
   - Real-time dashboards
   - Custom metrics storage
   - Historical trend analysis

3. **Integration Needs**
   - Existing database systems
   - API-based workflows
   - Third-party integrations
   - Custom authentication

4. **Real-time Updates**
   - Live leaderboard scores
   - WebSocket updates
   - Immediate result reflection
   - Custom notification system

**Example**: Company-internal agent benchmarking system

### ✅ Use Official AgentBeats For:

1. **Public Benchmarks**
   - Shared research community
   - Open-source evaluations
   - Published benchmarks
   - Reproducible research

2. **Community Building**
   - Crowdsourced evaluations
   - Community agent participation
   - Shared leaderboards
   - Open competition

3. **Standards Compliance**
   - Reproducible workflows
   - Transparent evaluation
   - Published results
   - Peer-reviewed evaluation

4. **Ease of Deployment**
   - GitHub-native workflow
   - No infrastructure
   - Automatic updates
   - Built-in visibility

**Example**: Publishing GAIA benchmark publicly with community participation

## Architecture Diagram

### Custom Implementation

```
┌─────────────────────────────────────────────────┐
│          Your Infrastructure                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐         ┌──────────────┐    │
│  │ Green Agent  │────────▶│ Purple Agent │    │
│  └──────┬───────┘         └──────────────┘    │
│         │                                      │
│         │ Results                              │
│         ▼                                      │
│  ┌──────────────────────────────────────┐    │
│  │      FastAPI REST API                │    │
│  │  /leaderboard                        │    │
│  │  /submissions                        │    │
│  │  /agents/{name}/history              │    │
│  └────────────┬─────────────────────────┘    │
│               │                               │
│               ▼                               │
│  ┌──────────────────────────────────────┐    │
│  │    SQLAlchemy ORM (Database Layer)   │    │
│  │  - Submissions Table                 │    │
│  │  - Leaderboard Table                 │    │
│  │  - Webhook Events Table              │    │
│  └────────────┬─────────────────────────┘    │
│               │                               │
│               ▼                               │
│  ┌──────────────────────────────────────┐    │
│  │  PostgreSQL / SQLite (Persistent)    │    │
│  └──────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘

Web API:
- http://localhost:8000/leaderboard
- http://localhost:8000/api/submissions
- http://localhost:8000/docs (Swagger UI)
```

### Official AgentBeats

```
┌──────────────────────────────────────────────────────┐
│  GitHub Repository (Leaderboard)                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────┐        │
│  │  scenario.toml                         │        │
│  │  - Green Agent ID                      │        │
│  │  - Purple Agent ID                     │        │
│  │  - Assessment Config                   │        │
│  └──────────────────┬─────────────────────┘        │
│                     │                              │
│  ┌──────────────────▼──────────────────┐          │
│  │  .github/workflows/assessment.yml    │          │
│  │  - Runs on push to scenario.toml     │          │
│  │  - Generates docker-compose.yml     │          │
│  │  - Executes assessment               │          │
│  │  - Creates PR with results           │          │
│  └──────────────────┬────────────────────┘         │
│                     │                              │
│  ┌──────────────────▼────────────────────┐        │
│  │  GitHub Actions Runner                │        │
│  │  - Pulls agent images                 │        │
│  │  - Runs docker-compose                │        │
│  │  - Executes assessment                │        │
│  └──────────────────┬────────────────────┘        │
│                     │                              │
│  ┌──────────────────▼────────────────────┐        │
│  │  Assessment Results                   │        │
│  │  /results/yyyy-mm-dd-hhmm.json       │        │
│  │  {                                     │        │
│  │    "participants": {...},             │        │
│  │    "results": [...]                   │        │
│  │  }                                     │        │
│  └──────────────────┬────────────────────┘        │
│                     │                              │
│                     ▼                              │
│              GitHub Webhook                       │
│                     │                              │
└─────────────────────┼──────────────────────────────┘
                      │
                      ▼
            ┌──────────────────────┐
            │  AgentBeats.dev      │
            │                      │
            │  Leaderboard UI      │
            │  Query Engine (DuckDB)
            │  Results Database    │
            └──────────────────────┘
```

## Data Flow Comparison

### Custom Implementation

```
Evaluation:
1. Green agent evaluates purple agent
2. Results saved to database (Submission table)
3. Leaderboard entries materialized
4. Webhook events logged
5. API returns rankings on demand

Submission: Manual POST to /submissions or from green agent
Query: SQL via REST API endpoints
Update: Real-time (on every submission)
```

### Official AgentBeats

```
Evaluation:
1. GitHub Actions triggered (push to scenario.toml)
2. Docker compose runs assessment
3. Results written to JSON file
4. PR created with results
5. Manual merge approval
6. GitHub webhook notifies AgentBeats
7. AgentBeats reads results from repo
8. DuckDB queries generate leaderboard

Submission: Automatic PR creation from GitHub Actions
Query: DuckDB SQL (batch, no real-time)
Update: On merge (controlled updates)
```

## Data Format Comparison

### Custom Implementation: Database Schema

```sql
-- Submissions (per evaluation run)
CREATE TABLE submissions (
  submission_id TEXT PRIMARY KEY,
  agent_name TEXT,
  team_name TEXT,
  accuracy FLOAT,
  correct_tasks INT,
  total_tasks INT,
  task_results JSONB,
  timestamp DATETIME
);

-- Leaderboard (cached rankings)
CREATE TABLE leaderboard (
  rank INT,
  agent_name TEXT,
  accuracy FLOAT,
  submission_id TEXT,
  refreshed_at DATETIME
);
```

### Official AgentBeats: JSON Format

```json
{
  "participants": {
    "executor": "agent-id-12345"
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
      "accuracy": 100,
      "time_seconds": 2.5
    }
  ]
}
```

## Workflow Comparison

### Custom Implementation

```
┌─────────────────────────────────────────┐
│ Manual Result Submission                │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ POST /submissions    │
    │ with metrics         │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Database Insert      │
    │ Validate & Store     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Refresh Leaderboard  │
    │ Materialized Views   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ API Response         │
    │ Return Rankings      │
    └──────────────────────┘
```

### Official AgentBeats

```
┌────────────────────────────┐
│ Push to scenario.toml       │
└──────────┬─────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ GitHub Actions Workflow      │
│ - Generate docker-compose    │
│ - Run Assessment             │
│ - Save results.json          │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Create Pull Request          │
│ with results/yyyy-mm-dd.json │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Manual Review & Merge        │
│ (Quality Control)            │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ GitHub Webhook Notification  │
│ to AgentBeats                │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ AgentBeats Updates           │
│ - Read results.json          │
│ - Run DuckDB queries         │
│ - Update leaderboard UI      │
└──────────────────────────────┘
```

## Operational Differences

| Operation | Custom | Official |
|-----------|--------|----------|
| **Start New Benchmark** | Setup database, create tables | Fork template, edit scenario.toml |
| **Add Results** | POST to API | Push to GitHub, merge PR |
| **Query Leaderboard** | HTTP REST API | DuckDB SQL |
| **Authentication** | API keys | GitHub authentication |
| **Monitoring** | Database logs | GitHub Actions logs |
| **Backups** | Database backups | Git history, GitHub backups |
| **Scaling** | Database tuning | GitHub scaling (unlimited) |
| **Cost** | Server hosting | Free (GitHub) |
| **Discovery** | By URL only | Listed on agentbeats.dev |

## Migration Path

### From Custom to Official

If you start with custom and want to migrate:

1. Export results from database as JSON
2. Create leaderboard repo from official template
3. Add results to `/results/` folder
4. Push to GitHub
5. Set up webhook
6. Verify queries work with DuckDB

### From Official to Custom

If you need custom features later:

1. Export results from official GitHub repo
2. Set up PostgreSQL database
3. Import results to database tables
4. Start FastAPI server
5. Configure custom queries

## Recommendation for GAIA

### ✅ For Public Benchmark: Use Official AgentBeats

- Publish GAIA benchmark on agentbeats.dev
- Community agents can submit results
- Transparent, reproducible evaluation
- GitHub-native workflow
- No infrastructure costs

### ✅ For Internal Testing: Use Custom Implementation

- Keep in your feature branch (if needed)
- Private leaderboard
- Real-time updates
- Custom analytics
- Full control

## Summary

**Choose Custom Implementation** if you need:
- Private leaderboards
- Real-time dashboards
- Advanced analytics
- API integrations
- Full control

**Choose Official AgentBeats** if you need:
- Public benchmark visibility ✅
- Community participation ✅
- Standardized workflows ✅
- GitHub-native operations ✅
- **This is recommended for GAIA** ✅
