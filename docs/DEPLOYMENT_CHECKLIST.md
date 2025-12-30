# Leaderboard Deployment Checklist

## Pre-Deployment Setup

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set `OPENAI_API_KEY` in `.env`
- [ ] Set `HF_TOKEN` in `.env`
- [ ] Set `DATABASE_URL` (SQLite for local, PostgreSQL for production)
- [ ] Generate and set `GITHUB_WEBHOOK_SECRET` (if using webhooks)
- [ ] Set `LEADERBOARD_API_HOST` and `LEADERBOARD_API_PORT`

### 2. Dependencies
- [ ] Install dependencies: `pip install -e .`
- [ ] Verify SQLAlchemy: `python -c "import sqlalchemy; print(sqlalchemy.__version__)"`
- [ ] Verify FastAPI: `python -c "import fastapi; print(fastapi.__version__)"`
- [ ] For PostgreSQL: Install `pip install psycopg2-binary`
- [ ] Test all imports: `python -c "from src.agentbeats.database import *"`

### 3. Code Review
- [ ] Review `src/agentbeats/database.py` - SQLAlchemy models
- [ ] Review `src/agentbeats/github_webhook.py` - Webhook handler
- [ ] Review `src/leaderboard_api.py` - API endpoints
- [ ] Review `src/utils/leaderboard_queries.py` - SQL queries
- [ ] Review `src/green_agent/agent.py` - Agent integration

## Database Setup

### Local Development (SQLite)
```bash
# Initialize database
python scripts/setup_db.py init
# Expected: ✅ Database initialized successfully

# Verify setup
python scripts/setup_db.py check
# Expected: ✅ Database is accessible
#           ✅ All required tables exist

# Check stats
python scripts/setup_db.py stats
# Expected: Show 0 submissions, 0 teams
```

- [ ] Database file created: `agentbeats_leaderboard.db`
- [ ] All 3 tables exist (submissions, leaderboard, webhook_events)
- [ ] Indexes created properly

### Production (PostgreSQL)
```bash
# Create database
createdb gaia_leaderboard

# Set connection string
export DATABASE_URL="postgresql://user:password@host:5432/gaia"

# Initialize
python scripts/setup_db.py init

# Verify
python scripts/setup_db.py check
```

- [ ] PostgreSQL server running
- [ ] Database and user created
- [ ] Connection string correct
- [ ] All tables created in PostgreSQL
- [ ] Indexes exist in PostgreSQL

## Local Development Testing

### 1. API Server Startup
```bash
python -m src.leaderboard_api
# Expected: 
# INFO: Uvicorn running on http://0.0.0.0:8000
# ✅ Database tables initialized
```

- [ ] Server starts without errors
- [ ] Listens on correct port (default 8000)
- [ ] No database connection errors

### 2. Health Check
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] `curl http://localhost:8000/docs` shows API documentation
- [ ] All endpoints listed in Swagger UI

### 3. Direct Submission Test
```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test-agent",
    "agent_version": "1.0.0",
    "level": 1,
    "split": "validation",
    "accuracy": 75.5,
    "correct_tasks": 22,
    "total_tasks": 30,
    "average_time_per_task": 2.3,
    "total_time_seconds": 69.0
  }'
```

- [ ] Returns 200 with submission ID
- [ ] Submission appears in database: `python scripts/setup_db.py stats`
- [ ] Leaderboard updated

### 4. Leaderboard Query Test
```bash
curl http://localhost:8000/leaderboard?level=1&split=validation
```

- [ ] Returns valid JSON
- [ ] Shows submitted entry
- [ ] Proper ranking by accuracy
- [ ] All fields present

### 5. Full Endpoint Testing
- [ ] `GET /leaderboard` returns rankings
- [ ] `GET /leaderboard/teams` returns team rankings
- [ ] `GET /submissions/{id}` returns submission details
- [ ] `GET /agents/{name}/history` returns agent history
- [ ] `GET /teams/{name}/history` returns team history
- [ ] `GET /recent` returns recent submissions
- [ ] `GET /stats` returns statistics

### 6. Benchmark Execution Test
```bash
# Terminal 1: Start agents
python main.py green
python main.py purple

# Terminal 2: Run benchmark
python main.py launch --level 1 --task-ids "0,1,2"
```

- [ ] Green and purple agents start
- [ ] Benchmark runs to completion
- [ ] Results submitted to leaderboard
- [ ] Leaderboard updated: `curl http://localhost:8000/leaderboard`

## GitHub Webhook Setup (Optional)

### 1. Configuration
- [ ] Generate webhook secret:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Set `GITHUB_WEBHOOK_SECRET` in `.env`
- [ ] Restart API server

### 2. Local Testing (ngrok)
```bash
ngrok http 8000
# Get URL like: https://xxxx-xx-xxx-xxx-xx.ngrok.io
```

- [ ] ngrok tunnel created
- [ ] Shows forwarding URL
- [ ] Accessible from public internet

### 3. GitHub Repository Setup
- [ ] Go to repo Settings → Webhooks
- [ ] Click "Add webhook"
  - [ ] Payload URL: `https://your-domain.com/webhooks/github`
  - [ ] Content type: `application/json`
  - [ ] Secret: (your generated secret)
  - [ ] Events: `Pushes` and `Pull requests`
- [ ] Click "Add webhook"
- [ ] Green checkmark shows successful delivery

### 4. Test Submission
```bash
git commit -m "Test results

{
  \"gaia_submission\": {
    \"agent_name\": \"webhook-test\",
    \"agent_version\": \"1.0.0\",
    \"team_name\": \"test-team\",
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

- [ ] Webhook received (green checkmark in GitHub)
- [ ] Submission created in database
- [ ] Appears in leaderboard
- [ ] All GitHub metadata captured

## Production Deployment

### 1. Server Preparation
- [ ] Provision server (EC2, GCP, Azure, etc.)
- [ ] Install Python 3.11+
- [ ] Install PostgreSQL (recommended)
- [ ] Create database and user
- [ ] Configure firewall rules (allow port 8000 or 443)

### 2. Application Setup
- [ ] Clone repository
- [ ] Create `.env` with production values
- [ ] Install dependencies: `pip install -e .`
- [ ] Initialize database: `python scripts/setup_db.py init`
- [ ] Run verification: `python scripts/setup_db.py check`

### 3. Process Management (systemd)
Create `/etc/systemd/system/leaderboard.service`:
```ini
[Unit]
Description=GAIA Leaderboard API
After=network.target

[Service]
Type=simple
User=agentbeats
WorkingDirectory=/path/to/gaia-agentbeats
EnvironmentFile=/path/to/.env
ExecStart=/usr/bin/python -m src.leaderboard_api
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] Service file created
- [ ] Permissions set correctly
- [ ] Service enabled: `sudo systemctl enable leaderboard`
- [ ] Service started: `sudo systemctl start leaderboard`
- [ ] Status OK: `sudo systemctl status leaderboard`

### 4. Reverse Proxy (Nginx)
```nginx
upstream leaderboard {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://leaderboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] Nginx configured
- [ ] SSL certificates installed
- [ ] Service started: `sudo systemctl start nginx`
- [ ] Test: `curl https://your-domain.com/health`

### 5. GitHub Webhook (Production)
- [ ] Go to repo Settings → Webhooks
- [ ] Update Payload URL: `https://your-domain.com/webhooks/github`
- [ ] Keep same secret
- [ ] Verify green checkmark
- [ ] Test with commit

### 6. Monitoring & Logging
- [ ] Set up log rotation for API logs
- [ ] Configure monitoring (Prometheus, CloudWatch, etc.)
- [ ] Set up alerts for errors
- [ ] Monitor database size
- [ ] Track API response times
- [ ] Check webhook delivery logs

## Verification & Testing

### 1. Production API Endpoints
- [ ] `GET /health` → 200 OK
- [ ] `GET /leaderboard` → valid JSON
- [ ] `GET /stats` → statistics
- [ ] `POST /submissions` → creates submission
- [ ] `POST /webhooks/github` → accepts webhooks
- [ ] `GET /docs` → API documentation

### 2. Database Verification
- [ ] Tables created: `submissions`, `leaderboard`, `webhook_events`
- [ ] Indexes exist for performance
- [ ] Sample data persists after restart
- [ ] Database backups configured

### 3. GitHub Integration
- [ ] Webhook signature verified correctly
- [ ] JSON parsing works from commits
- [ ] Submissions created from webhooks
- [ ] Leaderboard updates automatically
- [ ] Webhook events logged

### 4. Performance Testing
- [ ] API response time < 500ms
- [ ] Leaderboard query < 200ms
- [ ] Webhook processing < 1s
- [ ] Under load: no connection drops
- [ ] Memory usage stable

## Documentation & Knowledge Transfer

- [ ] Team reviewed LEADERBOARD_SETUP.md
- [ ] Team reviewed WEBHOOK_EXAMPLES.md
- [ ] API docs at /docs explained
- [ ] Custom configurations documented
- [ ] Runbook created for common tasks
- [ ] Troubleshooting guide distributed

## Security Hardening

### API Security
- [ ] HTTPS/TLS enabled
- [ ] CORS configured properly
- [ ] Input validation working
- [ ] Rate limiting (if needed)
- [ ] Security headers set

### Database Security
- [ ] Strong passwords used
- [ ] Least-privilege access configured
- [ ] Connection encryption enabled (PostgreSQL)
- [ ] Backups encrypted
- [ ] Access logs enabled

### GitHub Integration
- [ ] Webhook secret set securely
- [ ] Signature verification enabled
- [ ] Payload size limits configured
- [ ] Webhook logs monitored

## Backup & Recovery

### Database Backups
- [ ] Daily automated backups configured
- [ ] Backups stored securely (encrypted)
- [ ] Test restore procedure
- [ ] Recovery steps documented
- [ ] Retention policy set (e.g., 30 days)

### Application Backups
- [ ] Configuration files backed up
- [ ] Code repository secure
- [ ] Environment files stored safely

### Backup Verification
- [ ] Can restore database from backup
- [ ] Restored data is correct
- [ ] Restore time acceptable
- [ ] Backup automation working

## Post-Deployment

### 1. Monitor First 24 Hours
- [ ] Check logs for errors
- [ ] Monitor database connections
- [ ] Watch for failed submissions
- [ ] Track error rates
- [ ] Monitor resource usage

### 2. Week 1 Monitoring
- [ ] Review webhook deliveries
- [ ] Check for slow queries
- [ ] Monitor storage growth
- [ ] Verify backups running
- [ ] Gather performance metrics

### 3. Ongoing Maintenance
- [ ] Weekly log review
- [ ] Monthly database maintenance
- [ ] Quarterly dependency updates
- [ ] Regular security reviews
- [ ] Performance optimization

## Rollback Procedure

If critical issues occur:

1. **Stop Service**
   ```bash
   sudo systemctl stop leaderboard
   ```

2. **Restore Database Backup**
   ```bash
   # SQLite
   cp /backup/leaderboard.db ./agentbeats_leaderboard.db
   
   # PostgreSQL
   psql database_name < /backup/backup.sql
   ```

3. **Revert Code Changes** (if needed)
   ```bash
   git revert <commit-hash>
   ```

4. **Restart Service**
   ```bash
   sudo systemctl start leaderboard
   ```

5. **Verify**
   ```bash
   curl https://your-domain.com/health
   ```

## Sign-Off

- [ ] All checklist items completed
- [ ] Testing passed successfully
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Team trained
- [ ] Ready for production use

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Approved By:** _______________  

## Quick Reference Commands

```bash
# Database
python scripts/setup_db.py init      # Initialize DB
python scripts/setup_db.py check     # Verify DB
python scripts/setup_db.py stats     # Show stats

# API
python -m src.leaderboard_api        # Start API
curl http://localhost:8000/health    # Health check

# System
sudo systemctl status leaderboard    # Check service
sudo systemctl restart leaderboard   # Restart
sudo journalctl -u leaderboard -f    # View logs

# Database CLI
sqlite3 agentbeats_leaderboard.db    # SQLite
psql -U user database_name           # PostgreSQL
```

---

**Document Version:** 2.0  
**Updated:** December 31, 2025  
**Status:** Ready for Deployment

# Verify
python scripts/setup_db.py check
```

### Database Verification
- [ ] Tables created: `submissions`, `leaderboard`, `webhook_events`
- [ ] Indexes created on frequently queried columns
- [ ] Can connect from application
- [ ] Database user has proper permissions
- [ ] Database backup configured (if production)

## API Testing

### Start API Server
```bash
# Development
python -m src.leaderboard_api

# Production with custom settings
LEADERBOARD_API_HOST=0.0.0.0 LEADERBOARD_API_PORT=8000 python -m src.leaderboard_api
```

### Test Endpoints
- [ ] Health check: `curl http://localhost:8000/health`
- [ ] Stats: `curl http://localhost:8000/stats`
- [ ] Empty leaderboard: `curl http://localhost:8000/leaderboard?level=1`
- [ ] Create submission: Test POST `/submissions` endpoint
- [ ] Get submission: Test GET with submission ID from above
- [ ] API docs: Visit `http://localhost:8000/docs`

### Test Responses
- [ ] All endpoints return valid JSON
- [ ] Error responses have proper HTTP status codes
- [ ] Response schemas match documentation
- [ ] Timestamps are ISO 8601 format
- [ ] Pagination works (limit parameter)

## GitHub Webhook Setup

### Generate Secret
```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Option 2: OpenSSL
openssl rand -hex 32

# Option 3: Use environment
export GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

### GitHub Configuration
- [ ] Go to repository Settings → Webhooks
- [ ] Add new webhook
  - [ ] Payload URL: `https://your-server.com/webhooks/github`
  - [ ] Content type: `application/json`
  - [ ] Secret: (paste generated secret)
  - [ ] Events: Push, Pull Request
  - [ ] Active: ✓
- [ ] Save webhook
- [ ] Check "Recent Deliveries" to see test attempts

### Environment Configuration
- [ ] Set `GITHUB_WEBHOOK_SECRET` environment variable
- [ ] Variable matches GitHub webhook secret exactly
- [ ] Restart API server after setting variable

### Test Webhook
```bash
# Create test commit with submission
git commit -m "Test submission

{
  \"gaia_submission\": {
    \"agent_name\": \"test-agent\",
    \"agent_version\": \"1.0.0\",
    \"team_name\": \"test-team\",
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

# Check webhook deliveries in GitHub
# Verify submission appears in database
curl http://localhost:8000/leaderboard?level=1
```

## Green Agent Integration

### Configuration Testing
- [ ] Verify `scenario.toml` has leaderboard settings
- [ ] Set `submit_to_leaderboard = true`
- [ ] Set `agent_name`, `agent_version`, `team_name`
- [ ] Optionally set `github_repo`, `github_commit`, `github_branch`

### Integration Testing
```bash
# Terminal 1: Start green agent
python src/green_agent/agent.py --host 127.0.0.1 --port 9001

# Terminal 2: Start purple agent
python src/purple_agent/agent.py --host 127.0.0.1 --port 9002

# Terminal 3: Run evaluation
python main.py launch --level 1 --task-ids "0,1,2" --split validation

# Terminal 4: Check submission
curl http://localhost:8000/leaderboard?level=1&limit=1
```

Verify:
- [ ] Evaluation completes successfully
- [ ] Leaderboard API is running
- [ ] Submission appears in database
- [ ] Leaderboard rankings are correct
- [ ] Agent name matches configuration

## Load Testing

### Small Load Test
```bash
# Submit 10 test submissions
for i in {1..10}; do
  curl -X POST http://localhost:8000/submissions \
    -H "Content-Type: application/json" \
    -d "{
      \"agent_name\": \"load-test-agent-$i\",
      \"agent_version\": \"1.0.0\",
      \"level\": 1,
      \"split\": \"validation\",
      \"accuracy\": $((70 + RANDOM % 30)).0,
      \"correct_tasks\": $((20 + RANDOM % 10)),
      \"total_tasks\": 30,
      \"average_time_per_task\": 2.3,
      \"total_time_seconds\": 69.0
    }"
done

# Verify all submissions in database
curl http://localhost:8000/stats
```

Verify:
- [ ] API responds quickly (< 200ms)
- [ ] All submissions saved correctly
- [ ] Leaderboard rankings are accurate
- [ ] No database errors in logs
- [ ] Indexes are being used (check query performance)

## Monitoring Setup

### Logging
- [ ] Configure logging in `src/leaderboard_api.py`
- [ ] Log directory created and writable
- [ ] Logs include timestamps and levels
- [ ] Monitor common errors: database connection, validation errors

### Metrics
- [ ] Track API response times
- [ ] Monitor database connection pool
- [ ] Count submissions per day/week/month
- [ ] Track webhook success/failure rate

### Alerts
- [ ] Database connection failures
- [ ] API server crashes
- [ ] Webhook verification failures
- [ ] Unusual submission patterns

## Security

### Database
- [ ] Database credentials in `.env`, not committed
- [ ] Database backups encrypted
- [ ] User permissions: least privilege principle
- [ ] Connection pooling configured
- [ ] SQL injection prevention (using ORM)

### API
- [ ] Rate limiting configured (if public)
- [ ] Input validation on all endpoints
- [ ] HTTPS enabled in production
- [ ] Webhook signature verification enabled
- [ ] CORS configured appropriately

### GitHub
- [ ] Webhook secret is strong (32+ hex chars)
- [ ] Secret never exposed in logs/code
- [ ] Webhook events logged for audit
- [ ] Signature verification enabled

## Backup & Recovery

### Database Backups
```bash
# SQLite backup
cp agentbeats_leaderboard.db agentbeats_leaderboard.db.backup

# PostgreSQL backup
pg_dump gaia_leaderboard > backup.sql

# Scheduled backups (daily at 2 AM)
0 2 * * * pg_dump gaia_leaderboard > /backups/gaia_$(date +\%Y\%m\%d).sql
```

- [ ] Automated backup schedule configured
- [ ] Backups stored in secure location
- [ ] Backup retention policy defined (30+ days)
- [ ] Backup restoration tested

### Recovery Plan
- [ ] Database recovery procedure documented
- [ ] Time to recover (RTO) target defined
- [ ] Recovery tested with backup data
- [ ] Failover procedure documented

## Documentation

### User Documentation
- [ ] LEADERBOARD_SETUP.md complete and tested
- [ ] WEBHOOK_EXAMPLES.md has working examples
- [ ] LEADERBOARD_QUICK_REF.md is accessible
- [ ] API docs generated (visit `/docs`)

### Deployment Documentation
- [ ] Infrastructure requirements documented
- [ ] Environment variables documented
- [ ] Troubleshooting guide completed
- [ ] Support contact information available

## Post-Deployment

### Verification
- [ ] API responding on all endpoints
- [ ] Database connected and populated
- [ ] Webhooks processing correctly
- [ ] Agent integration working
- [ ] Leaderboard rankings accurate

### Monitoring
- [ ] Set up log collection
- [ ] Configure alerts
- [ ] Monitor key metrics
- [ ] Regular health checks

### Performance
- [ ] API response times < 200ms
- [ ] Database query times < 500ms
- [ ] Webhook processing < 1 second
- [ ] No memory leaks or connection issues

### User Communication
- [ ] Share leaderboard API documentation
- [ ] Explain webhook submission process
- [ ] Provide example configurations
- [ ] Set expectations for update frequency

## Maintenance

### Weekly
- [ ] Review error logs
- [ ] Check database size
- [ ] Verify backups completed
- [ ] Monitor API metrics

### Monthly
- [ ] Database optimization
- [ ] Index usage analysis
- [ ] Query performance review
- [ ] Security audit

### Quarterly
- [ ] Dependency updates
- [ ] Performance tuning
- [ ] Disaster recovery test
- [ ] Capacity planning

## Rollback Plan

If deployment fails:
```bash
# Restore from backup
cp agentbeats_leaderboard.db.backup agentbeats_leaderboard.db

# Or restore PostgreSQL
psql gaia_leaderboard < backup.sql

# Restart services
systemctl restart leaderboard-api

# Verify health
curl http://localhost:8000/health
```

- [ ] Backup available and tested
- [ ] Rollback procedure documented
- [ ] Team trained on rollback process
- [ ] Estimated rollback time: < 5 minutes

## Sign-Off

- [ ] Development Lead: _______________  Date: ______
- [ ] DevOps/Infrastructure: _______________  Date: ______
- [ ] QA/Testing: _______________  Date: ______
- [ ] Product Manager: _______________  Date: ______

## Notes

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________
