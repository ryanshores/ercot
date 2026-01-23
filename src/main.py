import os
import threading
import time
import traceback

import schedule
import uvicorn

from src.clients.ercot import Ercot
from src.db import save_fuel_mix, get_conn, init_db
from src.logger import get_logger
from src.router import app

logger = get_logger(__name__)

APP_MODE = os.getenv('APP_MODE', 'dev')


def run():
    try:
        with get_conn() as conn:
            init_db(conn)
            with Ercot() as ercot_client:
                save_fuel_mix(
                    conn,
                    ercot_client.timestamp,
                    ercot_client.mix,
                    ercot_client.pct_renewable
                )
                ercot_client.create_visualization()
    except Exception as e:
        logger.error(f"Error in run: {e}")


def run_scheduler():
    """
    This function runs the scheduler in a loop.
    """

    try:
        run()  # Run immediately
        schedule.every(2).hours.at(":00").do(run)

        logger.info("Running schedule. Will check every 2 hours.")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in scheduled run: {e}")
        traceback.print_exc()


def main():
    # Run once if not in production mode
    if APP_MODE == 'dev':
        run()
    elif APP_MODE == 'prod':
        # Start the scheduler in a background thread
        target = run_scheduler if APP_MODE == 'prod' else run
        scheduler_thread = threading.Thread(target=target, daemon=True)
        scheduler_thread.start()

        # Run the FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000)


# ==== STARTUP ====
if __name__ == "__main__":
    main()
