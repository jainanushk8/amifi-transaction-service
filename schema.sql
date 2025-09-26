-- @ai perplexity database-schema
-- Transaction processing schema for AmiFi
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,  -- UUID
    userid TEXT NOT NULL DEFAULT 'demo-user',
    ts TIMESTAMP NOT NULL,
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    account_ref TEXT,
    channel TEXT NOT NULL,  -- 'sms' or 'email'
    raw_msg_id TEXT NOT NULL,  -- hash of raw line
    hash TEXT UNIQUE NOT NULL,  -- idempotency key
    type TEXT NOT NULL,  -- 'credit', 'debit', 'bill', 'fee', 'other'
    category TEXT,  -- 'shopping', 'utilities', etc.
    confidence REAL NOT NULL DEFAULT 0.0,  -- 0..1
    meta JSON,  -- arbitrary details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goal_impacts (
    id TEXT PRIMARY KEY,  -- UUID
    transaction_id TEXT NOT NULL,
    goal_id TEXT NOT NULL,  -- 'demo-savings', 'cc-bill', etc.
    impact_score REAL NOT NULL,  -- -1..1
    message TEXT NOT NULL,  -- human-readable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(hash);
CREATE INDEX IF NOT EXISTS idx_transactions_userid_ts ON transactions(userid, ts);
CREATE INDEX IF NOT EXISTS idx_goal_impacts_transaction ON goal_impacts(transaction_id);
