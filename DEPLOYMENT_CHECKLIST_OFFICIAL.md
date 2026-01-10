# Official AgentBeats Deployment Checklist

## ✅ Phase 1: Code Alignment (COMPLETE)

- [x] Updated scenario.toml to use `agentbeats_id` format
- [x] Removed database dependencies from pyproject.toml
- [x] Added DuckDB support
- [x] Removed custom submission logic from green agent
- [x] Created GitHub Actions workflow
- [x] Created generate_compose.py tool
- [x] Updated .env.example
- [x] Committed to feature branch

**Status**: ✅ Complete - 2 commits on feature branch

---

## 📋 Phase 2: AgentBeats Registration (TO DO)

### Step 1: Register Green Agent (15 mins)
- [ ] Build Docker image: `docker build --platform linux/amd64 -t ghcr.io/yourusername/gaia-evaluator:v1.0 .`
- [ ] Push to registry: `docker push ghcr.io/yourusername/gaia-evaluator:v1.0`
- [ ] Go to https://agentbeats.dev/
- [ ] Click "Register Agent" (top right)
- [ ] Select "Green Agent"
- [ ] Fill in:
  - [ ] Display Name: "GAIA Evaluator"
  - [ ] Docker Image: `ghcr.io/yourusername/gaia-evaluator:v1.0`
  - [ ] Repository URL: `https://github.com/yourusername/gaia-agentbeats`
- [ ] Click "Register"
- [ ] **Copy Green Agent ID**: `agent_green_xxxxx`

### Step 2: Create Leaderboard Repository (5 mins)
- [ ] Go to https://github.com/RDI-Foundation/agentbeats-leaderboard-template
- [ ] Click "Use this template" → "Create a new repository"
- [ ] Name: `gaia-benchmark-leaderboard`
- [ ] Visibility: **Public**
- [ ] Click "Create repository"

### Step 3: Register Purple Agent (15 mins) [Optional]
- [ ] Build Docker image: `docker build --platform linux/amd64 -t ghcr.io/yourusername/gaia-executor:v1.0 .`
- [ ] Push to registry: `docker push ghcr.io/yourusername/gaia-executor:v1.0`
- [ ] Go to https://agentbeats.dev/
- [ ] Click "Register Agent"
- [ ] Select "Purple Agent"
- [ ] Fill in agent details
- [ ] Click "Register"
- [ ] **Copy Purple Agent ID**: `agent_purple_yyyyy`

---

## ⚙️ Phase 3: Configuration (TO DO)

### Step 1: Clone Leaderboard Repo
```bash
git clone https://github.com/yourusername/gaia-benchmark-leaderboard.git
cd gaia-benchmark-leaderboard
```

### Step 2: Configure scenario.toml
- [ ] Edit `scenario.toml`
- [ ] Add green agent ID:
  ```toml
  [green_agent]
  agentbeats_id = "agent_green_xxxxx"  # Your green agent ID
  ```
- [ ] Add purple agent ID (if you registered one):
  ```toml
  [[participants]]
  agentbeats_id = "agent_purple_yyyyy"
  ```
- [ ] Verify config looks correct:
  ```bash
  cat scenario.toml
  ```

### Step 3: Add GitHub Secret
- [ ] Go to your leaderboard repo → Settings
- [ ] Go to "Secrets and variables" → "Actions"
- [ ] Click "New repository secret"
- [ ] Name: `OPENAI_API_KEY`
- [ ] Value: Your actual OpenAI API key
- [ ] Click "Add secret"

### Step 4: Verify Workflow
- [ ] Check `.github/workflows/assessment.yml` exists
- [ ] Verify it has your assessment config
- [ ] Commit changes:
  ```bash
  git add scenario.toml
  git commit -m "Configure GAIA assessment for AgentBeats"
  git push origin main
  ```

---

## 🧪 Phase 4: Local Testing (TO DO)

### Step 1: Test generate_compose.py
```bash
# Copy the tool from your main repo
cp ../gaia-agentbeats/generate_compose.py .

# Install dependencies
pip install tomli-w requests pyyaml

# Generate docker-compose.yml
python generate_compose.py --scenario scenario.toml

# Verify output
ls -la docker-compose.yml
cat docker-compose.yml
```

### Step 2: Test Locally (Optional)
```bash
# Set environment variables
cp .env.example .env
# Edit .env to add OPENAI_API_KEY

# Create output directory
mkdir -p output

# Run with docker-compose
docker compose up --abort-on-container-exit

# Check results
ls output/results.json
cat output/results.json
```

### Step 3: Verify Results Format
- [ ] Results are in `/results/` folder
- [ ] Format matches expected JSON structure:
  ```json
  {
    "participants": {"executor": "agent-id"},
    "config": {...},
    "results": [...]
  }
  ```

---

## 🚀 Phase 5: Deploy Assessment (TO DO)

### Step 1: Trigger GitHub Actions
```bash
# Push to main branch (should trigger workflow)
git add .
git commit -m "Ready for first assessment"
git push origin main
```

### Step 2: Monitor Workflow
- [ ] Go to your leaderboard repo → Actions
- [ ] Click on the latest workflow run
- [ ] Wait for assessment to complete (may take 5-30 mins)
- [ ] Check for errors in logs
- [ ] Look for "Submit your results" link in workflow summary

### Step 3: Create PR with Results
- [ ] Click "Submit your results" link from workflow
- [ ] Review the PR with results.json
- [ ] Click "Create pull request"

### Step 4: Merge Results
- [ ] Review PR changes
- [ ] Click "Merge pull request"
- [ ] Confirm merge

---

## 🎯 Phase 6: Leaderboard Configuration (TO DO)

### Step 1: Connect Leaderboard to Agent
1. [ ] Go to your green agent page on agentbeats.dev
2. [ ] Click "Edit Agent"
3. [ ] Scroll to "Leaderboard Repository"
4. [ ] Enter your leaderboard repo URL:
   ```
   https://github.com/yourusername/gaia-benchmark-leaderboard
   ```
5. [ ] Click "Save"

### Step 2: Add Leaderboard Queries
1. [ ] Still on agent edit page
2. [ ] Scroll to "Leaderboard Configuration"
3. [ ] Add DuckDB query for rankings:
   ```json
   [
     {
       "name": "Overall Performance",
       "query": "SELECT results.participants.executor AS id, COUNT(*) as tasks, SUM(CASE WHEN r.result.passed THEN 1 ELSE 0 END) as passed FROM results CROSS JOIN UNNEST(results.results) AS r(result) GROUP BY id ORDER BY passed DESC"
     }
   ]
   ```
4. [ ] Click "Save"

### Step 3: Set Up Webhook
1. [ ] On agent edit page, scroll to "Webhook Integration"
2. [ ] Copy webhook URL
3. [ ] Go to leaderboard repo → Settings → Webhooks
4. [ ] Click "Add webhook"
5. [ ] Fill in:
   - [ ] **Payload URL**: Paste webhook URL
   - [ ] **Content type**: `application/json`
   - [ ] **Events**: "Push events"
   - [ ] **Active**: Checked
6. [ ] Click "Add webhook"

---

## ✨ Phase 7: Launch Benchmark (TO DO)

### Step 1: Verify Leaderboard is Live
- [ ] Go to: `https://agentbeats.dev/agents/agent_green_xxxxx/leaderboard`
- [ ] Verify your results appear
- [ ] Check leaderboard formatting

### Step 2: Promote Your Benchmark
- [ ] Add benchmark link to README
- [ ] Share with research community
- [ ] Announce on social media
- [ ] Publish benchmark paper/report

### Step 3: Invite Community
- [ ] Send leaderboard link to colleagues
- [ ] Create issues for baseline agents
- [ ] Encourage submissions
- [ ] Monitor leaderboard growth

---

## 📚 Reference Documents

### For Setup
- [AGENTBEATS_QUICKSTART.md](AGENTBEATS_QUICKSTART.md) - 5-step overview
- [docs/AGENTBEATS_OFFICIAL_SETUP.md](docs/AGENTBEATS_OFFICIAL_SETUP.md) - Detailed guide

### For Queries
- [docs/DUCKDB_LEADERBOARD_QUERIES.md](docs/DUCKDB_LEADERBOARD_QUERIES.md) - Query examples

### For Understanding
- [docs/ARCHITECTURE_COMPARISON.md](docs/ARCHITECTURE_COMPARISON.md) - Design decisions
- [docs/OFFICIAL_AGENTBEATS_MIGRATION.md](docs/OFFICIAL_AGENTBEATS_MIGRATION.md) - What changed
- [OFFICIAL_AGENTBEATS_SUMMARY.md](OFFICIAL_AGENTBEATS_SUMMARY.md) - Complete summary

### Official Resources
- **AgentBeats Docs**: https://docs.agentbeats.dev/
- **AgentBeats Platform**: https://agentbeats.dev/
- **Official Templates**: https://github.com/RDI-Foundation/

---

## 🆘 Troubleshooting

### Workflow Not Running
- [ ] Verify `.github/workflows/assessment.yml` exists
- [ ] Check if scenario.toml was committed
- [ ] View Actions tab for error logs

### Results Not Appearing
- [ ] Check GitHub Actions logs
- [ ] Verify Docker images are accessible
- [ ] Ensure environment variables are set
- [ ] Check result JSON format

### Leaderboard Not Updating
- [ ] Verify webhook is configured
- [ ] Check webhook delivery logs (GitHub)
- [ ] Ensure PR was merged
- [ ] Wait 30 seconds for webhook to process

### Docker Build Fails
- [ ] Verify Docker daemon is running
- [ ] Check Docker login: `docker login ghcr.io`
- [ ] Verify platform flag: `--platform linux/amd64`

---

## ✅ Final Checklist

### Before Launch
- [ ] Code is on feature branch
- [ ] All documentation is complete
- [ ] GitHub Actions workflow tested
- [ ] Docker images published
- [ ] Agents registered on AgentBeats
- [ ] Scenario configured with agent IDs
- [ ] GitHub secrets added
- [ ] Webhook configured
- [ ] First assessment succeeded
- [ ] Results appear on leaderboard

### After Launch
- [ ] Leaderboard is public
- [ ] Benchmark is shareable
- [ ] Community can see results
- [ ] Agents can submit to leaderboard
- [ ] Queries display correctly

---

## �� Next Steps

1. **Immediate** (Today)
   - [ ] Review AGENTBEATS_QUICKSTART.md
   - [ ] Verify feature branch is ready

2. **This Week**
   - [ ] Register green agent on AgentBeats
   - [ ] Create leaderboard repository
   - [ ] Configure scenario.toml

3. **This Week**
   - [ ] Test GitHub Actions locally
   - [ ] Run first assessment
   - [ ] Verify results on leaderboard

4. **This Month**
   - [ ] Set up DuckDB queries
   - [ ] Configure webhook
   - [ ] Launch public benchmark
   - [ ] Promote to community

---

**Status**: Ready for Phase 2 deployment
**Documentation**: Complete and comprehensive
**Code**: Tested and aligned with official AgentBeats
**Next**: Begin Phase 2 registration

Your GAIA Benchmark is ready for the public! 🎉
