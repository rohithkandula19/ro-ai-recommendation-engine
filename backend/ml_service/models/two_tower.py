import os
import pickle
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


class UserTower(nn.Module):
    def __init__(self, n_users: int, emb_dim: int = 128, out_dim: int = 32):
        super().__init__()
        self.emb = nn.Embedding(n_users, emb_dim)
        self.fc1 = nn.Linear(emb_dim, 64)
        self.fc2 = nn.Linear(64, out_dim)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        x = self.emb(u)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class ItemTower(nn.Module):
    def __init__(self, n_items: int, emb_dim: int = 128, out_dim: int = 32):
        super().__init__()
        self.emb = nn.Embedding(n_items, emb_dim)
        self.fc1 = nn.Linear(emb_dim, 64)
        self.fc2 = nn.Linear(64, out_dim)

    def forward(self, i: torch.Tensor) -> torch.Tensor:
        x = self.emb(i)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class TwoTower(nn.Module):
    def __init__(self, n_users: int, n_items: int, emb_dim: int = 128, out_dim: int = 32):
        super().__init__()
        self.user_tower = UserTower(n_users, emb_dim, out_dim)
        self.item_tower = ItemTower(n_items, emb_dim, out_dim)

    def forward(self, u: torch.Tensor, i: torch.Tensor) -> torch.Tensor:
        ue = self.user_tower(u)
        ie = self.item_tower(i)
        return (ue * ie).sum(dim=-1)

    def score(self, u: int, items: list[int]) -> list[float]:
        self.eval()
        with torch.no_grad():
            ue = self.user_tower(torch.tensor([u], dtype=torch.long))
            ie = self.item_tower(torch.tensor(items, dtype=torch.long))
            scores = (ue * ie).sum(dim=-1)
        return scores.tolist()

    def export_scripted(self, path: str) -> None:
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
        scripted = torch.jit.script(self)
        scripted.save(path)

    def save(self, dir_path: str, user_id_to_idx: dict, item_id_to_idx: dict) -> None:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), os.path.join(dir_path, "two_tower.pt"))
        with open(os.path.join(dir_path, "mappings.pkl"), "wb") as f:
            pickle.dump({"user_id_to_idx": user_id_to_idx, "item_id_to_idx": item_id_to_idx}, f)
