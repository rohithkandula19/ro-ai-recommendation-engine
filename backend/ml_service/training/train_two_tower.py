"""Train a two-tower model with BPR loss.

Usage:
    python training/train_two_tower.py --interactions-path data/interactions.parquet --output-path artifacts/two_tower
"""
import argparse
import os
import random

import pandas as pd
import torch
import torch.nn.functional as F
from loguru import logger
from torch.utils.data import DataLoader, Dataset

from core.config import settings
from models.two_tower import TwoTower


class BPRDataset(Dataset):
    def __init__(self, pairs: list[tuple[int, int]], n_items: int, user_items: dict[int, set[int]]):
        self.pairs = pairs
        self.n_items = n_items
        self.user_items = user_items

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        u, i_pos = self.pairs[idx]
        seen = self.user_items.get(u, set())
        while True:
            i_neg = random.randrange(self.n_items)
            if i_neg not in seen:
                break
        return u, i_pos, i_neg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactions-path", default="data/interactions.parquet")
    parser.add_argument("--output-path", default=os.path.join(settings.ARTIFACTS_DIR, "two_tower"))
    parser.add_argument("--epochs", type=int, default=settings.TWO_TOWER_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=settings.TWO_TOWER_BATCH)
    parser.add_argument("--lr", type=float, default=settings.TWO_TOWER_LR)
    args = parser.parse_args()

    df = pd.read_parquet(args.interactions_path)
    df = df[df["event_type"].isin({"play", "complete", "like"})]
    users = sorted(df["user_id"].astype(str).unique())
    items = sorted(df["content_id"].astype(str).unique())
    u2i = {u: idx for idx, u in enumerate(users)}
    it2i = {it: idx for idx, it in enumerate(items)}

    pairs = [(u2i[str(r.user_id)], it2i[str(r.content_id)]) for r in df.itertuples(index=False)]
    user_items: dict[int, set[int]] = {}
    for u, i in pairs:
        user_items.setdefault(u, set()).add(i)

    ds = BPRDataset(pairs, n_items=len(items), user_items=user_items)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True, num_workers=0)

    model = TwoTower(n_users=len(users), n_items=len(items), emb_dim=128, out_dim=settings.TWO_TOWER_DIM)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    model.train()
    for epoch in range(args.epochs):
        total = 0.0
        count = 0
        for u, i_pos, i_neg in dl:
            opt.zero_grad()
            pos = model(u.long(), i_pos.long())
            neg = model(u.long(), i_neg.long())
            loss = -F.logsigmoid(pos - neg).mean()
            loss.backward()
            opt.step()
            total += float(loss.item()) * u.size(0)
            count += u.size(0)
        logger.info(f"epoch {epoch+1}/{args.epochs} bpr_loss={total/max(count,1):.4f}")

    model.save(args.output_path, u2i, it2i)
    try:
        model.export_scripted(os.path.join(args.output_path, "two_tower_scripted.pt"))
    except Exception as e:
        logger.warning(f"TorchScript export skipped: {e}")
    logger.info(f"Saved two-tower to {args.output_path}")


if __name__ == "__main__":
    main()
