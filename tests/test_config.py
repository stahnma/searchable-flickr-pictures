import os
from flickr_index.config import Settings


def test_default_settings(monkeypatch):
    monkeypatch.delenv("FLICKR_FEED_URL", raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)
    settings = Settings()
    assert settings.data_dir == "./data/chromadb"
    assert settings.flickr_feed_url is None


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("FLICKR_FEED_URL", "https://example.com/feed")
    monkeypatch.setenv("DATA_DIR", "/tmp/testdb")
    settings = Settings()
    assert settings.flickr_feed_url == "https://example.com/feed"
    assert settings.data_dir == "/tmp/testdb"
