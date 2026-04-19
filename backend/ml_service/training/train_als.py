"""Train ALS model from interactions parquet.

Usage:
    python training/train_als.py --interactions-path data/interactions.parquet --output-path artifacts/als
"""
import argparse
import os

import pandas as pd
from loguru import logger

from core.config import settings
from models.als_model import ALSRecommender


CONFIDENCE_WEIGHT = {
    "complete": 3.0,
    "like": 2.0,
    "play": 1.0,
    "click": 0.3,
    "add_to_list": 1.5,
    "rate": 2.0,
    "dislike": -1.0,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactions-path", default="data/interactions.parquet")
    parser.add_argument("--output-path", default=os.path.join(settings.ARTIFACTS_DIR, "als"))
    args = parser.parse_args()

    df = pd.read_parquet(args.interactions_path)
    logger.info(f"Loaded {len(df)} interactions")
    df = df[df["event_type"].isin(CONFIDENCE_WEIGHT.keys())]
    df["confidence"] = df["event_type"].map(CONFIDENCE_WEIGHT)
    agg = df.groupby(["user_id", "content_id"], as_index=False)["confidence"].sum()
    agg = agg[agg["confidence"] > 0]

    interactions = [
        (str(r.user_id), str(r.content_id), float(r.confidence))
        for r in agg.itertuples(index=False)
    ]
    model = ALSRecommender(
        factors=settings.ALS_FACTORS,
        iterations=settings.ALS_ITERATIONS,
        regularization=settings.ALS_REGULARIZATION,
    )
    model.fit(interactions)
    model.save(args.output_path)
    logger.info(f"Saved ALS to {args.output_path}")


if __name__ == "__main__":
    main()
