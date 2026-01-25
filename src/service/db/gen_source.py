from typing import List

from sqlalchemy.orm import Session

from src.models import energy as energy_models
from src.schema import schema
from src.service.db.source_service import get_source, get_or_create_source


def get_source_gens(db: Session, source_name: str) -> List[type[energy_models.GenSource]]:
    source = get_source(db, source_name)
    if source is None:
        raise ValueError(f"Source '{source_name}' not found")
    return db.query(energy_models.GenSource).filter(energy_models.GenSource.source.name == source_name).all()


def create_source_gen(db: Session, gen_source: schema.GenSourceCreate) -> energy_models.GenSource:
    db_source = get_or_create_source(db, gen_source.source_name)
    db_gen_source = energy_models.GenSource(gen_source.gen, db_source)
    db.add(db_gen_source)
    db.commit()
    db.refresh(db_gen_source)
    return db_gen_source
