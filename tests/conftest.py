from typing import Generator

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from src.db.database import Base
from src.service.db.source_service import seed


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="session")
def db_session(engine) -> Generator[Session, None, None]:
    local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = local_session()
    try:
        yield db
    finally:
        Base.metadata.drop_all(bind=engine)
        db.close()


@pytest.fixture(scope="session")
def seed_sources(db_session: Session):
    seed(db_session)
