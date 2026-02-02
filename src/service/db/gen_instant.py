from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.energy import GenInstant, GenSource
from src.schema import schema
from src.service.db.source_service import get_or_create_source


class GenInstantAlreadyExistsError(ValueError):
    def __init__(self, timestamp: str) -> None:
        super().__init__(f"GenInstant already exists for timestamp={timestamp!r}")
        self.timestamp = timestamp


def get_gen_instant(db: Session, timestamp: str) -> GenInstant | None:
    return db.query(GenInstant).filter(GenInstant.timestamp == timestamp).first()


def get_last_x_gen_instants(db: Session, n: int) -> list[GenInstant]:
    return db.query(GenInstant).order_by(GenInstant.timestamp.desc()).limit(n).all()


def get_by_dates(db: Session, start_time: datetime, end_time: datetime) -> list[GenInstant]:
    return db.query(GenInstant).filter(
        GenInstant.created_at >= start_time,
        GenInstant.created_at <= end_time
    ).all()


def create_gen_instant(db: Session, gen_instant: schema.GenInstantCreate, commit: bool = True) -> GenInstant:
    # Friendly early failure (fast path)
    existing = get_gen_instant(db, gen_instant.timestamp)
    if existing is not None:
        raise GenInstantAlreadyExistsError(gen_instant.timestamp)

    gen_sources: list[GenSource] = []
    for source_label, gen in gen_instant.sources.items():
        db_source = get_or_create_source(db, source_label)
        gen_sources.append(GenSource(gen=gen, source=db_source))

    db_gen_instant = GenInstant(gen_instant.timestamp, gen_sources)
    db.add(db_gen_instant)

    if commit:
        try:
            db.commit()
        except IntegrityError:
            # Handles race condition: another transaction inserted the same timestamp.
            db.rollback()
            raise GenInstantAlreadyExistsError(gen_instant.timestamp)

        db.refresh(db_gen_instant)

    return db_gen_instant


def create_gen_instances(db: Session, gen_instants: list[schema.GenInstantCreate]) -> list[GenInstant]:
    """
    Create multiple gen instant records in a single transaction, while skipping any duplicates.

    Args:
        db (Session): Database session.
        gen_instants (list[schema.GenInstantCreate]): List of gen instant creation schemas.

    Returns:
        list[GenInstant]: List of created gen instant records.
    """

    instants_to_commit = []
    for gen_instant in gen_instants:
        try:
            created_instant = create_gen_instant(db, gen_instant, commit=False)
            instants_to_commit.append(created_instant)
        except GenInstantAlreadyExistsError:
            # Skip duplicates
            continue
    db.commit()
    return instants_to_commit
