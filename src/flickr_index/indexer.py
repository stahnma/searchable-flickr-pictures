import base64
import json
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import feedparser

from flickr_index.store import PhotoStore

OLLAMA_URL = "http://localhost:11434"


class Indexer:
    def __init__(self, store: PhotoStore, model: str = "moondream", ollama_url: str = OLLAMA_URL):
        self.store = store
        self.model = model
        self.ollama_url = ollama_url

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
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        payload = json.dumps({
            "model": self.model,
            "prompt": "Describe this image in detail for use as alt-text and search indexing.",
            "images": [image_b64],
            "stream": False,
        }).encode("utf-8")
        req = Request(
            f"{self.ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["response"]

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
