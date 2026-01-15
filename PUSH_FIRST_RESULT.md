# 🚀 Push Your First GAIA Result to Leaderboard

Your sample result is ready! Follow these steps to push it to your leaderboard repo and see it appear on AgentBeats.

## 📋 Prerequisites

Before you start, make sure you have:
- [ ] A leaderboard repository created from the AgentBeats template
  - Template: https://github.com/RDI-Foundation/agentbeats-leaderboard-template
  - Should be named: `gaia-benchmark-leaderboard` 
  - URL format: `https://github.com/yourusername/gaia-benchmark-leaderboard`

- [ ] Your agent registered on AgentBeats
  - URL: https://agentbeats.dev/harshada-javeri/g-agent

- [ ] Webhook configured on your leaderboard repo (see WEBHOOK_SETUP_VERIFICATION.md)

---

## 🔧 Steps to Push Your First Result

### Step 1: Clone Your Leaderboard Repository

```bash
# Clone your leaderboard repo
git clone https://github.com/yourusername/gaia-benchmark-leaderboard.git
cd gaia-benchmark-leaderboard

# Verify the structure has these folders:
# - results/          (where result JSONs go)
# - .github/workflows/ (GitHub Actions runner)
# - leaderboard_config.json
# - scenario.toml
```

If you don't have a leaderboard repo yet:
1. Go to https://github.com/RDI-Foundation/agentbeats-leaderboard-template
2. Click "Use this template"
3. Name it: `gaia-benchmark-leaderboard`
4. Set visibility to "Public"
5. Create the repository
6. Clone it locally

---

### Step 2: Copy the Sample Result

```bash
# Copy the generated result to your leaderboard repo
cp /Users/harshada/Project/gaia-agentbeats/results/gaia-result-*.json \
   /path/to/gaia-benchmark-leaderboard/results/

# Verify it's there
ls -la gaia-benchmark-leaderboard/results/
```

---

### Step 3: Commit and Push

```bash
cd /path/to/gaia-benchmark-leaderboard

# Add the new result
git add results/

# Commit with a descriptive message
git commit -m "Test GAIA benchmark result submission - Level 1 validation split"

# Push to main branch (or your configured branch)
git push origin main
```

---

### Step 4: Verify the Webhook Was Triggered

1. **GitHub Webhook Logs**
   - Go to your leaderboard repo on GitHub
   - Settings → Webhooks
   - Click on your AgentBeats webhook
   - Scroll to "Recent Deliveries"
   - ✅ You should see your push event with status **200** or **202**

2. **AgentBeats Leaderboard** (wait 30 seconds)
   - Visit: https://agentbeats.dev/harshada-javeri/g-agent
   - Go to the "Leaderboard" tab
   - Your result should appear! 🎉

---

## 🧪 Troubleshooting

### Webhook shows 400 error?
- Check that the webhook is configured on the **leaderboard repo** (not your code repo)
- Verify the payload URL matches AgentBeats format: `https://agentbeats.dev/api/hook/v2/<token>`

### Result doesn't appear on leaderboard?
- Wait 30-60 seconds for the webhook to process
- Check GitHub Actions tab to see if any workflow ran
- Verify your agent is registered with the correct ID in AgentBeats

### File not found when pushing?
```bash
# Make sure you're in the right directory
pwd  # Should end with: .../gaia-benchmark-leaderboard

# Check if results directory exists
ls -la results/
```

---

## 📊 Next Steps After Success

Once your first result appears on the leaderboard:

1. **Run a real evaluation**
   ```bash
   # In your gaia-agentbeats repo
   python main.py launch --level 1 --task-ids "0,1,2,3,4,5" --split validation
   ```

2. **Format and save actual results** 
   - Parse output from the evaluation
   - Save to your leaderboard repo's `results/` folder
   - Commit and push

3. **Share your leaderboard**
   - Copy your leaderboard URL
   - Share on GitHub, Twitter, or team channels

4. **Monitor leaderboard growth**
   - Watch results accumulate as agents submit
   - Check webhook activity in GitHub

---

## 🔗 Quick Links

- **Your Agent**: https://agentbeats.dev/harshada-javeri/g-agent
- **AgentBeats Docs**: https://docs.agentbeats.dev/tutorial
- **Leaderboard Template**: https://github.com/RDI-Foundation/agentbeats-leaderboard-template
- **Sample Result**: `/Users/harshada/Project/gaia-agentbeats/results/gaia-result-*.json`
