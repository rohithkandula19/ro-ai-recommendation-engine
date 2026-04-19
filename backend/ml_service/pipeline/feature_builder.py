from datetime import datetime, timezone
from typing import Any


class FeatureBuilder:
    def build_user_features(self, user_ctx: dict[str, Any]) -> dict[str, float]:
        created = user_ctx.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                created = None
        if isinstance(created, datetime):
            age_days = (datetime.now(timezone.utc) - created).days
        else:
            age_days = 0
        return {
            "user_age_days": float(age_days),
            "watch_count": float(user_ctx.get("watch_count", 0)),
            "avg_watch_pct": float(user_ctx.get("avg_watch_pct", 0.0)),
        }

    def build_item_features(self, candidate: dict, content: dict, user_genre_prefs: set[int]) -> dict[str, float]:
        sources = candidate.get("sources", [])
        release_year = content.get("release_year") or 2000
        recency = max(0.0, 1.0 - (datetime.now().year - int(release_year)) / 30.0)
        genre_ids = set(content.get("genre_ids") or [])
        match = len(genre_ids & user_genre_prefs) / (len(genre_ids) or 1) if user_genre_prefs else 0.0
        return {
            "content_popularity": float(content.get("popularity_score", 0.0)),
            "genre_match_score": float(match),
            "release_recency": float(recency),
            "cf_score": float(candidate.get("score", 0.0)) if "cf" in sources else 0.0,
            "cb_score": float(candidate.get("score", 0.0)) if "cb" in sources else 0.0,
            "trending_score": float(candidate.get("score", 0.0)) if "trending" in sources else 0.0,
            "session_score": float(candidate.get("score", 0.0)) if "session" in sources else 0.0,
        }
