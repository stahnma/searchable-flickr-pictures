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
@click.option("--feed-url", default=None, help="Flickr RSS feed URL (or set FLICKR_FEED_URL)")
@click.option("--data-dir", default=None, help="ChromaDB data directory")
def index(feed_url: str | None, data_dir: str | None):
    """Index photos from a Flickr RSS feed."""
    settings = Settings()
    url = feed_url or settings.flickr_feed_url
    if not url:
        raise click.UsageError("No feed URL provided. Pass --feed-url or set FLICKR_FEED_URL in .env")
    store = PhotoStore(persist_dir=data_dir or settings.data_dir)

    from flickr_index.indexer import Indexer

    indexer = Indexer(store=store)
    result = indexer.run(url)
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
