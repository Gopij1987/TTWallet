-- ============================================================================
-- SIMPLE TRADETRON DATABASE SCHEMA
-- Minimal schema: Shared Code + Instruments  
-- Shared Code ID = 23894081
-- ============================================================================

-- TABLE 1: SHARED_CODES
-- Master reference for strategy shared code versions
CREATE TABLE IF NOT EXISTS shared_codes (
    shared_code_id BIGINT PRIMARY KEY,
    code_name VARCHAR(255) NOT NULL,
    code_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- TABLE 2: INSTRUMENTS  
-- Parsed instrument symbols from trades
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id BIGSERIAL PRIMARY KEY,
    shared_code_id BIGINT NOT NULL REFERENCES shared_codes(shared_code_id),
    instrument_full VARCHAR(100) NOT NULL UNIQUE,
    inst_type VARCHAR(20),        -- OPTIDX, FUTIDX, EQ, etc
    underlying VARCHAR(50),       -- NIFTY, SENSEX, BANKNIFTY
    expiry VARCHAR(20),          -- 24DEC2025, 12MAR2026, etc
    option_type VARCHAR(5),      -- CE, PE, blank for futures/stocks
    strike VARCHAR(20),          -- Strike price
    exchange VARCHAR(10),        -- NFO, BFO, MCX, etc
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_shared_code(shared_code_id),
    INDEX idx_underlying(underlying),
    INDEX idx_expiry(expiry),
    INDEX idx_option_type(option_type)
);

-- ============================================================================
-- INSERT SAMPLE DATA
-- ============================================================================

-- Insert Shared Code
INSERT INTO shared_codes (shared_code_id, code_name, code_version, description)
VALUES (23894081, 'Directional Option Selling BNF With Hedge V4', '1.0', 'Main shared strategy code')
ON CONFLICT (shared_code_id) DO NOTHING;

-- Insert Sample Instruments for Shared Code 23894081
INSERT INTO instruments (shared_code_id, instrument_full, inst_type, underlying, expiry, option_type, strike, exchange)
VALUES
-- SENSEX Options
(23894081, 'OPTIDX_SENSEX_12MAR2026_CE_79500', 'OPTIDX', 'SENSEX', '12MAR2026', 'CE', '79500', 'BFO'),
(23894081, 'OPTIDX_SENSEX_12MAR2026_PE_78500', 'OPTIDX', 'SENSEX', '12MAR2026', 'PE', '78500', 'BFO'),
(23894081, 'OPTIDX_SENSEX_04DEC2025_CE_85700', 'OPTIDX', 'SENSEX', '04DEC2025', 'CE', '85700', 'BFO'),
(23894081, 'OPTIDX_SENSEX_24DEC2025_CE_85300', 'OPTIDX', 'SENSEX', '24DEC2025', 'CE', '85300', 'BFO'),
(23894081, 'OPTIDX_SENSEX_18DEC2025_CE_85100', 'OPTIDX', 'SENSEX', '18DEC2025', 'CE', '85100', 'BFO'),
(23894081, 'OPTIDX_SENSEX_13NOV2025_CE_84200', 'OPTIDX', 'SENSEX', '13NOV2025', 'CE', '84200', 'BFO'),
(23894081, 'OPTIDX_SENSEX_08JAN2026_CE_85200', 'OPTIDX', 'SENSEX', '08JAN2026', 'CE', '85200', 'BFO'),

-- NIFTY Options
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

-- Show all instruments for shared code 23894081
-- SELECT * FROM instruments WHERE shared_code_id = 23894081;

-- Show unique underlyings
-- SELECT DISTINCT underlying FROM instruments WHERE shared_code_id = 23894081 ORDER BY underlying;

-- Show all expiries
-- SELECT DISTINCT expiry FROM instruments WHERE shared_code_id = 23894081 ORDER BY expiry DESC;

-- Count instruments by underlying
-- SELECT underlying, COUNT(*) as count FROM instruments WHERE shared_code_id = 23894081 GROUP BY underlying;
