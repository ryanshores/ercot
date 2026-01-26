from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.service.dashboard_service import DashboardService

# Project root (../ from this file because this file lives in src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "out"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Create the templates directory if it doesn't exist
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount the 'out' folder to be served at '/images'
app.mount("/images", StaticFiles(directory=str(OUT_DIR)), name="images")


@app.get("/", response_class=HTMLResponse)
def list_images(
        request: Request,
        page: int = 1,
        page_size: int = 20,
        sort: str = "desc"
):
    """
    Endpoint to list all images in the 'out' folder with paging and sorting.
    """
    files = [
        f.name
        for f in OUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]

    # Sort files
    files.sort(reverse=(sort == "desc"))

    # Pagination
    total = len(files)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_files = files[start:end]

    return templates.TemplateResponse(
        request,
        "images.html",
        {
            "files": paginated_files,
            "page": page,
            "page_size": page_size,
            "sort": sort,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
        request: Request,
        timespan: str = '5D',  # 3W, 1M, 3M, 6M, 1Y
        db: Session = Depends(get_db)):
    """
    UI dashboard to view the data over time.
    """
    labels, datasets = DashboardService.get_dashboard_data(db, timespan)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "labels": labels,
            "datasets": datasets
        }
    )
