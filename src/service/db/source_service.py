from sqlalchemy.orm import Session

from src.models import energy as energy_models
from src.models.energy import energy_sources
from src.schema import schema


def seed(db: Session):
    for source in energy_sources.keys():
        source_create = schema.SourceCreate(name=source)
        create_source(db, source_create)


def get_source(db: Session, name: str) -> energy_models.Source | None:
    return db.query(energy_models.Source).filter(energy_models.Source.name == name).first()


def get_sources(db: Session) -> list[type[energy_models.Source]]:
    return db.query(energy_models.Source).all()


def create_source(db: Session, source: schema.SourceCreate) -> energy_models.Source:
    db_source = energy_models.Source(source.name)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source
