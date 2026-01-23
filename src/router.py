from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Project root (../ from this file because this file lives in src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "out"

app = FastAPI()

# Mount the 'out' folder to be served at '/images'
app.mount("/images", StaticFiles(directory=str(OUT_DIR)), name="images")


@app.get("/", response_class=HTMLResponse)
def list_images():
    """
    Simple endpoint to list all images in the 'out' folder.
    """
    files = [
        f.name
        for f in OUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    files.sort(reverse=True)

    html_content = (
        "<html><head><title>ERCOT Images</title></head><body>"
        "<h1>ERCOT Visualizations</h1><ul>"
    )
    for file in files:
        html_content += f'<li><a href="/images/{file}">{file}</a></li>'
    html_content += "</ul></body></html>"
    return html_content
