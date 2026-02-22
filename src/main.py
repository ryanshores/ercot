import os
import threading
import time

import schedule
import uvicorn

from src.logger.logger import get_logger
from src.router import app
from src.service.ercot import Ercot

MODE_DEV = "dev"
MODE_PROD = "prod"

APP_MODE = os.getenv("APP_MODE", MODE_DEV)

logger = get_logger(__name__)

SCHEDULE_EVERY_MINUTES = 30


def run() -> None:

    try:
        with Ercot() as ercot:
            ercot.create_visualization()
    except Exception as e:
        logger.exception("Error connecting to ERCOT", exc_info=e)
        return


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
