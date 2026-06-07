-- seed sample data for TT Dashboard

INSERT INTO shared_codes (strategy_id, strategy_name, status, creator_name, broker_name, exchange, all_pnl, max_run_counter)
VALUES
('SC1001','Market Star ETF Portfolio','Active','Market Star','IIFL', 'NSE', 29.00, 6),
('SC1002','0945 - 08 Prem Safe Sensex Weekly','Completed','Gopi J','Stocko','NSE', -223.00, 14),
('SC1003','1020 - 08 Prem Safe Sensex Weekly','Completed','Gopi J','Stocko','NSE', -650.00, 17);

-- Insert some ttdata (counters/rounds)
INSERT INTO ttdata (strategy_id, counter, trade_date, trade_time, instrument_full, inst_type, underlying, qty, price, amount)
VALUES
('SC1001', 6, '2026-04-30', '09:45:00', 'ETF-ABC', 'EQ', 'NIFTY', 1, 100.0, 29.00),
('SC1002', 14, '2026-03-25', '10:20:00', 'FUT-XYZ', 'FUT', 'SENSEX', 1, 200.0, -223.00),
('SC1003', 17, '2026-03-26', '12:00:00', 'OPT-123', 'OPT', 'SENSEX', 1, 50.0, -650.00);
