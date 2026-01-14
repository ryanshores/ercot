import os
import threading
import time
import traceback

import schedule
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from clients.ercot import Ercot
from logger import get_logger

logger = get_logger(__name__)

APP_MODE = os.getenv('APP_MODE', 'dev')
app = FastAPI()

# Mount the 'out' folder to be served at '/images'
app.mount("/images", StaticFiles(directory="out"), name="images")


@app.get("/", response_class=HTMLResponse)
def list_images():
    """
    Simple endpoint to list all images in the 'out' folder.
    """
    files = [f for f in os.listdir("out") if f.endswith((".png", ".jpg", ".jpeg"))]
    files.sort(reverse=True)

    html_content = "<html><head><title>ERCOT Images</title></head><body><h1>ERCOT Visualizations</h1><ul>"
    for file in files:
        html_content += f'<li><a href="/images/{file}">{file}</a></li>'
    html_content += "</ul></body></html>"
    return html_content

def run():
    try:
        with Ercot() as ercot_client:
            ercot_client.create_visualization()
    except Exception as e:
        logger.error(f"Error in run: {e}")


def run_scheduler():
    """
    This function runs the scheduler in a loop.
    """
    try:
        run() # Run immediately
        schedule.every(2).hours.at(":00").do(run)

        logger.info("Running schedule. Will check every 2 hours.")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in scheduled run: {e}")
        traceback.print_exc()


def main():
    # Start the scheduler in a background thread
    target = run_scheduler if APP_MODE == 'prod' else run
    scheduler_thread = threading.Thread(target=target, daemon=True)
    scheduler_thread.start()

    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ==== STARTUP ====
if __name__ == "__main__":
    main()
