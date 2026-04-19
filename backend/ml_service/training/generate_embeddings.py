"""Build content embeddings and FAISS index.

Usage:
    python training/generate_embeddings.py --content-path data/content.csv --output-path artifacts/faiss
"""
import argparse
import os

import pandas as pd
from loguru import logger

from core.config import settings
from core.faiss_index import FaissIndex
from models.embeddings import TextEmbedder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-path", default="data/content.csv")
    parser.add_argument("--output-path", default=os.path.join(settings.ARTIFACTS_DIR, "faiss"))
    args = parser.parse_args()

    df = pd.read_csv(args.content_path)
    embedder = TextEmbedder(settings.EMBED_MODEL)
    texts = []
    for r in df.itertuples(index=False):
        genres = getattr(r, "genres_joined", "") or ""
        genre_list = genres.split("|") if isinstance(genres, str) else []
        texts.append(embedder.build_text(
            getattr(r, "title", ""),
            getattr(r, "description", ""),
            genre_list,
        ))
    logger.info(f"Embedding {len(texts)} content items")
    emb = embedder.encode(texts, batch_size=32)

    ids = df["id"].astype(str).tolist()
    idx = FaissIndex(dim=emb.shape[1], nlist=settings.FAISS_NLIST, m=settings.FAISS_M)
    idx.build(emb, ids)
    idx.save(args.output_path)
    logger.info(f"Saved FAISS index to {args.output_path}")


if __name__ == "__main__":
    main()
