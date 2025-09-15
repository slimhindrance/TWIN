# 🎯 Notion Integration Setup Guide

## Quick Start (5 minutes)

Your Digital Twin can now access your Notion workspace! Here's how to connect it:

### Step 1: Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill out:
   - **Name**: "Digital Twin" (or whatever you prefer)
   - **Associated workspace**: Select your workspace
   - **Type**: Internal integration
4. Click **"Submit"**
5. Copy your **Internal Integration Token** (starts with `secret_...`)

### Step 2: Share Pages with Your Integration

**Important**: Your integration can only access pages that are explicitly shared with it.

1. Go to any Notion page you want your Digital Twin to access
2. Click **"Share"** in the top right
3. Click **"Invite"** 
4. Search for your integration name (e.g., "Digital Twin")
5. Select it and click **"Invite"**
6. Repeat for other pages/databases you want to include

### Step 3: Connect in Digital Twin

1. Open your Digital Twin application
2. Click **Settings** → **Knowledge Sources**
3. Find **Notion** in the "Available Sources" section
4. Click **"Connect"**
5. Paste your Integration Token
6. Click **"Connect"**

### Step 4: Test & Sync

1. Once connected, click **"Sync All"** to import your Notion pages
2. Start chatting! Ask about content from your Notion workspace

## 🎉 You're Done!

Your Digital Twin can now:
- Search through your Notion pages
- Answer questions about your Notion content
- Combine insights from both Obsidian and Notion
- Show source citations from your Notion pages

## 💡 Pro Tips

### What Gets Imported
- ✅ All pages shared with your integration
- ✅ Page content (text, headings, lists, code blocks)
- ✅ Page titles and properties
- ✅ Tags from multi-select and select properties
- ✅ Database entries (if database is shared)

### What Doesn't Get Imported (Yet)
- ❌ Images and files
- ❌ Comments
- ❌ Page templates
- ❌ Private pages not shared with integration

### Best Practices
1. **Share strategically**: Only share pages you want in your Digital Twin
2. **Use descriptive titles**: Better titles = better search results
3. **Tag consistently**: Tags help organize and find content
4. **Sync regularly**: Click "Sync All" to update with latest changes

## 🔧 Troubleshooting

### "Failed to connect to Notion"
- Check your API token is correct (starts with `secret_`)
- Make sure you copied the full token
- Verify your integration is still active in Notion

### "No documents found"
- Make sure you've shared at least one page with your integration
- Check that shared pages contain text content
- Try sharing a simple page first to test

### "Permission denied"
- Your integration token may have expired
- Regenerate a new token in Notion Integrations
- Re-connect with the new token

## 🚀 What's Next?

With Notion connected, your Digital Twin becomes even more powerful:

- **Cross-platform insights**: "What did I write in Notion about this Obsidian topic?"
- **Unified search**: Find information across all your knowledge sources
- **Conversation continuity**: Switch between apps while maintaining context
- **Knowledge connections**: Discover relationships between your notes

## 💰 Costs

**Completely FREE!** 
- Notion API is free (10K requests/hour)
- You provide your own API token
- No additional costs to you or us

---

**Need help?** Open an issue on GitHub or check our documentation for more advanced configurations.
