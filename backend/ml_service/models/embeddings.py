import numpy as np
from sentence_transformers import SentenceTransformer


class TextEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        arr = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
        return arr.astype(np.float32)

    @staticmethod
    def build_text(title: str, description: str | None, genres: list[str] | None) -> str:
        parts = [title or ""]
        if description:
            parts.append(description)
        if genres:
            parts.append(" ".join(genres))
        return " ".join(parts).strip()
