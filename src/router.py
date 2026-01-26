from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.service.db.gen_instant import get_by_dates

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
    # Map units to days for conversion
    unit_map = {'D': 1, 'W': 7, 'M': 30, 'Y': 365}
    try:
        unit = timespan[-1].upper()
        amount = int(timespan[:-1])
        delta_days = amount * unit_map.get(unit, 0)
    except (ValueError, IndexError):
        delta_days = 0

    if delta_days == 0:
        delta_days = 5

    # Compute start and end timestamps
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=delta_days)

    # Fetch and reverse entries for chronological order
    instants = get_by_dates(db, start_time, end_time)

    # Prepare data for Chart.js
    labels = [i.timestamp for i in instants]

    # Collect and categorize source names and their data in a single pass
    non_renewable_sources = set()
    renewable_sources = set()
    # Map source_name -> list of generation values (aligned with instants)
    source_data_map = {}

    for i_idx, instant in enumerate(instants):
        for gs in instant.gen_sources:
            name = gs.source.name
            if name not in source_data_map:
                source_data_map[name] = [0] * len(instants)
                if gs.source.renewable:
                    renewable_sources.add(name)
                else:
                    non_renewable_sources.add(name)
            source_data_map[name][i_idx] = gs.gen

    # Build datasets: Non-renewable first, then Renewable, both sorted alphabetically
    datasets = []
    for source_name in sorted(non_renewable_sources):
        datasets.append({
            "label": source_name,
            "data": source_data_map[source_name],
            "fill": True
        })

    for source_name in sorted(renewable_sources):
        datasets.append({
            "label": source_name,
            "data": source_data_map[source_name],
            "fill": '-1'
        })

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "labels": labels,
            "datasets": datasets
        }
    )
