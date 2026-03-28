# Flickr Photo Indexer

Index your Flickr photos with AI-generated descriptions and search them semantically.

Uses [Moondream](https://github.com/vikhyat/moondream) (a local vision model) to automatically describe each photo, then stores descriptions in [ChromaDB](https://www.trychroma.com/) for vector-based semantic search. No API keys or cloud services required.

## Prerequisites

- [Flox](https://flox.dev) (manages Python, ChromaDB, and other native dependencies)

## Setup

```bash
flox activate
```

This installs Python 3.12, ChromaDB, FastAPI, and other dependencies via Flox, then creates a virtual environment and installs the remaining Python packages (Moondream, Click) via uv.

## Usage

### Index photos from a Flickr RSS feed

```bash
flickr-index index --feed-url "https://api.flickr.com/services/feeds/photos_public.gne?id=YOUR_FLICKR_ID"
```

The first run downloads the Moondream model (~1.7GB). Subsequent runs are incremental — only new photos are processed.

### Search your photos

```bash
flickr-index search "sunset over mountains"
```

Searches are semantic, not keyword-based. A query like "golden hour beach" will match a photo described as "warm sunlight casting long shadows over sandy shoreline."

### Start the API server

```bash
flickr-index serve
```

Runs a FastAPI server at `http://127.0.0.1:8000` with auto-generated docs at `/docs`.

#### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/search?q=...` | Semantic search |
| `GET` | `/photos` | List all indexed photos |
| `GET` | `/photos/{id}` | Get a single photo |
| `POST` | `/index?feed_url=...` | Trigger indexing |

### Configuration

Set via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLICKR_FEED_URL` | — | Default RSS feed URL (avoids passing `--feed-url` each time) |
| `DATA_DIR` | `./data/chromadb` | ChromaDB storage location |

## Finding your Flickr RSS feed URL

Your public photostream feed URL follows this pattern:

```
https://api.flickr.com/services/feeds/photos_public.gne?id=YOUR_FLICKR_ID&format=atom
```

To find your Flickr ID, visit your Flickr profile — it's the number in the URL (e.g., `12345678@N00`).

## Running tests

```bash
flox activate
python -m pytest tests/ -v
```

## Project structure

```
src/flickr_index/
  config.py    — Settings from environment variables
  store.py     — ChromaDB wrapper (add, search, list, get)
  indexer.py   — RSS feed parsing + Moondream image captioning
  main.py      — FastAPI REST API
  cli.py       — Command-line interface (serve, index, search)
```
