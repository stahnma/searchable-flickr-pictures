import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from flickr_index.main import create_app
from flickr_index.store import PhotoStore


def test_health():
    with tempfile.TemporaryDirectory() as tmpdir:
        app = create_app(data_dir=tmpdir)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_search_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        app = create_app(data_dir=tmpdir)
        client = TestClient(app)
        # Add a photo first so the collection isn't empty
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="1", description="A sunset", metadata={"title": "Sunset"})
        response = client.get("/search", params={"q": "mountains"})
        assert response.status_code == 200
        assert "results" in response.json()


def test_list_photos():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="1", description="A sunset", metadata={"title": "Sunset"})
        app = create_app(data_dir=tmpdir)
        client = TestClient(app)
        response = client.get("/photos")
        assert response.status_code == 200
        assert len(response.json()["photos"]) == 1


def test_get_photo():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="42", description="A mountain", metadata={"title": "Peak"})
        app = create_app(data_dir=tmpdir)
        client = TestClient(app)
        response = client.get("/photos/42")
        assert response.status_code == 200
        assert response.json()["description"] == "A mountain"


def test_get_photo_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        app = create_app(data_dir=tmpdir)
        client = TestClient(app)
        response = client.get("/photos/nonexistent")
        assert response.status_code == 404
