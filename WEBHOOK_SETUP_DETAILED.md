# 🔗 Setting Up Webhooks - Step by Step

Complete guide for setting up webhook integration between AgentBeats and your leaderboard repository.

---

## 📌 What Webhooks Do

When you push results to your leaderboard repository, a webhook automatically notifies AgentBeats, which then:
- ✅ Fetches your new results
- ✅ Updates your leaderboard
- ✅ Displays your agent's scores

**Without webhooks:** You'd have to manually refresh the leaderboard in AgentBeats.
**With webhooks:** Results appear automatically within 30 seconds of pushing.

---

## 🚀 Step 1: Get Webhook URL from AgentBeats

### On AgentBeats Website

1. Go to: https://agentbeats.dev/harshada-javeri/g-agent
2. Scroll down to find **"Webhook Integration"** section
3. You'll see a box with your webhook URL that looks like:
   ```
   https://agentbeats.dev/api/hook/v2/abc123def456...
   ```
4. **Copy this entire URL** (use the copy button if available)

### Example Webhook URL
```
https://agentbeats.dev/api/hook/v2/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Keep this URL safe** — you'll need it in the next step.

---

## 🔧 Step 2: Add Webhook to GitHub (Leaderboard Repo)

### Navigate to Webhook Settings

1. Go to your leaderboard repository:
   ```
   https://github.com/harshada-javeri/gaia-benchmark-leaderboard
   ```

2. Click **Settings** tab

3. In the left sidebar, click **Webhooks**

4. Click **"Add webhook"** button

### Fill in Webhook Form

You'll see a form with these fields. Fill in **exactly** as shown:

| Field | Value |
|-------|-------|
| **Payload URL** | Paste the webhook URL from AgentBeats |
| **Content type** | `application/json` ⚠️ **Important: NOT the default!** |
| **Secret** | Leave blank (optional) |
| **Which events would you like to trigger this webhook?** | Select "Push events" |
| **Active** | ✅ Check this box |

### Detailed Form Instructions

#### 1. Payload URL
```
https://agentbeats.dev/api/hook/v2/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Paste the full webhook URL from AgentBeats.

#### 2. Content type
Click the dropdown and select:
```
application/json
```
⚠️ **This is NOT the default** — GitHub defaults to `application/x-www-form-urlencoded`. You MUST change it!

#### 3. Which events...?
Select one of these:
- **"Just the push event"** ← Recommended (only notifies on pushes)
- **"Send me everything"** ← Also works (sends all GitHub events)

#### 4. Active
✅ Make sure the checkbox is **checked** to enable the webhook.

### Save Webhook

Click the green **"Add webhook"** button at the bottom.

---

## ✅ Step 3: Verify Webhook is Active

### Check Recent Deliveries

After clicking "Add webhook", GitHub will immediately try to send a test event.

1. You'll be on the webhook detail page
2. Scroll down to **"Recent Deliveries"**
3. You should see an entry with:
   - 🔵 A delivery ID
   - Status: **200**, **201**, or **202** (success)
   - Timestamp: "just now"

### If Status is 200/202 ✅

Perfect! Your webhook is set up correctly. AgentBeats received the test and confirmed.

### If Status is 400 or 500 ❌

Check these:
- [ ] Payload URL is correct (copy-paste from AgentBeats)
- [ ] Content-Type is set to `application/json`
- [ ] The webhook is on the **leaderboard repo**, not your code repo
- [ ] Your agent's leaderboard repository URL is correct in AgentBeats

---

## 🧪 Step 4: Test with a Sample Push

Now let's verify everything works by pushing a test result.

### Push a Test Result

```bash
# Navigate to your leaderboard repository
cd /path/to/gaia-benchmark-leaderboard

# Copy a sample result
cp /Users/harshada/Project/gaia-agentbeats/results/gaia-result-*.json results/

# Commit and push
git add results/
git commit -m "Test webhook submission"
git push origin main
```

### Check Webhook Delivery

1. Go back to your webhook settings:
   ```
   https://github.com/harshada-javeri/gaia-benchmark-leaderboard/settings/webhooks
   ```

2. Click on your webhook

3. Scroll to **"Recent Deliveries"**

4. You should see a **new entry** from your push with:
   - Status: **200** or **202** ✅
   - Time: Just now
   - Response shows success

### Verify on AgentBeats

1. Visit: https://agentbeats.dev/harshada-javeri/g-agent
2. Go to **"Leaderboard"** tab
3. Wait **30 seconds** (webhook processing)
4. Your result should appear! 🎉

---

## 🔍 Webhook Troubleshooting

### Problem: Status 400 Bad Request

**Cause:** Payload format doesn't match AgentBeats expectations

**Solution:**
- Verify results JSON structure is correct
- Check webhook response body in GitHub logs (click the delivery)
- Ensure your result file has correct JSON format

### Problem: Status 403 Forbidden

**Cause:** AgentBeats can't authenticate

**Solution:**
- Verify webhook URL is exactly as copied from AgentBeats
- Check that your agent is still registered

### Problem: Status 404 Not Found

**Cause:** Wrong leaderboard repository URL in AgentBeats

**Solution:**
- Go to agent edit page on AgentBeats
- Verify "Leaderboard Repository" URL is correct
- Make sure the repo is public

### Problem: No Recent Deliveries Shown

**Cause:** Webhook wasn't triggered or network issue

**Solution:**
- Verify webhook is set to trigger on "Push events"
- Make sure webhook is "Active" (checkbox checked)
- Try pushing a commit again
- Check GitHub Actions → Workflows for any errors

---

## 📋 Complete Webhook Setup Checklist

- [ ] **Copy webhook URL** from AgentBeats agent page
- [ ] **Go to GitHub** leaderboard repo settings
- [ ] **Add new webhook** with:
  - [ ] Correct payload URL (from AgentBeats)
  - [ ] Content-Type: `application/json`
  - [ ] Events: "Push events"
  - [ ] Active: ✅ checked
- [ ] **Verify** first test delivery shows 200/202
- [ ] **Push test result** to leaderboard repo
- [ ] **Confirm** webhook delivery succeeded (200/202)
- [ ] **Check leaderboard** after 30 seconds
- [ ] **See result** on AgentBeats! 🎉

---

## 🔗 Quick Links

| Item | Link |
|------|------|
| Your Agent | https://agentbeats.dev/harshada-javeri/g-agent |
| Edit Agent | https://agentbeats.dev/harshada-javeri/g-agent/edit |
| Leaderboard Repo | https://github.com/harshada-javeri/gaia-benchmark-leaderboard |
| Webhook Settings | https://github.com/harshada-javeri/gaia-benchmark-leaderboard/settings/webhooks |
| Tutorial | https://docs.agentbeats.dev/tutorial |

---

## 📊 What Happens After Webhook Setup

```
You push results to leaderboard repo
         ↓
GitHub sends webhook event to AgentBeats
         ↓
AgentBeats receives and processes event (5-30 seconds)
         ↓
Results appear on your leaderboard page
         ↓
Visitors see your agent's scores
```

Your leaderboard is now **live and updating automatically!** 🚀
