# Flickr Photo Indexer

Index your Flickr photos with AI-generated descriptions and search them semantically.

Uses [Moondream](https://github.com/vikhyat/moondream) via [Ollama](https://ollama.com) (local vision model) to automatically describe each photo, then stores descriptions in [ChromaDB](https://www.trychroma.com/) for vector-based semantic search. No API keys or cloud services required — everything runs locally.

## Quickstart

```bash
# 1. Activate the environment (installs all dependencies)
flox activate

# 2. Pull the vision model (~1.7GB, one-time download)
ollama pull moondream

# 3. Start Ollama and the API server
flox services start

# 4. Set your Flickr feed URL (find your ID at webfx.com/tools/idgettr)
echo 'FLICKR_FEED_URL=https://api.flickr.com/services/feeds/photos_public.gne?id=YOUR_FLICKR_ID&format=atom' > .env

# 5. Index your photos
flickr-index index

# 6. Search!
flickr-index search "sunset over mountains"
```

## Prerequisites

- [Flox](https://flox.dev) (manages Python, Ollama, ChromaDB, and all other dependencies)

## Setup

```bash
flox activate
```

This installs Python 3.12, Ollama, ChromaDB, FastAPI, and other dependencies via Flox, then creates a virtual environment and installs the remaining Python packages (Click) via uv.

Before first use, pull the Moondream model:

```bash
ollama pull moondream
```

## Services

The Flox environment defines two services:

| Service | Description |
|---------|-------------|
| `ollama` | Ollama model server (required for indexing) |
| `api` | FastAPI server at `http://127.0.0.1:8000` |

```bash
# Start both services
flox services start

# Or start individually
flox services start ollama
flox services start api

# Check status
flox services status

# Activate and start services in one step
flox activate --start-services
```

## Usage

### Index photos from a Flickr RSS feed

```bash
flickr-index index
```

Reads `FLICKR_FEED_URL` from `.env`. You can also pass it directly:

```bash
flickr-index index --feed-url "https://api.flickr.com/services/feeds/photos_public.gne?id=YOUR_FLICKR_ID&format=atom"
```

Indexing is incremental — only new photos are processed on each run.

### Search your photos

```bash
flickr-index search "sunset over mountains"
```

Searches are semantic, not keyword-based. A query like "golden hour beach" will match a photo described as "warm sunlight casting long shadows over sandy shoreline."

### Start the API server manually

```bash
flickr-index serve
```

Runs a FastAPI server at `http://127.0.0.1:8000` with auto-generated docs at `/docs`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/search?q=...` | Semantic search |
| `GET` | `/photos` | List all indexed photos |
| `GET` | `/photos/{id}` | Get a single photo |
| `POST` | `/index?feed_url=...` | Trigger indexing |

## Configuration

Set via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLICKR_FEED_URL` | — | Default RSS feed URL (avoids passing `--feed-url` each time) |
| `DATA_DIR` | `./data/chromadb` | ChromaDB storage location |

## Finding your Flickr ID

Your Flickr ID (e.g., `12345678@N00`) is not the same as your username or URL path. For example, `https://flickr.com/photos/jwfc/` uses the alias `jwfc`, but the actual Flickr ID is something like `30378931@N00`.

To find your numeric ID:

1. Go to [idGettr](https://www.webfx.com/tools/idgettr/)
2. Paste your Flickr profile URL (e.g., `https://flickr.com/photos/yourname/`)
3. The tool returns your numeric Flickr ID
4. Use that ID in your feed URL:
   ```
   https://api.flickr.com/services/feeds/photos_public.gne?id=YOUR_FLICKR_ID&format=atom
   ```

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
  indexer.py   — RSS feed parsing + Ollama/Moondream image captioning
  main.py      — FastAPI REST API
  cli.py       — Command-line interface (serve, index, search)
```
