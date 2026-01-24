from sqlalchemy.orm import Session

from src.models import energy as energy_models
from src.models.energy import energy_sources
from src.schema import schema


def seed(db: Session):
    for source in energy_sources.keys():
        get_or_create_source(db, source)
        db.commit()


def get_source(db: Session, name: str) -> energy_models.Source | None:
    return db.query(energy_models.Source).filter(energy_models.Source.name == name).first()


def get_sources(db: Session) -> list[type[energy_models.Source]]:
    return db.query(energy_models.Source).all()


def get_or_create_source(db: Session, source_label: str) -> energy_models.Source:
    """
    source_label: human label key (e.g. "Coal and Lignite")
    Returns a persisted Source with a canonical name (e.g. "coal").
    """
    source_meta = energy_models.Source.metadata_for(source_label)
    canonical_name = source_meta["name"]
    existing = get_source(db, canonical_name)
    if existing is not None:
        return existing

    db_source = energy_models.Source(source_label)
    db.add(db_source)
    db.flush()  # get PK without committing the whole transaction
    return db_source


def create_source(db: Session, source: schema.SourceCreate) -> energy_models.Source:
    # Keep this as an explicit "create + commit" API if you want it elsewhere.
    db_source = get_or_create_source(db, source.name)
    db.commit()
    db.refresh(db_source)
    return db_source