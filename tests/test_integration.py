"""
Integration test: RSS parsing → store → search.
Skips Moondream (requires model download) — uses mock captioning.
"""
import tempfile
from unittest.mock import patch, MagicMock
from flickr_index.indexer import Indexer
from flickr_index.store import PhotoStore


SAMPLE_RSS = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Mountain View</title>
    <link rel="alternate" type="text/html" href="https://www.flickr.com/photos/testuser/11111/"/>
    <id>tag:flickr.com,2005:/photo/11111</id>
    <published>2026-03-15T10:00:00Z</published>
    <content type="html">&lt;img src="https://live.staticflickr.com/server/11111_abc_b.jpg" alt="Mountain View"/&gt;</content>
  </entry>
  <entry>
    <title>City Night</title>
    <link rel="alternate" type="text/html" href="https://www.flickr.com/photos/testuser/22222/"/>
    <id>tag:flickr.com,2005:/photo/22222</id>
    <published>2026-03-16T20:00:00Z</published>
    <content type="html">&lt;img src="https://live.staticflickr.com/server/22222_def_b.jpg" alt="City Night"/&gt;</content>
  </entry>
</feed>"""


def test_full_flow():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        indexer = Indexer.__new__(Indexer)
        indexer.store = store
        indexer.model = MagicMock()

        # Parse the feed
        entries = indexer.parse_feed(SAMPLE_RSS)
        assert len(entries) == 2

        # Mock image description
        def fake_describe(url):
            if "11111" in url:
                return "Snow-capped mountains under a clear blue sky with pine trees in the foreground"
            return "City skyline at night with illuminated skyscrapers reflecting on water"

        indexer._describe_image = fake_describe

        # Index
        result = indexer.index_entries(entries)
        assert result["indexed"] == 2
        assert result["skipped"] == 0

        # Search
        mountain_results = store.search("snowy mountains", n_results=5)
        assert len(mountain_results) > 0
        assert mountain_results[0]["id"] == "11111"

        city_results = store.search("urban night skyline", n_results=5)
        assert len(city_results) > 0
        assert city_results[0]["id"] == "22222"

        # Re-index should skip
        result2 = indexer.index_entries(entries)
        assert result2["skipped"] == 2
        assert result2["indexed"] == 0
