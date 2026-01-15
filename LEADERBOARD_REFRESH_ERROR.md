# ❌ Leaderboard Refresh Failed - Fix Guide

## 🔍 Problem

AgentBeats shows this error:
```
Failed to fetch from https://github.com/harshada-javeri/gaia-agentbeats (refs/heads/main)
Check that the repository is public.
```

This means AgentBeats is configured with the **wrong repository URL**.

---

## ✅ Solution: Update the Leaderboard URL

### Step 1: Go to Your Agent Page

1. Visit: https://agentbeats.dev/harshada-javeri/g-agent
2. Click **"Edit Agent"** button

### Step 2: Find "Leaderboard Repository"

Scroll down to the section titled **"Leaderboard Repository"**

### Step 3: Check/Update the URL

Currently it shows:
```
https://github.com/harshada-javeri/gaia-agentbeats  ❌ WRONG
```

It should be:
```
https://github.com/harshada-javeri/gaia-benchmark-leaderboard  ✅ CORRECT
```

### Step 4: Make Sure Leaderboard Repo is Public

Before saving, verify:
- [ ] Go to https://github.com/harshada-javeri/gaia-benchmark-leaderboard
- [ ] Click **Settings**
- [ ] Scroll to **"Danger Zone"**
- [ ] Verify visibility is **"Public"** (not Private)

If it's private:
1. Click **"Change visibility"**
2. Select **"Public"**
3. Confirm

### Step 5: Update and Save

Back on AgentBeats:
1. [ ] Clear the old URL field
2. [ ] Paste: `https://github.com/harshada-javeri/gaia-benchmark-leaderboard`
3. [ ] Click **"Save"**

---

## 🔧 Verify Webhook Configuration

After updating the URL, verify your webhook is set up correctly:

1. Go to: https://github.com/harshada-javeri/gaia-benchmark-leaderboard
2. Settings → **Webhooks**
3. Check your AgentBeats webhook:
   - [ ] **Payload URL**: `https://agentbeats.dev/api/hook/v2/<token>`
   - [ ] **Content type**: `application/json`
   - [ ] **Events**: "Push events" or "Send me everything"
   - [ ] **Active**: ✅ Checked
   - [ ] Recent deliveries show **200** or **202** status

---

## 📋 Checklist to Fix

- [ ] **Leaderboard repo URL** is correct in AgentBeats
- [ ] **Repository is public** on GitHub
- [ ] **Webhook is configured** on leaderboard repo (not code repo)
- [ ] **Webhook status** is active in GitHub
- [ ] Save changes in AgentBeats

---

## 🚀 After Fixing

Once you've made these changes:

1. **Push a test result** to your leaderboard repo:
   ```bash
   cd /path/to/gaia-benchmark-leaderboard
   cp /Users/harshada/Project/gaia-agentbeats/results/gaia-result-*.json results/
   git add results/
   git commit -m "Test result"
   git push origin main
   ```

2. **Wait 30 seconds** for webhook to process

3. **Check your leaderboard**: https://agentbeats.dev/harshada-javeri/g-agent/leaderboard

4. **Verify in GitHub** webhook logs that delivery was successful (200/202)

---

## 🆘 Still Not Working?

If you still see errors:

1. **Verify repository exists and is public**
   ```bash
   curl -I https://github.com/harshada-javeri/gaia-benchmark-leaderboard
   # Should return 200, not 404
   ```

2. **Check webhook deliveries**
   - GitHub repo → Settings → Webhooks → Recent Deliveries
   - Look for 400+ errors and read response body

3. **Review webhook payload format**
   - Results JSON must have proper structure
   - Check examples in `/Users/harshada/Project/gaia-agentbeats/results/`

4. **Ask for help**
   - Screenshot the AgentBeats error
   - Screenshot the GitHub webhook logs
   - Share your leaderboard repo name/URL

---

## 🔗 Key URLs

- **Agent Page**: https://agentbeats.dev/harshada-javeri/g-agent
- **Edit Agent**: https://agentbeats.dev/harshada-javeri/g-agent/edit
- **Leaderboard Repo**: https://github.com/harshada-javeri/gaia-benchmark-leaderboard
- **Leaderboard Settings**: https://github.com/harshada-javeri/gaia-benchmark-leaderboard/settings/webhooks
