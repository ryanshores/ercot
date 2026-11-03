from contextlib import contextmanager

import pytest

from src.service.ercot import Ercot
from src.service.db.gen_instant import get_gen_instant


@pytest.mark.parametrize('storage', [-120.0, 250.0])
def test_import_storage_breakdown_without_double_counting(monkeypatch, db_session, storage):
    @contextmanager
    def session():
        yield db_session

    monkeypatch.setattr('src.service.ercot.SessionLocal', session)
    timestamp = '2026-11-02 12:00:00-0600'
    mix = {name: {'gen': 100.0} for name in Ercot.FUEL_KEYS.values()}
    mix['Power Storage'] = {'gen': storage}
    mix['Power Storage Charging'] = {'gen': min(storage, 0)}
    mix['Power Storage Discharging'] = {'gen': max(storage, 0)}
    data = {'2026-11-02': {timestamp: mix}}
    ercot = Ercot()
    ercot._process_gen_mixes(data)
    ercot._process_gen_mixes(data)  # overlapping feed windows remain idempotent
    instant = get_gen_instant(db_session, timestamp)
    assert len(instant.gen_sources) == 8
    assert sum(source.gen for source in instant.gen_sources) == 700 + storage
    assert next(s.gen for s in instant.gen_sources if s.source.name == 'power_storage') == storage


def test_import_failure_is_not_swallowed(monkeypatch):
    def failed_session():
        raise RuntimeError('database unavailable')

    monkeypatch.setattr('src.service.ercot.SessionLocal', failed_session)
    with pytest.raises(RuntimeError, match='database unavailable'):
        Ercot()._process_gen_mixes({})
