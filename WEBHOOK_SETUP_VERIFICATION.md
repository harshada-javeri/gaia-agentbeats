# ✅ Webhook Setup Verification Guide

Based on **AgentBeats Official Tutorial** - Webhooks Section

## 🎯 Correct Webhook Flow

The AgentBeats webhook is specifically designed for **leaderboard repository integration**, not general code repository webhooks.

### ✅ What Should Happen

1. **You (or GitHub Actions) push results** to your **leaderboard repository**
2. **GitHub sends a webhook** to AgentBeats webhook URL
3. **AgentBeats receives the push event** and parses the result JSON
4. **Leaderboard auto-updates** with new results

---

## 🔧 Setup Checklist

### Part 1: Get the Webhook URL from AgentBeats

- [ ] Go to your green agent page on AgentBeats
- [ ] Find the **"Webhook Integration"** box
- [ ] Copy the webhook URL (format: `https://agentbeats.dev/api/hook/v2/<token>`)

### Part 2: Configure GitHub Webhook (Leaderboard Repo ONLY)

1. [ ] Go to your **leaderboard repository** on GitHub
2. [ ] Navigate to: **Settings → Webhooks**
3. [ ] Click **"Add webhook"**
4. [ ] Fill in exactly:

| Setting | Value |
|---------|-------|
| **Payload URL** | `https://agentbeats.dev/api/hook/v2/<token>` (from Part 1) |
| **Content type** | `application/json` |
| **Events** | "Send me everything" OR "Push events" |
| **Active** | ✅ Checked |

5. [ ] Click **"Add webhook"**

### Part 3: Verify Webhook is Working

After pushing new results to your leaderboard repo:

1. [ ] Go to leaderboard repo → Settings → Webhooks
2. [ ] Click on your webhook
3. [ ] Scroll to **"Recent Deliveries"**
4. [ ] Check the most recent delivery:
   - [ ] Status should be **✅ (green checkmark)**
   - [ ] Response code should be **200** or **202**
   - [ ] If **400**: payload format mismatch with AgentBeats expectations

---

## ❌ What NOT to Do

- ❌ **Do NOT** add webhook to your **code repository**
- ❌ **Do NOT** point the webhook to generic code push events
- ❌ **Do NOT** use a different webhook URL than what AgentBeats provides
- ❌ **Do NOT** send arbitrary GitHub events to the AgentBeats webhook

The AgentBeats webhook endpoint is specifically built to parse leaderboard result payloads, not generic GitHub push events.

---

## 🧪 Testing the Webhook

### Manual Test: Push Results to Leaderboard Repo

```bash
# In your leaderboard repository
cd /path/to/leaderboard-repo

# Create or update a results file
echo '{"results": "..."}' > results.json

# Commit and push
git add results.json
git commit -m "New benchmark results"
git push origin main
```

Then check:
1. GitHub webhook delivery logs (should show 200/202)
2. AgentBeats leaderboard page (should show updated results within 30 seconds)

### Debug: Check Webhook Payload Format

Your webhook endpoint expects payloads from the leaderboard repo push events. The `github_webhook.py` handler:
- Looks for GAIA configuration in commit messages or PR bodies
- Extracts JSON with `"gaia_submission"` key
- Creates submissions in the database
- Returns proper status codes

If you see HTTP 400 errors:
- Verify the payload contains valid GAIA configuration JSON
- Check webhook is on the **correct repository** (leaderboard repo)
- Ensure commit message or PR body has properly formatted `gaia_submission` JSON

---

## 📋 Current Implementation

Your codebase already implements webhook handling correctly:

- **File**: `src/agentbeats/github_webhook.py`
- **Features**: 
  - ✅ Signature verification
  - ✅ GAIA config extraction from commit messages
  - ✅ PR body parsing support
  - ✅ Database logging of webhook events
  - ✅ Submission creation on valid payloads

**No code changes needed** — just ensure webhooks are configured on the leaderboard repo, not the code repo.

---

## 🚀 Next Steps

1. Verify webhook is ONLY on leaderboard repo
2. Remove any webhooks from code repository (if present)
3. Push a test result to leaderboard repo
4. Check webhook delivery logs for 200/202 status
5. Verify leaderboard updates automatically
