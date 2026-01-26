from datetime import datetime, UTC

from sqlalchemy.orm import Session

from src.models.energy import energy_sources
from src.schema import schema
from src.service.db.gen_instant import create_gen_instant

valid_data = {key: 10 for key in energy_sources}


def _generate_valid_data():
    return schema.GenInstantCreate(
        timestamp=datetime.now(UTC).isoformat(),
        sources={key: 10 for key in energy_sources}
    )


def test_create_valid_instant(db_session: Session):
    gen_instant = _generate_valid_data()
    db_gen_instant = create_gen_instant(db_session, gen_instant)
    assert db_gen_instant.timestamp == gen_instant.timestamp
    assert db_gen_instant.id is not None
    assert len(db_gen_instant.gen_sources) == len(valid_data)
    assert db_gen_instant.gen_renewables == 60.0
    assert db_gen_instant.gen_total == 80.0
    assert db_gen_instant.percentage_renewable == 75.0
