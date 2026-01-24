import os
import threading
import time
from typing import Iterator

import schedule
import uvicorn
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db_1 import get_conn, init_db, save_gen_mix
from src.logger.logger import get_logger
from src.router import app
from src.service.ercot import Ercot

logger = get_logger(__name__)

MODE_DEV = "dev"
MODE_PROD = "prod"

SCHEDULE_EVERY_MINUTES = 15

APP_MODE = os.getenv("APP_MODE", MODE_DEV)


def _init_db_connection():
    conn = get_conn()
    init_db(conn)
    return conn


def get_db() -> Iterator[Session]:
    """Dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_ercot_snapshot() -> Ercot:
    # Ercot implements __enter__/__exit__, so use it as a context manager.
    with Ercot() as ercot:
        ercot.create_visualization()
        return ercot


def _persist_gen_mix(conn, ercot: Ercot) -> None:
    save_gen_mix(
        conn,
        ercot.timestamp,
        ercot.coal,
        ercot.hydro,
        ercot.nuclear,
        ercot.natural_gas,
        ercot.other,
        ercot.power_storage,
        ercot.solar,
        ercot.wind,
    )


def run() -> None:
    try:
        conn = _init_db_connection()
    except Exception:
        logger.exception("Error connecting to database")
        return

    try:
        ercot = _create_ercot_snapshot()
    except Exception:
        logger.exception("Error connecting to ERCOT")
        return

    try:
        _persist_gen_mix(conn, ercot)
    except Exception:
        logger.exception("Error saving gen mix")


def run_scheduler() -> None:
    """Run the scheduler loop."""
    try:
        run()  # Run immediately
        schedule.every(15).minutes.do(run)

        logger.info("Running schedule. Will check every %s minutes.", SCHEDULE_EVERY_MINUTES)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception:
        logger.exception("Error in scheduled run")


def _start_scheduler_thread() -> None:
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


def main() -> None:
    if APP_MODE == MODE_DEV:
        run()
        return

    if APP_MODE == MODE_PROD:
        _start_scheduler_thread()
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return

    logger.warning("Unknown APP_MODE=%r; expected %r or %r.", APP_MODE, MODE_DEV, MODE_PROD)


# ==== STARTUP ====
if __name__ == "__main__":
    main()
