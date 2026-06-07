-- simple schema for TT Dashboard
-- Creates shared_codes and ttdata tables

DROP TABLE IF EXISTS ttdata;
DROP TABLE IF EXISTS shared_codes;

CREATE TABLE shared_codes (
  id SERIAL PRIMARY KEY,
  strategy_id VARCHAR(128) UNIQUE NOT NULL,
  strategy_name TEXT,
  status VARCHAR(64),
  creator_name TEXT,
  broker_name TEXT,
  exchange VARCHAR(32),
  all_pnl NUMERIC DEFAULT 0,
  max_run_counter INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE ttdata (
  id SERIAL PRIMARY KEY,
  strategy_id VARCHAR(128) NOT NULL,
  counter INTEGER DEFAULT 1,
  trade_date DATE,
  trade_time TIME,
  instrument_full TEXT,
  inst_type VARCHAR(32),
  underlying TEXT,
  expiry DATE,
  option_type VARCHAR(8),
  strike NUMERIC,
  qty NUMERIC,
  price NUMERIC,
  amount NUMERIC,
  note TEXT
);

CREATE INDEX IF NOT EXISTS idx_ttdata_strategy_id ON ttdata(strategy_id);
CREATE INDEX IF NOT EXISTS idx_ttdata_trade_date ON ttdata(trade_date);
