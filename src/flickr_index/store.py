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
