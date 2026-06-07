# SETUP & STARTUP GUIDE

## 📋 Quick Commands

### **1. Check Setup Status (Recommended First)**

Choose one based on your OS:

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Windows (Command Prompt):**
```cmd
setup.bat
```

**macOS/Linux:**
```bash
node setup.js
```

This script will:
- ✅ Check Node.js & npm versions
- ✅ Verify project folder structure
- ✅ Check if `.env` is configured
- ✅ Verify dependencies installed
- ✅ Test PostgreSQL connection
- 📊 Show overall setup status percentage

---

## 🔧 Installation Steps

### **Step 1: Check Status**
```bash
node setup.js
# OR
.\setup.ps1
# OR
setup.bat
```

### **Step 2: Install Dependencies (if needed)**

**Option A - Individual:**
```bash
cd backend && npm install
cd ../frontend && npm install
```

**Option B - From project root:**
```bash
npm run install:all
```

### **Step 3: Configure Backend**

Copy template and fill in credentials:
```bash
cp backend/.env.example backend/.env
```

**Edit `backend/.env` and fill in:**
```
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alphametrix
DB_USER=postgres
DB_PASSWORD=your_password

# Tradetron Cookies (from dual_wallet_monitor.py)
TT_COOKIES_B64_GOPI=<paste_here>
TT_COOKIES_B64_RAMKI=<paste_here>
TT_COOKIES_B64_CAPITAL=<paste_here>

# Server
PORT=5000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000
```

### **Step 4: Verify Setup Again**
```bash
node setup.js
# Should show ~100% completion
```

---

## 🚀 Starting Servers

### **Option 1: Start Both (Recommended)**

**Windows (PowerShell):**
```powershell
.\start-all.ps1
```

**Windows (Command Prompt):**
```cmd
start-all.bat
```

**macOS/Linux:**
```bash
node start-all.js
```

This will:
- 🔵 Open backend terminal (port 5000)
- 🟢 Open frontend terminal (port 3000)
- 🌐 Ready for browser access

### **Option 2: Start Individually**

**Terminal 1 - Backend:**
```bash
npm run backend:dev
# OR
cd backend && npm run dev
```

**Terminal 2 - Frontend:**
```bash
npm run frontend:dev
# OR
cd frontend && npm run dev
```

---

## 🌐 Access Dashboard

Once both servers are running:

**Dashboard UI:**
- URL: http://localhost:3000
- React development server with hot-reload

**API Backend:**
- Base: http://localhost:5000
- Health check: http://localhost:5000/api/health
- Swagger/docs available at: http://localhost:5000/docs (if enabled)

---

## 📊 Testing the Setup

### **1. Backend Health**
```bash
curl http://localhost:5000/api/health
# Expected response: {"status":"ok","timestamp":"..."}
```

### **2. Fetch Strategies**
```bash
curl http://localhost:5000/api/strategies
# Should return JSON array of strategies
```

### **3. Dashboard Summary**
```bash
curl http://localhost:5000/api/dashboard/summary
# Should return aggregated metrics
```

### **4. Manual Refresh**
```bash
curl -X POST http://localhost:5000/api/refresh
# Triggers new_sc_update.py to sync from Tradetron
```

---

## 🛠️ Individual Commands Reference

### **Root-level Scripts**
```bash
npm run setup          # Check setup status
npm run install:all    # Install both backend & frontend
npm run start          # Start both servers
npm run backend:dev    # Start backend only
npm run frontend:dev   # Start frontend only
```

### **Backend-specific**
```bash
cd backend
npm run dev            # Development mode with auto-reload
npm start              # Production mode
npm run refresh        # Trigger data sync
```

### **Frontend-specific**
```bash
cd frontend
npm run dev            # Vite development server
npm run build          # Production build
npm run preview        # Preview production build locally
```

---

## ⚠️ Troubleshooting

### **Setup Check Issues**

| Problem | Solution |
|---------|----------|
| "Node.js not found" | Install from https://nodejs.org/ |
| "npm not found" | Reinstall Node.js (includes npm) |
| ".env not found" | Run: `cp backend/.env.example backend/.env` |
| "node_modules not found" | Run: `npm run install:all` |
| "PostgreSQL connection failed" | Start PostgreSQL; verify credentials in .env |

### **Runtime Issues**

| Problem | Solution |
|---------|----------|
| "Cannot GET /api/strategies" | Backend not running; check `npm run backend:dev` |
| "CORS error" in browser | Check `CORS_ORIGIN` in `.env` |
| "401 from Tradetron" | Cookies expired; update in `.env` |
| "No data on dashboard" | Click "Refresh Now" to sync from Tradetron |
| "Port 5000 already in use" | Change `PORT` in `.env` or kill process using that port |
| "Port 3000 already in use" | Edit `frontend/vite.config.js` and change port |

---

## 📝 Environment Checklist

Before running:

- [ ] Node.js 14+ installed (`node -v`)
- [ ] npm installed (`npm -v`)
- [ ] PostgreSQL running and `alphametrix` database exists
- [ ] `backend/.env` created and filled with credentials
- [ ] `backend/node_modules` directory exists
- [ ] `frontend/node_modules` directory exists
- [ ] Tradetron cookies exported to `.env`

---

## 🎯 Development Workflow

### **1. First Time Setup**
```bash
node setup.js                    # Check status
npm run install:all              # Install deps
# Edit backend/.env
node setup.js                    # Verify
npm run start                    # Start servers
```

### **2. Daily Development**
```bash
npm run start                    # Start both servers
# Open http://localhost:3000
# Code changes auto-reload
# Press Ctrl+C to stop
```

### **3. After Dependency Changes**
```bash
npm run backend:install          # Update backend only
npm run frontend:install         # Update frontend only
npm run install:all              # Update both
npm run start                    # Restart servers
```

---

## 🔄 Refresh Data from Tradetron

### **Via Dashboard**
1. Open http://localhost:3000
2. Click **"🔄 Refresh Now"** button
3. Wait for completion (check backend logs)
4. Dashboard auto-updates

### **Via API**
```bash
curl -X POST http://localhost:5000/api/refresh
# Response: {"status":"refresh_started",...}
```

### **Via Terminal**
```bash
cd backend && npm run refresh
# Executes new_sc_update.py directly
```

---

## 📦 Project Structure

```
TT dashboard/
├── setup.js              ← Status check script
├── setup.bat             ← Windows batch version
├── setup.ps1             ← Windows PowerShell version
├── start-all.js          ← Startup script
├── start-all.bat         ← Windows batch version
├── start-all.ps1         ← Windows PowerShell version
├── package.json          ← Root scripts
├── README.md             ← Full documentation
├── QUICKSTART.md         ← Quick start (5 min)
├── SETUP.md              ← This file
│
├── backend/
│   ├── server.js
│   ├── db.js
│   ├── routes/
│   ├── .env              ← FILL THIS IN!
│   └── package.json
│
└── frontend/
    ├── src/
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## ✅ Verification

After setup, verify with:

```bash
# 1. Check status
node setup.js

# 2. Test API
curl http://localhost:5000/api/health

# 3. View frontend
open http://localhost:3000
# or
start http://localhost:3000
# or
xdg-open http://localhost:3000
```

---

## 🆘 Need Help?

1. **Check QUICKSTART.md** for basic setup
2. **Review README.md** for full documentation
3. **Run `node setup.js`** to diagnose issues
4. **Check server logs** for error messages
5. **Verify .env configuration** is correct
6. **Ensure PostgreSQL is running** and accessible

---

## 🎉 Success!

Once everything is green in `setup.js`:
- ✅ Backend ready on `http://localhost:5000`
- ✅ Frontend ready on `http://localhost:3000`
- ✅ Database connected
- ✅ Ready to monitor strategies! 📈

Enjoy your TT Dashboard! 🚀
