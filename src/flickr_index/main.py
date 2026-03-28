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
