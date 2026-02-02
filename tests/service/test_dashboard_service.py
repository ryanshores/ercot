from sqlalchemy.orm import Session

from src.service.dashboard_service import DashboardService
from tests.fixtures.gen_instants import in_order_days


def test_get_dashboard_data(db_session: Session, seed_sources: None, seed_gen_instants: None):

    labels, datasets = DashboardService().get_dashboard_data(db_session, '1W')
    assert labels == in_order_days
