import uuid
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.dna_snapshot import UserDNASnapshot
from models.user import User


VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


class DNASnapshotService:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def snapshot_user(self, user_id: uuid.UUID) -> UserDNASnapshot | None:
        u = (await self.s.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if u is None:
            return None
        today = date.today()
        existing = (await self.s.execute(select(UserDNASnapshot).where(
            UserDNASnapshot.user_id == user_id,
            UserDNASnapshot.snapshot_date == today,
        ))).scalar_one_or_none()
        values = {f"dna_{d}": float(getattr(u, f"dna_{d}")) for d in VIBE_DIMS}
        values["samples"] = int(u.dna_samples)
        if existing is None:
            snap = UserDNASnapshot(user_id=user_id, snapshot_date=today, **values)
            self.s.add(snap)
            await self.s.commit()
            await self.s.refresh(snap)
            return snap
        for k, v in values.items():
            setattr(existing, k, v)
        await self.s.commit()
        return existing

    async def timeline(self, user_id: uuid.UUID, days: int = 90) -> list[dict]:
        since = date.today() - timedelta(days=days)
        res = await self.s.execute(
            select(UserDNASnapshot)
            .where(UserDNASnapshot.user_id == user_id, UserDNASnapshot.snapshot_date >= since)
            .order_by(UserDNASnapshot.snapshot_date.asc())
        )
        rows = list(res.scalars().all())
        return [
            {
                "date": r.snapshot_date.isoformat(),
                "samples": r.samples,
                **{d: float(getattr(r, f"dna_{d}")) for d in VIBE_DIMS},
            }
            for r in rows
        ]

    async def snapshot_all(self) -> int:
        res = await self.s.execute(text("SELECT id FROM users WHERE dna_samples > 0"))
        ids = [r[0] for r in res]
        count = 0
        for uid in ids:
            await self.snapshot_user(uid)
            count += 1
        return count
