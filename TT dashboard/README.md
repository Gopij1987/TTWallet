# TT Dashboard - Tradetron PnL Monitor

A modern React + Node.js dashboard for monitoring PnL across multiple Tradetron wallets (Gopi, Ramki, Capital).

## Features

✅ **Multi-Wallet Support** - Monitor Gopi, Ramki, and Capital wallets simultaneously  
✅ **Strategy Performance** - View PnL by counter (round) for each strategy  
✅ **Interactive Charts** - Line chart showing PnL trends over time  
✅ **Heatmap View** - Visualize performance across dates and execution types  
✅ **Real-time Refresh** - One-click button to sync latest data from Tradetron API  
✅ **Advanced Filtering** - Filter by wallet, status, date range, execution type  
✅ **Trade Drill-Down** - Click any strategy to see all individual trades/legs  

## Architecture

```
TT Dashboard/
├── backend/                 # Express.js API server
│   ├── server.js           # Main server entry
│   ├── db.js               # PostgreSQL connection pool
│   ├── routes/             # API endpoints
│   │   ├── health.js       # Health check
│   │   ├── strategies.js   # Strategy list & detail
│   │   ├── dashboard.js    # Summary & charts
│   │   └── refresh.js      # Tradetron sync trigger
│   ├── package.json
│   └── .env.example
│
├── frontend/               # React dashboard UI
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── SummaryCards.jsx
│   │   │   ├── StrategyTable.jsx
│   │   │   ├── PnlChart.jsx
│   │   │   ├── Heatmap.jsx
│   │   │   └── FilterSidebar.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api.js          # Axios API client
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
│
└── docs/                   # Documentation
```

## Setup Instructions

### Prerequisites
- Node.js 16+ and npm
- PostgreSQL with alphametrix database
- Python 3.8+ (for refresh script)
- Tradetron API cookies

### Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env` file from template:**
   ```bash
   cp .env.example .env
   ```

4. **Fill in your configuration in `.env`:**
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=alphametrix
   DB_USER=postgres
   DB_PASSWORD=your_password
   
   TT_COOKIES_B64_GOPI=<base64_encoded_cookies>
   TT_COOKIES_B64_RAMKI=<base64_encoded_cookies>
   TT_COOKIES_B64_CAPITAL=<base64_encoded_cookies>
   
   PORT=5000
   NODE_ENV=development
   CORS_ORIGIN=http://localhost:3000
   ```

5. **Start the server:**
   ```bash
   npm run dev
   ```
   
   Server will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   
   Dashboard will be available at `http://localhost:3000`

### Running Both Simultaneously

From project root in 2 separate terminals:

**Terminal 1 - Backend:**
```bash
cd backend && npm run dev
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

## API Endpoints

### Health & Status
- `GET /api/health` - Server health check

### Strategies
- `GET /api/strategies` - List strategies with filters
  - Query params: `wallet`, `status`, `execution_type`, `date_from`, `date_to`
- `GET /api/strategies/:id` - Strategy detail with counter breakdown
- `GET /api/strategies/:id/trades` - All trades for strategy

### Dashboard
- `GET /api/dashboard/summary` - Aggregate metrics (total PnL, win rate, active count)
- `GET /api/dashboard/pnl-chart-data` - Time-series PnL data
  - Query params: `strategy_id` (optional), `group_by` (date|counter)
- `GET /api/dashboard/heatmap-data` - Heatmap matrix data

### Refresh
- `POST /api/refresh` - Trigger new_sc_update.py to sync Tradetron data

## Data Model

### Strategies
- Metadata from `shared_codes` table (strategy_id, name, status, PnL, broker)
- Counter-wise aggregation from `ttdata` table (per-trade ledger)

### Trades (Legs)
- Individual transactions stored in `ttdata`
- Columns: counter, date, time, instrument, qty, price, amount, etc.
- Aggregated by counter to show "Round 1", "Round 2", etc.

## Key Features

### Summary Cards
- **Total PnL**: Sum of all strategy PnLs (color: green for +, red for -)
- **Win Rate**: % of strategies with positive PnL
- **Active Strategies**: Count of active strategies
- **Total Strategies**: All strategies in database

### Strategy Table
- Sortable columns (ID, Name, Wallet, Status, PnL, Counter Count)
- Expandable rows showing recent counter-wise PnL
- Click row to expand/collapse
- "Refresh Now" button triggers live sync

### PnL Chart
- Toggle between "By Date" and "By Counter" grouping
- Shows both daily PnL and cumulative PnL
- Interactive tooltip on hover

### Heatmap
- X-axis: Execution types (Active, Completed, Stopped, etc.)
- Y-axis: Recent 10 dates
- Cell color intensity: PnL magnitude
- Dark green = large profit, dark red = large loss

### Filter Sidebar
- **Wallet**: Select Gopi, Ramki, or Capital
- **Status**: Filter by Active, Completed, Stopped
- **Date Range**: From/To date pickers
- **Reset**: Clear all filters at once

## Refreshing Data from Tradetron

Click **"Refresh Now"** button in the dashboard to:
1. Fetch latest strategy metadata from Tradetron API
2. Extract legs/trades for new strategies
3. Update `shared_codes` and `ttdata` tables
4. Refresh materialized views

The process typically takes 2-5 minutes depending on data volume.

## Troubleshooting

### API connection failed
- Check backend is running: `curl http://localhost:5000/api/health`
- Verify CORS_ORIGIN in backend `.env` includes frontend URL

### No strategies showing
- Verify PostgreSQL connection in backend `.env`
- Check `shared_codes` table has records: `SELECT COUNT(*) FROM shared_codes;`
- Run refresh to populate data

### Cookies expired / API returns 401
- Refresh your Tradetron browser session
- Re-export cookies and update TT_COOKIES_B64_* in `.env`
- Click "Refresh Now" button to re-sync

### Database connection refused
- Verify PostgreSQL is running
- Check host, port, credentials in `.env`
- Test connection: `psql -h localhost -U postgres -d alphametrix`

## Performance Optimization

- Pre-aggregated `strategy_counter_pnl` table for faster chart queries
- Materialized views for dashboard summary metrics
- Connection pooling (max 20 connections)
- Indexed queries on strategy_id, date, counter

## Future Enhancements

- [ ] WebSocket for real-time updates
- [ ] Position Greeks visualization (delta, theta, gamma)
- [ ] Automated alerts/notifications
- [ ] Portfolio optimization suggestions
- [ ] Trade analysis heatmaps
- [ ] Export reports (PDF, Excel)
- [ ] Mobile-responsive design

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

MIT
