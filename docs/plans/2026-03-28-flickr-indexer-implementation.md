# Flickr Photo Indexer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a tool that indexes Flickr photos with AI-generated descriptions and makes them semantically searchable.

**Architecture:** Single Python process with embedded ChromaDB for vector storage. Moondream runs locally for image captioning. FastAPI serves the REST API. Click provides the CLI. RSS feed is the photo source.

**Tech Stack:** Python 3.12, FastAPI, ChromaDB, Moondream, feedparser, click, uvicorn — managed by Flox + uv.

---

### Task 1: Flox Environment Setup

**Files:**
- Create: `.flox/env/manifest.toml` (via `flox init` + `flox install`)

**Step 1: Initialize Flox environment**

Run:
```bash
cd /Users/stahnma/development/personal/flickr-project
flox init
```
Expected: `.flox/` directory created

**Step 2: Install Flox packages**

Run:
```bash
flox install python312 python312Packages.chromadb python312Packages.fastapi python312Packages.uvicorn python312Packages.feedparser uv
```
Expected: All packages installed successfully

**Step 3: Verify installations**

Run:
```bash
flox activate -- python3 --version
flox activate -- python3 -c "import chromadb; print(chromadb.__version__)"
flox activate -- python3 -c "import fastapi; print(fastapi.__version__)"
flox activate -- python3 -c "import feedparser; print(feedparser.__version__)"
flox activate -- uv --version
```
Expected: All commands succeed with version output

**Step 4: Commit**

```bash
git add .flox
git commit -m "feat: initialize Flox environment with Python, ChromaDB, FastAPI, feedparser, uv"
```

---

### Task 2: uv Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/flickr_index/__init__.py`

**Step 1: Initialize uv project**

Run (inside `flox activate`):
```bash
uv init --lib --name flickr-index --package
```

Then edit `pyproject.toml` to have this content:

```toml
[project]
name = "flickr-index"
version = "0.1.0"
description = "Index Flickr photos with AI-generated descriptions for semantic search"
requires-python = ">=3.12"
dependencies = [
    "moondream>=0.0.1",
    "click>=8.0",
]

[project.scripts]
flickr-index = "flickr_index.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 2: Create package init**

Create `src/flickr_index/__init__.py`:
```python
"""Flickr photo indexer with AI-generated descriptions and semantic search."""
```

**Step 3: Install dependencies**

Run:
```bash
uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e .
```
Expected: moondream and click installed

**Step 4: Verify moondream import**

Run:
```bash
python3 -c "import moondream; print('moondream OK')"
```
Expected: `moondream OK`

**Step 5: Commit**

```bash
git add pyproject.toml src/flickr_index/__init__.py uv.lock .python-version
git commit -m "feat: set up uv project with moondream and click dependencies"
```

---

### Task 3: Config Module

**Files:**
- Create: `src/flickr_index/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

Create `tests/test_config.py`:
```python
import os
from flickr_index.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.data_dir == "./data/chromadb"
    assert settings.flickr_feed_url is None


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("FLICKR_FEED_URL", "https://example.com/feed")
    monkeypatch.setenv("DATA_DIR", "/tmp/testdb")
    settings = Settings()
    assert settings.flickr_feed_url == "https://example.com/feed"
    assert settings.data_dir == "/tmp/testdb"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

**Step 3: Write minimal implementation**

Create `src/flickr_index/config.py`:
```python
import os
from dataclasses import dataclass


@dataclass
class Settings:
    flickr_feed_url: str | None = None
    data_dir: str = "./data/chromadb"

    def __post_init__(self):
        self.flickr_feed_url = os.environ.get("FLICKR_FEED_URL", self.flickr_feed_url)
        self.data_dir = os.environ.get("DATA_DIR", self.data_dir)
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_config.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/flickr_index/config.py tests/test_config.py
git commit -m "feat: add config module with environment variable support"
```

---

### Task 4: ChromaDB Store Module

**Files:**
- Create: `src/flickr_index/store.py`
- Create: `tests/test_store.py`

**Step 1: Write the failing test**

Create `tests/test_store.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_store.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

Create `src/flickr_index/store.py`:
```python
import chromadb


class PhotoStore:
    def __init__(self, persist_dir: str = "./data/chromadb"):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="flickr_photos",
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, photo_id: str, description: str, metadata: dict) -> bool:
        if self.exists(photo_id):
            return False
        self._collection.add(
            ids=[photo_id],
            documents=[description],
            metadatas=[metadata],
        )
        return True

    def exists(self, photo_id: str) -> bool:
        result = self._collection.get(ids=[photo_id])
        return len(result["ids"]) > 0

    def search(self, query: str, n_results: int = 10) -> list[dict]:
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        return self._format_results(results)

    def get(self, photo_id: str) -> dict | None:
        result = self._collection.get(ids=[photo_id])
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "description": result["documents"][0],
            "metadata": result["metadatas"][0],
        }

    def list_all(self) -> list[dict]:
        result = self._collection.get()
        return [
            {
                "id": result["ids"][i],
                "description": result["documents"][i],
                "metadata": result["metadatas"][i],
            }
            for i in range(len(result["ids"]))
        ]

    def _format_results(self, results: dict) -> list[dict]:
        if not results["ids"] or not results["ids"][0]:
            return []
        return [
            {
                "id": results["ids"][0][i],
                "description": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_store.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add src/flickr_index/store.py tests/test_store.py
git commit -m "feat: add ChromaDB store module with add, search, list, get operations"
```

---

### Task 5: Indexer Module (RSS + Moondream)

**Files:**
- Create: `src/flickr_index/indexer.py`
- Create: `tests/test_indexer.py`

**Step 1: Write the failing test**

Create `tests/test_indexer.py`:
```python
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
        indexer.model = MagicMock()

        entries = [{"photo_id": "12345", "title": "Test", "flickr_url": "http://example.com", "image_url": "http://example.com/img.jpg", "published": "2026-03-01"}]
        result = indexer.index_entries(entries)
        assert result["skipped"] == 1
        assert result["indexed"] == 0
        indexer.model.caption.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_indexer.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

Create `src/flickr_index/indexer.py`:
```python
import re
from datetime import datetime, timezone
from io import BytesIO
from urllib.request import urlopen

import feedparser
import moondream as md
from PIL import Image

from flickr_index.store import PhotoStore


class Indexer:
    def __init__(self, store: PhotoStore, model_name: str = "vikhyat/moondream2"):
        self.store = store
        self.model = md.vl(model=model_name)

    def fetch_feed(self, feed_url: str) -> str:
        with urlopen(feed_url) as response:
            return response.read().decode("utf-8")

    def parse_feed(self, feed_content: str) -> list[dict]:
        parsed = feedparser.parse(feed_content)
        entries = []
        for entry in parsed.entries:
            photo_id = self._extract_photo_id(entry)
            if not photo_id:
                continue
            image_url = self._extract_image_url(entry)
            if not image_url:
                continue
            entries.append({
                "photo_id": photo_id,
                "title": entry.get("title", ""),
                "flickr_url": entry.get("link", ""),
                "image_url": image_url,
                "published": entry.get("published", ""),
            })
        return entries

    def index_entries(self, entries: list[dict]) -> dict:
        indexed = 0
        skipped = 0
        errors = 0
        for entry in entries:
            if self.store.exists(entry["photo_id"]):
                skipped += 1
                continue
            try:
                description = self._describe_image(entry["image_url"])
                self.store.add(
                    photo_id=entry["photo_id"],
                    description=description,
                    metadata={
                        "title": entry["title"],
                        "flickr_url": entry["flickr_url"],
                        "image_url": entry["image_url"],
                        "published": entry["published"],
                        "indexed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                indexed += 1
            except Exception as e:
                print(f"Error indexing {entry['photo_id']}: {e}")
                errors += 1
        return {"indexed": indexed, "skipped": skipped, "errors": errors}

    def run(self, feed_url: str) -> dict:
        feed_content = self.fetch_feed(feed_url)
        entries = self.parse_feed(feed_content)
        return self.index_entries(entries)

    def _describe_image(self, image_url: str) -> str:
        with urlopen(image_url) as response:
            image_data = response.read()
        image = Image.open(BytesIO(image_data))
        encoded = self.model.encode_image(image)
        caption = self.model.caption(encoded)["caption"]
        return caption

    def _extract_photo_id(self, entry) -> str | None:
        # Try the Atom ID field: tag:flickr.com,2005:/photo/12345
        entry_id = entry.get("id", "")
        match = re.search(r"/photo/(\d+)", entry_id)
        if match:
            return match.group(1)
        # Try the link URL
        link = entry.get("link", "")
        match = re.search(r"/photos/[^/]+/(\d+)", link)
        if match:
            return match.group(1)
        return None

    def _extract_image_url(self, entry) -> str | None:
        content = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")
        match = re.search(r'src="(https://[^"]+\.jpg)"', content)
        if match:
            return match.group(1)
        return None
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_indexer.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/flickr_index/indexer.py tests/test_indexer.py
git commit -m "feat: add indexer module with RSS parsing and Moondream captioning"
```

---

### Task 6: FastAPI Application

**Files:**
- Create: `src/flickr_index/main.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing test**

Create `tests/test_main.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_main.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

Create `src/flickr_index/main.py`:
```python
from fastapi import FastAPI, HTTPException, Query

from flickr_index.config import Settings
from flickr_index.store import PhotoStore


def create_app(data_dir: str | None = None) -> FastAPI:
    app = FastAPI(title="Flickr Photo Indexer")

    settings = Settings()
    store = PhotoStore(persist_dir=data_dir or settings.data_dir)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/search")
    def search(q: str = Query(..., description="Search query")):
        results = store.search(q)
        return {"query": q, "results": results}

    @app.get("/photos")
    def list_photos():
        photos = store.list_all()
        return {"photos": photos}

    @app.get("/photos/{photo_id}")
    def get_photo(photo_id: str):
        photo = store.get(photo_id)
        if photo is None:
            raise HTTPException(status_code=404, detail="Photo not found")
        return photo

    @app.post("/index")
    def index(feed_url: str = Query(None)):
        from flickr_index.indexer import Indexer

        url = feed_url or settings.flickr_feed_url
        if not url:
            raise HTTPException(status_code=400, detail="No feed URL provided. Pass feed_url param or set FLICKR_FEED_URL.")
        indexer = Indexer(store=store)
        result = indexer.run(url)
        return result

    return app


app = create_app()
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_main.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add src/flickr_index/main.py tests/test_main.py
git commit -m "feat: add FastAPI application with search, list, get, index endpoints"
```

---

### Task 7: CLI Module

**Files:**
- Create: `src/flickr_index/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

Create `tests/test_cli.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

Create `src/flickr_index/cli.py`:
```python
import click
import uvicorn

from flickr_index.config import Settings
from flickr_index.store import PhotoStore


@click.group()
def cli():
    """Flickr Photo Indexer — search your photos by AI-generated descriptions."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
def serve(host: str, port: int):
    """Start the API server."""
    uvicorn.run("flickr_index.main:app", host=host, port=port, reload=True)


@cli.command()
@click.option("--feed-url", required=True, help="Flickr RSS feed URL")
@click.option("--data-dir", default=None, help="ChromaDB data directory")
def index(feed_url: str, data_dir: str | None):
    """Index photos from a Flickr RSS feed."""
    settings = Settings()
    store = PhotoStore(persist_dir=data_dir or settings.data_dir)

    from flickr_index.indexer import Indexer

    indexer = Indexer(store=store)
    result = indexer.run(feed_url)
    click.echo(f"Indexed: {result['indexed']}, Skipped: {result['skipped']}, Errors: {result['errors']}")


@cli.command()
@click.argument("query")
@click.option("--data-dir", default=None, help="ChromaDB data directory")
@click.option("--limit", default=10, help="Max results")
def search(query: str, data_dir: str | None, limit: int):
    """Search indexed photos by description."""
    settings = Settings()
    store = PhotoStore(persist_dir=data_dir or settings.data_dir)
    results = store.search(query, n_results=limit)
    if not results:
        click.echo("No results found.")
        return
    for r in results:
        title = r["metadata"].get("title", "Untitled")
        url = r["metadata"].get("flickr_url", "")
        click.echo(f"  [{r['id']}] {title}")
        click.echo(f"    {r['description']}")
        click.echo(f"    {url}")
        click.echo()
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/flickr_index/cli.py tests/test_cli.py
git commit -m "feat: add CLI with serve, index, and search commands"
```

---

### Task 8: Integration Test (End-to-End)

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

Create `tests/test_integration.py`:
```python
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
```

**Step 2: Run test**

Run: `python3 -m pytest tests/test_integration.py -v`
Expected: 1 passed

**Step 3: Run full test suite**

Run: `python3 -m pytest tests/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add integration test for full index-and-search flow"
```

---

### Task 9: Final Wiring & Smoke Test

**Step 1: Verify CLI entry point**

Run:
```bash
flickr-index --help
```
Expected: Shows group help with `serve`, `index`, `search` commands

**Step 2: Start API server**

Run:
```bash
flickr-index serve &
curl http://127.0.0.1:8000/health
kill %1
```
Expected: `{"status":"ok"}`

**Step 3: Run full test suite one more time**

Run: `python3 -m pytest tests/ -v`
Expected: All tests pass

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final wiring and verification"
```
