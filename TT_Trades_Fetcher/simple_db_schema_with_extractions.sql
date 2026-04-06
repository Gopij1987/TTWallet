-- ============================================================================
-- TRADETRON DATABASE SCHEMA - WITH EXTRACTIONS TABLE
-- Shared Code ID: 23894081
-- ============================================================================

-- TABLE 1: SHARED_CODES
CREATE TABLE IF NOT EXISTS shared_codes (
    shared_code_id BIGINT PRIMARY KEY,
    code_name VARCHAR(255) NOT NULL,
    code_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- TABLE 2: INSTRUMENTS
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id BIGSERIAL PRIMARY KEY,
    shared_code_id BIGINT NOT NULL REFERENCES shared_codes(shared_code_id),
    instrument_full VARCHAR(100) NOT NULL UNIQUE,
    inst_type VARCHAR(20),
    underlying VARCHAR(50),
    expiry VARCHAR(20),
    option_type VARCHAR(5),
    strike VARCHAR(20),
    exchange VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_shared_code(shared_code_id),
    INDEX idx_underlying(underlying),
    INDEX idx_expiry(expiry),
    INDEX idx_option_type(option_type)
);

-- TABLE 3: EXTRACTIONS (Simple consolidated table for now)
-- Stores all extracted data with shared_code_id and strategy_id tracking
CREATE TABLE IF NOT EXISTS extractions (
    extraction_id BIGSERIAL PRIMARY KEY,
    
    -- Metadata about extraction
    shared_code_id BIGINT NOT NULL REFERENCES shared_codes(shared_code_id),
    strategy_id BIGINT NOT NULL,    -- Which strategy was extracted (can change in future)
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- All extracted trade data columns (from CSV)
    counter INT NOT NULL,
    trade_date DATE NOT NULL,
    trade_time TIME,
    instrument_full VARCHAR(100) NOT NULL,
    inst_type VARCHAR(20),
    underlying VARCHAR(50),
    expiry VARCHAR(20),
    option_type VARCHAR(5),
    strike VARCHAR(20),
    qty NUMERIC(15,4),
    price NUMERIC(15,6),
    amount NUMERIC(15,2),
    note TEXT,
    
    -- Indexes for performance
    INDEX idx_shared_code(shared_code_id),
    INDEX idx_strategy(strategy_id),
    INDEX idx_counter(strategy_id, counter),
    INDEX idx_trade_date(trade_date DESC),
    INDEX idx_underlying(underlying),
    INDEX idx_expiry(expiry),
    UNIQUE INDEX idx_unique_extraction(shared_code_id, strategy_id, counter, trade_date, trade_time, instrument_full, qty, price)
);

-- ============================================================================
-- DATA RELATIONSHIP
-- ============================================================================
/*
shared_codes (23894081)
    ├─→ instruments (15 instruments)
    └─→ extractions (all extracted trades)
        └─ Tracks: shared_code_id + strategy_id + all trade columns
*/

-- ============================================================================
-- INSERT FOUNDATION DATA
-- ============================================================================

-- Insert Shared Code
INSERT INTO shared_codes (shared_code_id, code_name, code_version, description)
VALUES (23894081, 'Directional Option Selling BNF With Hedge V4', '1.0', 'Main shared strategy code')
ON CONFLICT (shared_code_id) DO NOTHING;

-- Insert Sample Instruments
INSERT INTO instruments (shared_code_id, instrument_full, inst_type, underlying, expiry, option_type, strike, exchange)
VALUES
(23894081, 'OPTIDX_SENSEX_12MAR2026_CE_79500', 'OPTIDX', 'SENSEX', '12MAR2026', 'CE', '79500', 'BFO'),
(23894081, 'OPTIDX_SENSEX_12MAR2026_PE_78500', 'OPTIDX', 'SENSEX', '12MAR2026', 'PE', '78500', 'BFO'),
(23894081, 'OPTIDX_SENSEX_04DEC2025_CE_85700', 'OPTIDX', 'SENSEX', '04DEC2025', 'CE', '85700', 'BFO'),
(23894081, 'OPTIDX_SENSEX_24DEC2025_CE_85300', 'OPTIDX', 'SENSEX', '24DEC2025', 'CE', '85300', 'BFO'),
(23894081, 'OPTIDX_SENSEX_18DEC2025_CE_85100', 'OPTIDX', 'SENSEX', '18DEC2025', 'CE', '85100', 'BFO'),
(23894081, 'OPTIDX_SENSEX_13NOV2025_CE_84200', 'OPTIDX', 'SENSEX', '13NOV2025', 'CE', '84200', 'BFO'),
(23894081, 'OPTIDX_SENSEX_08JAN2026_CE_85200', 'OPTIDX', 'SENSEX', '08JAN2026', 'CE', '85200', 'BFO'),
(23894081, 'OPTIDX_NIFTY_23DEC2025_CE_25750', 'OPTIDX', 'NIFTY 50', '23DEC2025', 'CE', '25750', 'NFO'),
(23894081, 'OPTIDX_NIFTY_23DEC2025_PE_25250', 'OPTIDX', 'NIFTY 50', '23DEC2025', 'PE', '25250', 'NFO'),
(23894081, 'OPTIDX_NIFTY_24FEB2026_PE_25300', 'OPTIDX', 'NIFTY 50', '24FEB2026', 'PE', '25300', 'NFO'),
(23894081, 'OPTIDX_NIFTY_30DEC2025_CE_25900', 'OPTIDX', 'NIFTY 50', '30DEC2025', 'CE', '25900', 'NFO'),
(23894081, 'OPTIDX_NIFTY_30DEC2025_PE_25900', 'OPTIDX', 'NIFTY 50', '30DEC2025', 'PE', '25900', 'NFO'),
(23894081, 'OPTIDX_NIFTY_02DEC2025_PE_26100', 'OPTIDX', 'NIFTY 50', '02DEC2025', 'PE', '26100', 'NFO'),
(23894081, 'OPTIDX_NIFTY_10MAR2026_CE_24550', 'OPTIDX', 'NIFTY 50', '10MAR2026', 'CE', '24550', 'NFO')
ON CONFLICT (instrument_full) DO NOTHING;

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Show extractions for a strategy
-- SELECT * FROM extractions WHERE strategy_id = 25871841 LIMIT 10;

-- Count trades by strategy
-- SELECT strategy_id, COUNT(*) as trades FROM extractions WHERE shared_code_id = 23894081 GROUP BY strategy_id;

-- Count trades by counter
-- SELECT counter, COUNT(*) FROM extractions WHERE shared_code_id = 23894081 AND strategy_id = 25871841 GROUP BY counter;

-- P&L by counter
-- SELECT counter, SUM(amount) as counter_pnl FROM extractions WHERE shared_code_id = 23894081 AND strategy_id = 25871841 GROUP BY counter;
