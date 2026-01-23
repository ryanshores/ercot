CREATE TABLE IF NOT EXISTS fuel_mix
(
    timestamp     TEXT PRIMARY KEY,
    fuel_mix      TEXT NOT NULL,
    pct_renewable REAL NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)