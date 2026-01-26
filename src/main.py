import os
import threading
import time

import schedule
import uvicorn

from src.db.database import SessionLocal, init_db
from src.logger.logger import get_logger
from src.router import app
from src.schema import schema
from src.service.db.gen_instant import create_gen_instant, GenInstantAlreadyExistsError
from src.service.ercot import Ercot

init_db()

logger = get_logger(__name__)

MODE_DEV = "dev"
MODE_PROD = "prod"

SCHEDULE_EVERY_MINUTES = 5

APP_MODE = os.getenv("APP_MODE", MODE_DEV)


def _create_ercot_snapshot() -> Ercot:
    # Ercot implements __enter__/__exit__, so use it as a context manager.
    with Ercot() as ercot:
        ercot.create_visualization()
        return ercot


def _persist_gen_mix(ercot: Ercot) -> None:
    mix = {key: value['gen'] for key, value in ercot.mix.items()}
    gen_instant = schema.GenInstantCreate(
        timestamp=ercot.timestamp,
        sources=mix
    )
    try:
        with SessionLocal() as db:
            create_gen_instant(db, gen_instant)
        logger.info("Saved gen instant for timestamp=%r", gen_instant.timestamp)
    except GenInstantAlreadyExistsError:
        logger.warning("GenInstantAlreadyExistsError for timestamp=%r", gen_instant.timestamp)


def run() -> None:

    try:
        ercot = _create_ercot_snapshot()
    except Exception as e:
        logger.exception("Error connecting to ERCOT", exc_info=e)
        return
    else:
        try:
            _persist_gen_mix(ercot)
        except Exception as e:
            logger.exception("Error saving gen instant", exc_info=e)


def run_scheduler() -> None:
    """Run the scheduler loop."""
    try:
        run()  # Run immediately
        tr = list(range(0, 60, SCHEDULE_EVERY_MINUTES))
        for t in tr:
            schedule.every().hour.at(f":{t:02d}").do(run)

        logger.info("Running schedule. Will check every %s minutes.", SCHEDULE_EVERY_MINUTES)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.exception("Error in scheduled run", exc_info=e)


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
