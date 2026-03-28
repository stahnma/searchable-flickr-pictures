import tempfile
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from flickr_index.cli import cli
from flickr_index.store import PhotoStore


def test_search_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PhotoStore(persist_dir=tmpdir)
        store.add(photo_id="1", description="A cat sleeping on a bookshelf", metadata={"title": "Sleepy Cat", "flickr_url": "https://flickr.com/1", "image_url": "https://example.com/1.jpg", "published": "2026-03-01", "indexed_at": "2026-03-28"})

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "cat", "--data-dir", tmpdir])
        assert result.exit_code == 0
        assert "Sleepy Cat" in result.output or "cat" in result.output.lower()


def test_serve_command_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "serve" in result.output.lower() or "host" in result.output.lower()
