import sqlite3
from pathlib import Path

from src.logger import get_logger

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


def save_gen_mix(
        conn: sqlite3.Connection,
        timestamp: str,
        coal: float,
        hydro: float,
        nuclear: float,
        natural_gas: float,
        other: float,
        power_storage: float,
        solar: float,
        wind: float) -> None:
    with conn:
        conn.execute(
            "INSERT INTO gen_mix (timestamp, coal, hydro, nuclear, natural_gas, other, power_storage, solar, wind) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            "ON CONFLICT (timestamp) DO UPDATE SET coal = excluded.coal, hydro = excluded.hydro, "
            "nuclear = excluded.nuclear, natural_gas = excluded.natural_gas, other = excluded.other, "
            "power_storage = excluded.power_storage, solar = excluded.solar, wind = excluded.wind",
            (timestamp, coal, hydro, nuclear, natural_gas, other, power_storage, solar, wind)
        )
        logger.info(f"Saved gen mix for {timestamp}")
        conn.commit()
