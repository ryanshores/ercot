from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.energy import energy_sources
from src.service.dashboard_service import DashboardService

# Project root (../ from this file because this file lives in src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Create the templates directory if it doesn't exist
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI()

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

cache_header = {"Cache-Control": f"max-age={60 * 5}, must-revalidate"}


# Healthcheck endpoint
@app.get("/health", response_model=dict)
def health_check():
    """Simple health check endpoint returning status OK."""
    return {"status": "ok"}


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
