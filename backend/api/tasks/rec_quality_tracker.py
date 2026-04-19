"""Event → rec_quality_daily aggregator.

Called from events.ingest + content.feedback hooks to bucket by surface+day.
"""
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


EVENT_COLUMNS = {
    "click": "clicks",
    "play": "plays",
    "complete": "completes",
    "like": "likes",
    "dislike": "dislikes",
}


async def track(session: AsyncSession, event_type: str, surface: str | None) -> None:
    col = EVENT_COLUMNS.get(event_type)
    if not col or not surface:
        return
    today = date.today()
    await session.execute(text(f"""
        INSERT INTO rec_quality_daily (day, surface, {col}) VALUES (:d, :s, 1)
        ON CONFLICT (day, surface) DO UPDATE SET {col} = rec_quality_daily.{col} + 1
    """), {"d": today, "s": surface})


async def track_impression(session: AsyncSession, surface: str, count: int) -> None:
    today = date.today()
    await session.execute(text("""
        INSERT INTO rec_quality_daily (day, surface, impressions) VALUES (:d, :s, :n)
        ON CONFLICT (day, surface) DO UPDATE SET impressions = rec_quality_daily.impressions + :n
    """), {"d": today, "s": surface, "n": count})
