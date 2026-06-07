# 🚀 HOW TO RUN - TT Dashboard

## Quick Start (5 Steps)

### **Step 1: Open Terminal**

Navigate to the TT Dashboard folder:
```
C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\TT dashboard
```

**Using PowerShell (Recommended for Windows):**
- Right-click folder → "Open in Terminal" (or "Open with PowerShell")
- OR: Open PowerShell and run:
  ```powershell
  cd "C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\TT dashboard"
  ```

**Using Command Prompt:**
- Right-click folder → "Open Command Prompt here"
- OR: Open CMD and run:
  ```cmd
  cd "C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\TT dashboard"
  ```

---

### **Step 2: Check Setup Status**

**PowerShell:**
```powershell
.\setup.ps1
```

**Command Prompt:**
```cmd
setup.bat
```

**Output will show:**
```
✅ Node.js 16.x.x installed
✅ npm 8.x.x found
✅ backend/server.js found
✅ backend/routes/ directory found
❌ backend/.env not found
⚠️  backend/node_modules not found
...
Checks passed: 5/8 (62%)
```

If you see red/yellow items, continue to **Step 3**.

---

### **Step 3: Install Dependencies (if needed)**

**If setup shows missing dependencies:**

**Option A - PowerShell (Easiest):**
```powershell
npm run install:all
```

**Option B - Manual:**
```powershell
cd backend
npm install
cd ../frontend
npm install
cd ..
```

**This will:**
- Download and install all npm packages
- Takes 2-5 minutes
- Shows progress with checkmarks

---

### **Step 4: Configure Backend**

**Copy `.env` template:**
```powershell
cd backend
Copy-Item .env.example .env
```

**Edit `.env` file:**
- Open `backend/.env` in notepad/VS Code
- Fill in these values:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alphametrix
DB_USER=postgres
DB_PASSWORD=mcxdatabase

TT_COOKIES_B64_GOPI=<paste_your_cookies_here>
TT_COOKIES_B64_RAMKI=<paste_your_cookies_here>
TT_COOKIES_B64_CAPITAL=<paste_your_cookies_here>

PORT=5000
```

**Where to get cookies:**
- See `dual_wallet_monitor.py` in parent folder for instructions
- Or check `.env` in `TTGopiWallet/` or `TTRamkiWallet/` folders

---

### **Step 5: Start the Dashboard**

**From TT dashboard folder, run:**

**PowerShell (Opens new terminal windows):**
```powershell
.\start-all.ps1
```

**Command Prompt (Opens new terminal windows):**
```cmd
start-all.bat
```

**OR Manual (Same terminal, shows logs):**
```powershell
npm run start
# Or: node start-all.js
```

---

## ✅ Success!

After running startup script, you'll see:

**Backend Terminal:**
```
╔════════════════════════════════════════════════════════╗
║      🚀 TT Dashboard API Server Started                ║
╠════════════════════════════════════════════════════════╣
║  Environment: development
║  Port: 5000
║  Database: alphametrix
╚════════════════════════════════════════════════════════╝
```

**Frontend Terminal:**
```
  ➜  Local:   http://localhost:3000/
  ➜  Press q to quit
```

**Then:**
1. Open browser to: **http://localhost:3000**
2. Dashboard should load
3. Click **"Refresh Now"** button to pull data from Tradetron
4. Watch the data populate! 📊

---

## 📋 Alternative Methods

### **Method 1: Individual Terminals (Manual)**

**Terminal 1 - Backend:**
```powershell
cd backend
npm run dev
# Shows: 🚀 TT Dashboard API Server Started on port 5000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
# Shows: ➜ Local: http://localhost:3000/
```

### **Method 2: Using Node.js Directly**

```powershell
cd "C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\TT dashboard"
node start-all.js
```

### **Method 3: From Parent Folder**

```powershell
cd "C:\Users\gopij\OneDrive\Synced\Python\TT Wallet"
cd "TT dashboard"
npm run start
```

---

## 🛑 Stopping the Dashboard

**If terminals opened separately:**
- Close each terminal window individually
- OR press `Ctrl+C` in each terminal

**If running in same terminal:**
- Press `Ctrl+C` once (graceful shutdown)
- Wait 1-2 seconds for cleanup
- Type `exit` if needed

---

## 🔄 After First Run

### **Next time you want to use it:**

1. Open terminal in `TT dashboard` folder
2. Run: `npm run start` (or `.\start-all.ps1`)
3. Wait for "servers started" messages
4. Open http://localhost:3000
5. Click "Refresh Now" if no data shows

### **If changes were made:**
```powershell
# Backend changes auto-reload (no restart needed)
# Frontend changes auto-reload (no restart needed)
# Just refresh browser (F5)
```

---

## ⚠️ Troubleshooting

### **"Cannot find module"**
```
→ Run: npm run install:all
```

### **"Port 5000 already in use"**
```
→ Change PORT in backend/.env
→ OR kill process: netstat -ano | findstr :5000
```

### **"Port 3000 already in use"**
```
→ Edit frontend/vite.config.js change port
→ OR kill process: netstat -ano | findstr :3000
```

### **"Cannot connect to database"**
```
→ Check DB_HOST, DB_PORT, DB_PASSWORD in .env
→ Verify PostgreSQL is running
→ Run setup.ps1 to diagnose
```

### **"401 from Tradetron API"**
```
→ Cookies expired
→ Get new cookies from browser session
→ Update TT_COOKIES_B64_* in .env
```

### **"No data on dashboard"**
```
→ Click "Refresh Now" button
→ Check backend logs for errors
→ Wait 2-5 minutes for data sync
```

---

## 📚 Command Reference

### **From Project Root (`TT dashboard` folder):**

```bash
# Check status
node setup.js                      # Universal
.\setup.ps1                        # PowerShell
setup.bat                          # Command Prompt

# Install dependencies
npm run install:all                # Both backend & frontend
npm run backend:install            # Backend only
npm run frontend:install           # Frontend only

# Start servers
npm run start                       # Start both (recommended)
.\start-all.ps1                    # PowerShell version
start-all.bat                      # Command Prompt version
node start-all.js                  # Node.js version

# Individual servers
npm run backend:dev                # Backend only
npm run frontend:dev               # Frontend only
```

---

## 🎯 Complete Workflow

```
1. Open PowerShell in TT dashboard folder
   └─ cd "C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\TT dashboard"

2. Check setup
   └─ .\setup.ps1

3. Install if needed
   └─ npm run install:all

4. Configure backend/.env
   └─ Copy .env.example → .env
   └─ Fill in credentials

5. Start servers
   └─ npm run start
   
6. Open browser
   └─ http://localhost:3000

7. Click "Refresh Now"
   └─ Wait for data to sync

8. Explore dashboard! 📊
```

---

## 🎉 You're Done!

Once you see both servers running and the dashboard loads:

✅ Backend API at: http://localhost:5000  
✅ Frontend Dashboard at: http://localhost:3000  
✅ Click "Refresh Now" to sync strategies  
✅ View PnL trends, heatmaps, strategy performance  

Enjoy! 🚀📈
