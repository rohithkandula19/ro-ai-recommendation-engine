import os
import pickle
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class ModelRegistry:
    def __init__(self, base_dir: str = "artifacts"):
        self.base_dir = base_dir
        Path(base_dir).mkdir(parents=True, exist_ok=True)

    def save(self, name: str, obj: Any) -> str:
        path = os.path.join(self.base_dir, f"{name}.pkl")
        with open(path, "wb") as f:
            pickle.dump(obj, f)
        logger.info(f"Saved model: {path}")
        return path

    def load(self, name: str) -> Optional[Any]:
        path = os.path.join(self.base_dir, f"{name}.pkl")
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)

    def exists(self, name: str) -> bool:
        return os.path.exists(os.path.join(self.base_dir, f"{name}.pkl"))
