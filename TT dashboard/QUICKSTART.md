# TT Dashboard - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Update Backend Environment

Navigate to backend folder and create `.env`:

```bash
cd backend
cp .env.example .env
# Edit .env with your PostgreSQL credentials and Tradetron cookies
```

### Step 2: Install Backend Dependencies

```bash
npm install
```

### Step 3: Update Frontend Environment (if needed)

```bash
cd ../frontend
# .env is optional, uses http://localhost:5000 by default
```

### Step 4: Install Frontend Dependencies

```bash
npm install
```

### Step 5: Run Both Servers

**Terminal 1 - Backend (from `TT dashboard/backend`):**
```bash
npm run dev
# Should see:
# ╔════════════════════════════════════════════════════════════╗
# ║      🚀 TT Dashboard API Server Started                    ║
# ╚════════════════════════════════════════════════════════════╝
```

**Terminal 2 - Frontend (from `TT dashboard/frontend`):**
```bash
npm run dev
# Should see:
# ➜  Local:   http://localhost:3000/
```

### Step 6: Open Dashboard

Visit: http://localhost:3000

---

## 📋 File Structure

```
TT dashboard/
├── backend/
│   ├── server.js                 ← Main Express app
│   ├── db.js                     ← PostgreSQL connection
│   ├── routes/
│   │   ├── health.js             ← GET /api/health
│   │   ├── strategies.js         ← GET /api/strategies
│   │   ├── dashboard.js          ← GET /api/dashboard/*
│   │   └── refresh.js            ← POST /api/refresh
│   ├── package.json
│   └── .env                      ← Configuration (FILL THIS IN!)
│
├── frontend/
│   ├── src/
│   │   ├── components/           ← React components
│   │   ├── App.jsx               ← Main app
│   │   ├── api.js                ← API calls
│   │   └── index.css             ← Tailwind styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README.md                     ← Full documentation
```

---

## 🔑 Environment Variables (Backend)

**Critical variables to fill in `.env`:**

```
# PostgreSQL (replace with your credentials)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alphametrix
DB_USER=postgres
DB_PASSWORD=mcxdatabase

# Tradetron Cookies (get from dual_wallet_monitor.py)
TT_COOKIES_B64_GOPI=<paste_here>
TT_COOKIES_B64_RAMKI=<paste_here>
TT_COOKIES_B64_CAPITAL=<paste_here>

# Server
PORT=5000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000
```

### How to get Tradetron Cookies?

See `dual_wallet_monitor.py` in parent directory:
1. Manually get cookies from Tradetron browser session
2. Export as pickle and base64-encode
3. Paste into `.env` as `TT_COOKIES_B64_GOPI`, etc.

---

## ✅ Verification Checklist

- [ ] Backend running on http://localhost:5000
- [ ] Frontend running on http://localhost:3000
- [ ] Dashboard loads without errors
- [ ] Summary cards showing data (or "Loading...")
- [ ] Strategy table visible
- [ ] "Refresh Now" button clickable
- [ ] Charts rendering

---

## 🔄 Triggering Data Refresh

### Via Dashboard
Click **"Refresh Now"** button in top-right → Starts `new_sc_update.py` → Fetches from Tradetron

### Via Terminal
```bash
curl -X POST http://localhost:5000/api/refresh
```

Check backend logs for progress. Data sync takes 2-5 minutes.

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| `Cannot GET /api/strategies` | Backend not running. Check `npm run dev` in backend folder |
| `Error: ECONNREFUSED 5432` | PostgreSQL not running or wrong host/port in `.env` |
| `401 Unauthorized from Tradetron` | Cookie expired. Re-export from dual_wallet_monitor.py |
| Dashboard shows "No data" | Run "Refresh Now" button to sync from Tradetron |
| `CORS error` in browser console | Check `CORS_ORIGIN` in `.env` matches frontend URL |

---

## 📊 Dashboard Sections

1. **Summary Cards** (top)
   - Total PnL, Win Rate, Active Strategies, Strategy Count

2. **PnL Chart** (left)
   - Toggle between Date/Counter grouping
   - Shows daily PnL + cumulative trend

3. **Heatmap** (right)
   - Date × Execution Type matrix
   - Green = profit, Red = loss

4. **Strategy Table** (bottom)
   - All strategies with status
   - Click row to expand counter breakdown

5. **Filter Sidebar** (left)
   - Wallet, Status, Date Range filters
   - Reset button

---

## 🚀 Next Steps

1. **Customize colors/branding** → Edit `frontend/src/index.css` and component colors
2. **Add more charts** → Extend `frontend/src/components/` with new chart types
3. **Configure refresh schedule** → Set `REFRESH_INTERVAL_HOURS` in backend `.env`
4. **Deploy to cloud** → Push to Heroku, Vercel, or your host

---

## 📞 Support

- Check `README.md` for full documentation
- Review component code in `frontend/src/components/`
- Check API endpoints in `backend/routes/`
- View database schema in parent's `simple_db_schema.sql`

Enjoy! 📈
