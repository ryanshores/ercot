from datetime import datetime, timedelta, UTC
from random import randint, random

from sqlalchemy.orm import Session

from src.models.energy import energy_sources
from src.schema import schema
from src.service.db.gen_instant import create_gen_instances

# We'll use recent dates to ensure they fall within the '1W' timespan in tests.
_now = datetime.now(UTC)
_d1 = (_now - timedelta(days=3)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
_d2 = (_now - timedelta(days=2)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
_d3 = (_now - timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

out_of_order_days = [_d1, _d3, _d2]
in_order_days = [_d1, _d2, _d3]


# using energy_source create new object with key: random number [0, 30000]
def _create_mix() -> dict[str, float]:
    mix = {}
    for source in energy_sources.keys():
        mix[source] = randint(0, 30000) * random()
    return mix


def seed(db_session: Session):
    seed_instants = [schema.GenInstantCreate(
                    timestamp=date,
                    sources=_create_mix()
                ) for date in out_of_order_days]
    create_gen_instances(db_session, seed_instants)
