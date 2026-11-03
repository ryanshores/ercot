from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import src.router


def test_images_removed():
    client = TestClient(src.router.app)
    assert client.get("/images").status_code == 404
    assert client.get("/images/old.png").status_code == 404


def test_dashboard(db_session: Session):
    # Use dependency_overrides to inject the test database session
    src.router.app.dependency_overrides[src.router.get_db] = lambda: db_session

    try:
        client = TestClient(src.router.app)
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "canvas" in response.text
        assert "/images" not in response.text
        assert response.context['labels'] is not None
        assert response.context['datasets'] is not None

        # Verify that datasets have fill: True
        for dataset in response.context['datasets']:
            assert dataset['fill']
    finally:
        # Clean up overrides to avoid affecting other tests
        src.router.app.dependency_overrides.clear()
