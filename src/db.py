import sqlite3
from pathlib import Path

from logger import get_logger

DEFAULT_DB_PATH = Path("data") / "ercot.db"
SQL_FILES_PATH = Path(__file__).parent / "sql"

logger = get_logger(__name__)


def get_conn(db_path=DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    logger.info(f"Connected to database: {db_path}")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    migrations_path = SQL_FILES_PATH / "migrations"
    migrations = sorted(migrations_path.glob("*.sql"))
    for migration in migrations:
        logger.info(f"Running migration: {migration}")
        with conn:
            conn.executescript(open(migration).read())
            conn.commit()


def save_fuel_mix(
        conn: sqlite3.Connection,
        timestamp: str,
        fuel_mix: dict,
        pct_renewable: float
) -> None:
    with conn:
        conn.execute(
            "INSERT INTO fuel_mix (timestamp, fuel_mix, pct_renewable) "
            "VALUES (?, ?, ?)",
            (timestamp, str(fuel_mix), pct_renewable)
        )
        logger.info(f"Saved fuel mix for {timestamp}")
        conn.commit()
