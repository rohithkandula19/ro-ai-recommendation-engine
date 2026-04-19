"""Train LightGBM LTR ranker from feature parquet.

Expects a parquet with columns: user_id, content_id, label (relevance 0..3),
and feature columns matching FEATURE_NAMES.

Usage:
    python training/train_ranker.py --features-path data/ranker_features.parquet --output-path artifacts/ranker/ltr.txt
"""
import argparse
import os

import numpy as np
import pandas as pd
from loguru import logger

from core.config import settings
from models.ranking_model import FEATURE_NAMES, LtrRanker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-path", default="data/ranker_features.parquet")
    parser.add_argument("--output-path", default=os.path.join(settings.ARTIFACTS_DIR, "ranker", "ltr.txt"))
    args = parser.parse_args()

    df = pd.read_parquet(args.features_path)
    df = df.sort_values("user_id").reset_index(drop=True)
    groups = df.groupby("user_id", sort=False).size().tolist()
    X = df[FEATURE_NAMES].to_numpy(dtype=np.float32)
    y = df["label"].to_numpy(dtype=np.float32)

    ranker = LtrRanker()
    ranker.fit(X, y, groups=groups, num_boost_round=200)
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    ranker.save(args.output_path)
    logger.info(f"Saved LTR model to {args.output_path}")


if __name__ == "__main__":
    main()
