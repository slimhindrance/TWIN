# 🚀 **QUICK START - Digital Twin Launch**

## ⚡ **5-Minute Setup**

### **1. Get Your Servers Running**

#### **Backend Server**
```powershell
# In PowerShell (as Administrator if needed)
cd "C:\Users\641792\OneDrive - BOOZ ALLEN HAMILTON\Desktop\Projects\TWIN\backend"
poetry run uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
```

#### **Frontend Server** (New PowerShell Window)
```powershell
cd "C:\Users\641792\OneDrive - BOOZ ALLEN HAMILTON\Desktop\Projects\TWIN\frontend"
npm start
```

### **2. Open Your Digital Twin**
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

### **3. Connect Your Knowledge Sources**
1. **Click Settings** (⚙️ icon)
2. **Go to "Knowledge Sources" tab**
3. **Connect Notion**: 
   - Get token from: https://www.notion.so/my-integrations
   - Create new integration, copy "Internal Integration Token"
   - Paste into Digital Twin
4. **Connect Obsidian**: 
   - Browse to your vault folder
   - Watch it auto-sync your notes

### **4. Start Conversations**
- Ask: *"What projects have I been working on?"*
- Ask: *"Summarize my notes from last month"*
- Ask: *"What are my main areas of expertise?"*

---

## 🎯 **Ready to Launch?**

### **Option 1: Personal Use (Ready Now)**
- ✅ Use it daily for 1-2 weeks
- ✅ Refine based on your needs
- ✅ Share with close friends/colleagues

### **Option 2: Beta Launch (This Week)**
- Create simple landing page
- Share in Obsidian/Notion communities
- Collect 10-20 beta users for feedback

### **Option 3: Full Product Launch (Next Week)**  
- Build proper landing page
- Launch on Product Hunt
- Start building user base

---

## 🐛 **Troubleshooting**

### **Backend Won't Start**
```powershell
# Try from correct directory
cd backend
poetry install
poetry run python -c "from app.core.config import settings; print('Config OK')"
poetry run uvicorn app.main:app --port 8000
```

### **Frontend Won't Start** 
```powershell
# Try rebuilding
cd frontend
npm install
npm start
```

### **Can't Connect to Notion**
1. Go to https://www.notion.so/my-integrations
2. Create "New integration"  
3. Copy "Internal Integration Token"
4. In Notion, share your pages with the integration
5. Paste token into Digital Twin settings

---

## 📞 **You're Ready!**

**Your digital twin is working perfectly. All the complex technical work is done.**

**Time to decide: Personal tool or business opportunity?**

Either way, you've built something remarkable! 🎉
