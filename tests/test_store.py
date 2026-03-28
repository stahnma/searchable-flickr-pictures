import tempfile
import os
from flickr_index.store import PhotoStore


def test_add_and_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(
            photo_id="12345",
            description="A golden retriever playing fetch on a sandy beach at sunset",
            metadata={
                "title": "Beach Dog",
                "flickr_url": "https://flickr.com/photos/user/12345",
                "image_url": "https://farm1.static.flickr.com/12345.jpg",
                "published": "2026-03-01",
                "indexed_at": "2026-03-28T12:00:00",
            },
        )
        results = store.search("dog on beach", n_results=5)
        assert len(results) == 1
        assert results[0]["id"] == "12345"
        assert results[0]["description"] == "A golden retriever playing fetch on a sandy beach at sunset"
        assert results[0]["metadata"]["title"] == "Beach Dog"


def test_add_duplicate_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="111", description="A cat", metadata={"title": "Cat"})
        store.add(photo_id="111", description="A dog", metadata={"title": "Dog"})
        results = store.list_all()
        assert len(results) == 1
        assert results[0]["description"] == "A cat"


def test_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        assert store.exists("999") is False
        store.add(photo_id="999", description="A tree", metadata={"title": "Tree"})
        assert store.exists("999") is True


def test_get_by_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="42", description="Mountains at dawn", metadata={"title": "Dawn"})
        photo = store.get("42")
        assert photo is not None
        assert photo["description"] == "Mountains at dawn"
        assert store.get("nonexistent") is None


def test_list_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="1", description="Photo one", metadata={"title": "One"})
        store.add(photo_id="2", description="Photo two", metadata={"title": "Two"})
        results = store.list_all()
        assert len(results) == 2
        ids = {r["id"] for r in results}
        assert ids == {"1", "2"}
