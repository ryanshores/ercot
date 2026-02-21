from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import src.router


class FakeOutDir:
    def __init__(self, entries):
        self._entries = entries

    def iterdir(self):
        return self._entries


def test_list_images_with_no_files(monkeypatch, tmp_path):
    monkeypatch.setattr(src.router, "OUT_DIR", tmp_path)

    client = TestClient(src.router.app)
    response = client.get("/")

    assert response.status_code == 200
    assert '<a href="/" class="nav-brand">🔌 ERCOT</a>' in response.text


def test_list_images_with_files(monkeypatch, tmp_path):
    # Create real files in tmp_path
    (tmp_path / "image1.png").touch()
    (tmp_path / "image2.jpg").touch()
    (tmp_path / "image3.jpeg").touch()

    monkeypatch.setattr(src.router, "OUT_DIR", tmp_path)

    client = TestClient(src.router.app)
    response = client.get("/images")

    assert response.status_code == 200
    assert '/images/image1.png' in response.text
    assert '/images/image2.jpg' in response.text
    assert '/images/image3.jpeg' in response.text


def test_list_images_sorts_files_in_reverse_order(monkeypatch, tmp_path):
    # Create files in an order that isn't reverse-sorted
    (tmp_path / "image2.jpg").touch()
    (tmp_path / "image3.png").touch()
    (tmp_path / "image1.jpeg").touch()

    monkeypatch.setattr(src.router, "OUT_DIR", tmp_path)

    client = TestClient(src.router.app)
    response = client.get("/images")

    assert response.status_code == 200

    i3 = response.text.index('/images/image3.png')
    i2 = response.text.index('/images/image2.jpg')
    i1 = response.text.index('/images/image1.jpeg')
    assert i3 < i2 < i1


def test_dashboard(db_session: Session):
    # Use dependency_overrides to inject the test database session
    src.router.app.dependency_overrides[src.router.get_db] = lambda: db_session

    try:
        client = TestClient(src.router.app)
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "canvas" in response.text
        assert response.context['labels'] is not None
        assert response.context['datasets'] is not None

        # Verify that datasets have fill: True
        for dataset in response.context['datasets']:
            assert dataset['fill']
    finally:
        # Clean up overrides to avoid affecting other tests
        src.router.app.dependency_overrides.clear()
