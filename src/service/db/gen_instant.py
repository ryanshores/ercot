from sqlalchemy.orm import Session

from src.models import energy as energy_models
from src.schema import schema


def get_gen_instant(db: Session, timestamp: str) -> energy_models.GenInstant | None:
    return db.query(energy_models.GenInstant).filter(energy_models.GenInstant.timestamp == timestamp).first()


def create_gen_instant(db: Session, gen_instant: schema.GenInstantCreate) -> energy_models.GenInstant:
    db_gen_instant = energy_models.GenInstant(gen_instant.timestamp, gen_instant.gen_sources)
    db.add(db_gen_instant)
    db.commit()
    db.refresh(db_gen_instant)
    return db_gen_instant
