import os
from dataclasses import dataclass


@dataclass
class Settings:
    flickr_feed_url: str | None = None
    data_dir: str = "./data/chromadb"

    def __post_init__(self):
        self.flickr_feed_url = os.environ.get("FLICKR_FEED_URL", self.flickr_feed_url)
        self.data_dir = os.environ.get("DATA_DIR", self.data_dir)
