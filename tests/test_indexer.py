import tempfile
from unittest.mock import patch, MagicMock
from flickr_index.indexer import Indexer
from flickr_index.store import PhotoStore


SAMPLE_RSS = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Beach Sunset</title>
    <link rel="alternate" type="text/html" href="https://www.flickr.com/photos/user/12345/"/>
    <id>tag:flickr.com,2005:/photo/12345</id>
    <published>2026-03-01T12:00:00Z</published>
    <content type="html">&lt;p&gt;&lt;a href="https://www.flickr.com/photos/user/12345/"&gt;&lt;img src="https://live.staticflickr.com/server/12345_secret_b.jpg" alt="Beach Sunset"/&gt;&lt;/a&gt;&lt;/p&gt;</content>
  </entry>
</feed>"""


def test_parse_feed():
    indexer = Indexer.__new__(Indexer)
    entries = indexer.parse_feed(SAMPLE_RSS)
    assert len(entries) == 1
    assert entries[0]["photo_id"] == "12345"
    assert entries[0]["title"] == "Beach Sunset"
    assert "flickr.com" in entries[0]["flickr_url"]


def test_index_skips_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="12345", description="Already indexed", metadata={"title": "Old"})

        indexer = Indexer.__new__(Indexer)
        indexer.store = store
        indexer.model = "moondream"
        indexer.ollama_url = "http://localhost:11434"

        entries = [{"photo_id": "12345", "title": "Test", "flickr_url": "http://example.com", "image_url": "http://example.com/img.jpg", "published": "2026-03-01"}]
        result = indexer.index_entries(entries)
        assert result["skipped"] == 1
        assert result["indexed"] == 0
