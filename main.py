import time
import traceback

import schedule

from logger import get_logger
from clients.twitter import Twitter
from clients.ercot import Ercot

logger = get_logger(__name__)

def run():
    try:
        with Ercot() as ercot_client:
            ercot_client.create_visualization()
            # with Twitter() as twitter:
            #     twitter.post(ercot_client.message)
    except Exception:
        traceback.print_exc()

def run_scheduled():
    """
    This function is called by the scheduler.
    It runs the main function and handles exceptions.
    """
    try:
        run() # Run immediately
        schedule.every(2).hours.at(":00").do(run)

        print("Bot running. Will post every 2 hours.")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in scheduled run: {e}")
        traceback.print_exc()

# ==== SCHEDULER ====
if __name__ == "__main__":
    run_scheduled()