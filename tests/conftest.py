import os
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.db.database import Base
from src.service.db.source_service import seed as db_seed_sources
from tests.fixtures.gen_instants import seed as db_seed_gen_instants


@pytest.fixture(scope="session")
def engine():
    os.makedirs("/tmp", exist_ok=True)
    engine = create_engine("sqlite:////tmp/test.db")
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = local_session()
    try:
        yield db
    finally:
        # Since we use a session-scoped engine with an in-memory database,
        # we need to clear the data between tests if we want function-level isolation.
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def seed_sources(db_session: Session):
    db_seed_sources(db_session)


@pytest.fixture(scope="function")
def seed_gen_instants(db_session: Session):
    db_seed_gen_instants(db_session)
