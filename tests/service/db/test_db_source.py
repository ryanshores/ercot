from sqlalchemy.orm import Session

from src.models.energy import energy_sources, Source
from src.service.db import source_service


def test_get_source(db_session: Session, seed_sources: None):
    """Tests retrieval of seeded sources by name"""
    for source in energy_sources.keys():
        test_source = Source(name=source)
        db_source = source_service.get_source(db_session, test_source.name)
        assert db_source is not None
        assert db_source.name == test_source.name
        assert db_source.renewable == test_source.renewable


def test_get_sources(db_session: Session, seed_sources: None):
    expected_length = len(energy_sources)
    assert len(source_service.get_sources(db_session)) == expected_length
