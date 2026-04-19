"""Admin analytics aggregations over users, content, interactions."""
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def overview(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        d7 = now - timedelta(days=7)

        users_total = (await self.s.execute(text("SELECT COUNT(*) FROM users"))).scalar_one()
        users_active_7d = (await self.s.execute(text(
            "SELECT COUNT(DISTINCT user_id) FROM interactions WHERE created_at > :d"
        ), {"d": d7})).scalar_one()
        content_total = (await self.s.execute(text("SELECT COUNT(*) FROM content WHERE is_active"))).scalar_one()
        events_total = (await self.s.execute(text("SELECT COUNT(*) FROM interactions"))).scalar_one()
        events_7d = (await self.s.execute(text(
            "SELECT COUNT(*) FROM interactions WHERE created_at > :d"
        ), {"d": d7})).scalar_one()

        feedback_total = (await self.s.execute(text("SELECT COUNT(*) FROM rec_feedback"))).scalar_one()
        feedback_pos = (await self.s.execute(text(
            "SELECT COUNT(*) FROM rec_feedback WHERE feedback = 1"
        ))).scalar_one()
        feedback_neg = (await self.s.execute(text(
            "SELECT COUNT(*) FROM rec_feedback WHERE feedback = -1"
        ))).scalar_one()

        completion_avg = (await self.s.execute(text(
            "SELECT COALESCE(AVG(completion_rate), 0) FROM content"
        ))).scalar_one()

        return {
            "generated_at": now.isoformat(),
            "users": {"total": int(users_total), "active_7d": int(users_active_7d)},
            "content": {"total": int(content_total)},
            "events": {"total": int(events_total), "last_7d": int(events_7d)},
            "feedback": {
                "total": int(feedback_total),
                "positive": int(feedback_pos),
                "negative": int(feedback_neg),
                "positive_rate": (float(feedback_pos) / float(feedback_total)) if feedback_total else 0,
            },
            "catalog": {"avg_completion_rate": float(completion_avg)},
        }

    async def top_content(self, limit: int = 10) -> list[dict]:
        rows = (await self.s.execute(text("""
            SELECT c.id, c.title, c.type, c.release_year, c.popularity_score,
                   COUNT(i.id) FILTER (WHERE i.event_type IN ('play','complete')) AS plays,
                   COUNT(i.id) FILTER (WHERE i.event_type = 'like') AS likes
            FROM content c LEFT JOIN interactions i ON i.content_id = c.id
            WHERE c.is_active = true
            GROUP BY c.id
            ORDER BY plays DESC, likes DESC, c.popularity_score DESC
            LIMIT :limit
        """), {"limit": limit})).mappings().all()
        return [{**r, "id": str(r["id"])} for r in rows]

    async def events_timeseries(self, days: int = 14) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (await self.s.execute(text("""
            SELECT date_trunc('day', created_at) AS day, event_type, COUNT(*) AS n
            FROM interactions WHERE created_at > :since
            GROUP BY day, event_type ORDER BY day ASC
        """), {"since": since})).mappings().all()
        out: dict[str, dict] = {}
        for r in rows:
            key = r["day"].isoformat()
            out.setdefault(key, {"day": key})[r["event_type"]] = int(r["n"])
        return list(out.values())

    async def top_genres(self, limit: int = 10) -> list[dict]:
        rows = (await self.s.execute(text("""
            SELECT g.name, COUNT(i.id) AS events
            FROM interactions i
            JOIN content c ON c.id = i.content_id
            JOIN genres g ON g.id = ANY(c.genre_ids)
            WHERE i.event_type IN ('play','complete','like')
            GROUP BY g.name
            ORDER BY events DESC
            LIMIT :limit
        """), {"limit": limit})).mappings().all()
        return [{"genre": r["name"], "events": int(r["events"])} for r in rows]
