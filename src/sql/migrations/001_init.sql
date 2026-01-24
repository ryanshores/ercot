CREATE TABLE IF NOT EXISTS gen_mix
(
    timestamp     TEXT PRIMARY KEY,
    coal          REAL NOT NULL,
    hydro         REAL NOT NULL,
    nuclear       REAL NOT NULL,
    natural_gas   REAL NOT NULL,
    other         REAL NOT NULL,
    power_storage REAL NOT NULL,
    solar         REAL NOT NULL,
    wind          REAL NOT NULL,
    total_gen     REAL GENERATED ALWAYS AS (coal + hydro + nuclear + natural_gas + other + power_storage + solar + wind) STORED,
    renewable_gen REAL GENERATED ALWAYS AS (hydro + nuclear + power_storage + solar + wind) STORED,
    pct_renewable REAL GENERATED ALWAYS AS (CASE WHEN total_gen = 0 THEN 0 ELSE (renewable_gen / total_gen) * 100 END) STORED,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)