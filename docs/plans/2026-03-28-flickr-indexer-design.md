# Flickr Photo Indexer — Design

## Problem

Given a Flickr Pro photostream, make photos searchable by AI-generated descriptions. Photos on Flickr often lack good alt-text or descriptions, making it hard to find specific images by content.

## Solution

A Python tool that:

1. Fetches photos from a Flickr RSS feed
2. Generates descriptions using Moondream (local vision model)
3. Stores descriptions and vector embeddings in ChromaDB
4. Exposes semantic search via a REST API and CLI

## Architecture

```
Flickr RSS Feed
    → Indexer
        → Download image
        → Moondream (local) → description text
        → ChromaDB (embed + store)

Search query
    → FastAPI / CLI
        → ChromaDB semantic search
        → Return matching photos with descriptions
```

Single process. ChromaDB runs embedded (no separate server). Moondream runs locally via its Python SDK.

## Stack

| Layer | Technology | Installed via |
|-------|-----------|---------------|
| Runtime | Python 3.12 | Flox |
| API framework | FastAPI + uvicorn | Flox |
| Vector database | ChromaDB (embedded) | Flox |
| RSS parsing | feedparser | Flox |
| Package manager | uv | Flox |
| Vision model | Moondream | uv |
| CLI framework | click | uv |

## API Endpoints

```
POST /index          — Trigger incremental index run
GET  /search?q=...   — Semantic search across descriptions
GET  /photos         — List all indexed photos (paginated)
GET  /photos/{id}    — Single photo details
GET  /health         — Health check
```

## CLI Commands

```
flickr-index serve                        — Start the API server
flickr-index index --feed-url <url>       — Trigger indexing
flickr-index search "query text"          — Search from terminal
```

## Data Model (ChromaDB)

Each photo is stored as a ChromaDB document:

- **Document:** AI-generated description (embedded and searched)
- **ID:** Flickr photo ID
- **Metadata:**
  - `title` — original Flickr title
  - `flickr_url` — link to photo on Flickr
  - `image_url` — direct image URL
  - `published` — date from RSS feed
  - `indexed_at` — when we processed it

ChromaDB embeds descriptions automatically using its default model (all-MiniLM-L6-v2). Data persists to `./data/chromadb/`.

## Incremental Indexing

Before processing a photo, check if its Flickr photo ID already exists in ChromaDB. If it does, skip it. This avoids reprocessing and duplicate API/compute costs.

## Project Structure

```
flickr-project/
├── .flox/                  # Flox environment
├── pyproject.toml          # uv project config
├── src/
│   └── flickr_index/
│       ├── __init__.py
│       ├── main.py         # FastAPI app + endpoints
│       ├── indexer.py       # RSS fetching, image download, Moondream captioning
│       ├── store.py         # ChromaDB wrapper (add, search, list)
│       └── config.py        # Settings (feed URL, data dir, etc.)
├── data/
│   └── chromadb/           # Persistent storage (gitignored)
└── .gitignore
```

## Configuration

Via environment variables or `.env` file:

- `FLICKR_FEED_URL` — RSS feed URL for the target photostream
- `DATA_DIR` — path to ChromaDB storage (default: `./data/chromadb`)

## Future Upgrades

- Flickr API key support (full photostream access, not just recent RSS items)
- Swappable vision providers (Claude API, OpenAI, Moondream cloud)
- Web UI frontend
