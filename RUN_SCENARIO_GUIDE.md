# 🔬 Running GAIA Scenario Locally & Submitting Results

Complete guide for running the GAIA benchmark assessment locally and pushing results to your leaderboard.

---

## 📋 Prerequisites

Before you start, ensure you have:

- [ ] Docker installed and running
- [ ] Python 3.10+ installed
- [ ] OpenAI API key
- [ ] Your agent IDs from AgentBeats (if doing registered submission)
- [ ] Leaderboard repository cloned locally
- [ ] Published Docker images or local images for testing

---

## 🚀 Step 1: Prepare Environment

### Install Dependencies

```bash
cd /Users/harshada/Project/gaia-agentbeats

# Install required Python packages
pip install tomli-w requests
```

### Set Up Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your secrets:
# OPENAI_API_KEY=sk-...
nano .env
```

---

## 🧪 Step 2: Run Locally with Test Images

For **local testing** (before registering agents), use the `image` field instead of `agentbeats_id`:

### Edit scenario.toml for Local Testing

```toml
[green_agent]
# Use 'image' for local testing (NOT agentbeats_id)
image = "ghcr.io/harshada-javeri/gaia-evaluator:latest"
env = { OPENAI_API_KEY = "${OPENAI_API_KEY}" }

[[participants]]
# Use 'image' for local testing
image = "ghcr.io/harshada-javeri/gaia-executor:latest"
name = "executor"
env = { OPENAI_API_KEY = "${OPENAI_API_KEY}" }

[config]
level = 1
split = "validation"
task_indices = [0, 1, 2]  # Test with first 3 tasks
```

### Generate Docker Compose File

```bash
# Generate docker-compose from scenario
python generate_compose.py --scenario scenario.toml

# This creates docker-compose.yml in current directory
```

### Create Output Directory

```bash
mkdir -p output
```

### Run the Assessment

```bash
# Start the assessment (will exit when complete)
docker compose up --abort-on-container-exit
```

**What this does:**
- Pulls your agent images from registry
- Runs green agent (evaluator) on port 9001
- Runs purple agent (executor) on port 9002  
- Executes the configured tasks
- Saves results to `output/` directory
- Cleans up containers after completion

---

## 📊 Step 3: Check Results

### View Generated Results

```bash
# List all generated files
ls -la output/

# View the main results JSON
cat output/results.json | jq .
```

### Sample Output Structure

The `output/` folder should contain:
- `results.json` - Main benchmark results
- `logs/` - Execution logs from agents
- `artifacts/` - Any generated artifacts

---

## 🚢 Step 4: Submit to Leaderboard

### Option A: Manual Submission (For Testing)

```bash
# Copy results to your leaderboard repo
cp output/results.json \
   /path/to/gaia-benchmark-leaderboard/results/gaia-result-$(date +%Y%m%d-%H%M%S).json

# Commit and push
cd /path/to/gaia-benchmark-leaderboard
git add results/
git commit -m "GAIA benchmark result - Level 1 validation"
git push origin main
```

### Option B: GitHub Actions (For Registered Agents)

Once agents are registered, use `agentbeats_id` in scenario.toml:

```toml
[green_agent]
agentbeats_id = "agent_green_xxxxx"  # From AgentBeats
env = { OPENAI_API_KEY = "${OPENAI_API_KEY}" }

[[participants]]
agentbeats_id = "agent_purple_xxxxx"  # From AgentBeats
name = "executor"
env = { OPENAI_API_KEY = "${OPENAI_API_KEY}" }

[config]
level = 1
split = "validation"
task_indices = [0, 1, 2]
```

Then push scenario.toml to leaderboard repo and GitHub Actions will:
1. Run the assessment automatically
2. Generate results
3. Create a PR with results
4. You merge the PR → webhook triggers → leaderboard updates

---

## 🔍 Troubleshooting

### Docker images not found?

```bash
# Build your images locally first
docker build -t gaia-evaluator:latest -f Dockerfile.gaia-evaluator .
docker build -t gaia-executor:latest -f Dockerfile.gaia-executor .

# Update scenario.toml to use local images:
# image = "gaia-evaluator:latest"
# image = "gaia-executor:latest"
```

### Port already in use?

```bash
# Kill processes on ports 9001 and 9002
lsof -ti:9001,9002 | xargs kill -9

# Or use docker to clean up
docker ps
docker stop <container_id>
```

### Missing OpenAI API key?

```bash
# Verify .env has the key
grep OPENAI_API_KEY .env

# Or set it inline
export OPENAI_API_KEY="sk-..."
docker compose up --abort-on-container-exit
```

### Results not generated?

```bash
# Check docker compose logs
docker compose logs --tail 50

# Check if containers are still running
docker ps -a

# Review output directory
ls -la output/
find output/ -type f
```

---

## 📈 Workflow Summary

### Local Development Loop

```
1. Edit scenario.toml (use 'image' field)
   ↓
2. python generate_compose.py --scenario scenario.toml
   ↓
3. docker compose up --abort-on-container-exit
   ↓
4. Check output/ directory for results
   ↓
5. Review and validate results locally
   ↓
6. Once satisfied, copy to leaderboard repo & push
   ↓
7. Check GitHub webhook delivery logs
   ↓
8. Verify results appear on AgentBeats leaderboard
```

### Production Submission Flow

```
1. Edit scenario.toml (use 'agentbeats_id' field)
   ↓
2. Push scenario.toml to leaderboard repo
   ↓
3. GitHub Actions workflow runs automatically
   ↓
4. Results are generated in submissions/ folder
   ↓
5. PR is created for you to review & merge
   ↓
6. Webhook fires when you merge PR
   ↓
7. Results appear on AgentBeats leaderboard
```

---

## 🎯 Next Actions

1. **For Quick Testing:**
   - [ ] Update scenario.toml with test images
   - [ ] Run `python generate_compose.py --scenario scenario.toml`
   - [ ] Run `docker compose up --abort-on-container-exit`
   - [ ] Check results in `output/`

2. **For Leaderboard Submission:**
   - [ ] Copy results to leaderboard repo
   - [ ] Commit and push
   - [ ] Verify webhook in GitHub
   - [ ] Check leaderboard after 30 seconds

3. **For Production (Registered Agents):**
   - [ ] Update scenario.toml with `agentbeats_id`
   - [ ] Push to leaderboard repo
   - [ ] Let GitHub Actions handle execution
   - [ ] Merge resulting PR
   - [ ] Monitor leaderboard updates

---

## 🔗 Useful Commands

```bash
# Generate compose file
python generate_compose.py --scenario scenario.toml

# Run assessment
docker compose up --abort-on-container-exit

# View results
jq . output/results.json

# Clean up
docker compose down
docker system prune -f

# Push to leaderboard
git add results/
git commit -m "New GAIA result submission"
git push origin main
```

---

## 📚 References

- **AgentBeats Docs**: https://docs.agentbeats.dev/tutorial
- **Your Agent**: https://agentbeats.dev/harshada-javeri/g-agent
- **Leaderboard**: https://agentbeats.dev/harshada-javeri/g-agent/leaderboard
- **Sample Result**: `/Users/harshada/Project/gaia-agentbeats/results/gaia-result-*.json`
