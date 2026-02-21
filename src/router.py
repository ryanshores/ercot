from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.energy import energy_sources
from src.service.dashboard_service import DashboardService

# Project root (../ from this file because this file lives in src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "out"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Create the templates directory if it doesn't exist
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI()


# Healthcheck endpoint
@app.get("/health", response_model=dict)
def health_check():
    """Simple health check endpoint returning status OK."""
    return {"status": "ok"}


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount the 'out' folder to be served at '/images'
app.mount("/images", StaticFiles(directory=str(OUT_DIR)), name="images")


cache_header = {"Cache-Control": f"max-age={60 * 5}, must-revalidate"}


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    days: int = 30,
    view: str = "graph",  # 'graph' or 'table'
    db: Session = Depends(get_db),
):
    """
    Homepage showing daily generation overview.
    """
    chart_data, table_data = DashboardService.get_generation_by_day(db, days)

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "chart_data": chart_data,
            "table_data": table_data,
            "days": days,
            "view": view,
        },
        headers=cache_header,
    )


@app.get("/images", response_class=HTMLResponse)
def list_images(
    request: Request, page: int = 1, page_size: int = 20, sort: str = "desc"
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
            "total_pages": (total + page_size - 1) // page_size,
        },
        headers=cache_header,
    )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    timespan: str = "5D",  # 3W, 1M, 3M, 6M, 1Y
    db: Session = Depends(get_db),
):
    """
    UI dashboard to view the data over time.
    """
    labels, datasets = DashboardService.get_dashboard_data(db, timespan)

    # Build color mappings from energy_sources for frontend
    source_colors = {}
    for key, meta in energy_sources.items():
        source_colors[meta["name"]] = meta["color"]
    source_colors["power storage (discharging)"] = "#FF5078"
    source_colors["power storage (charging)"] = "#FF6384"

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"labels": labels, "datasets": datasets, "source_colors": source_colors},
        headers=cache_header,
    )


@app.get("/generation-by-day", response_class=HTMLResponse)
def generation_by_day(
    request: Request,
    days: int = 30,
    view: str = "graph",  # 'graph' or 'table'
    db: Session = Depends(get_db),
):
    """
    UI dashboard to view total energy generation by day with renewable percentage.
    """
    chart_data, table_data = DashboardService.get_generation_by_day(db, days)

    return templates.TemplateResponse(
        request,
        "generation_by_day.html",
        {
            "chart_data": chart_data,
            "table_data": table_data,
            "days": days,
            "view": view,
        },
        headers=cache_header,
    )
