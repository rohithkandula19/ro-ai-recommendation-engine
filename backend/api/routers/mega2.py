"""Mega-50 endpoints — all in one router to keep the import graph tiny."""
import base64
import hashlib
import hmac
import io
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.llm import get_llm
from middleware.auth_middleware import get_current_user, require_admin
from models.content import Content
from models.user import User

router = APIRouter(tags=["mega2"])
VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


# ─── 2FA (TOTP) ──────────────────────────────────────────
def _totp_code(secret: str, for_ts: int | None = None) -> str:
    import time, struct
    ts = for_ts or int(time.time())
    counter = ts // 30
    key = base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8))
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (int.from_bytes(h[offset:offset + 4], "big") & 0x7fffffff) % 1000000
    return f"{code:06d}"


@router.post("/auth/2fa/setup")
async def two_fa_setup(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
    await db.execute(text("UPDATE users SET totp_secret=:s, totp_verified=false WHERE id=:u"),
                     {"s": secret, "u": str(user.id)})
    await db.commit()
    uri = f"otpauth://totp/RO:{user.email}?secret={secret}&issuer=RO"
    return {"secret": secret, "otpauth_uri": uri}


class TwoFAVerifyIn(BaseModel):
    code: str = Field(min_length=6, max_length=6)


@router.post("/auth/2fa/verify")
async def two_fa_verify(
    body: TwoFAVerifyIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("SELECT totp_secret FROM users WHERE id=:u"), {"u": str(user.id)})).first()
    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="2FA not initialized")
    import time
    now = int(time.time())
    for offset in (-30, 0, 30):
        if _totp_code(row[0], now + offset) == body.code:
            await db.execute(text("UPDATE users SET totp_verified=true WHERE id=:u"), {"u": str(user.id)})
            await db.commit()
            return {"status": "ok"}
    raise HTTPException(status_code=400, detail="invalid code")


# ─── SSO (Google/GitHub — stub that exchanges an id_token) ─
class SSOIn(BaseModel):
    provider: str  # google | github
    access_token: str


@router.post("/auth/sso")
async def sso(body: SSOIn, db: Annotated[AsyncSession, Depends(get_db)]):
    from core.security import create_access_token, create_refresh_token
    from core.redis import get_redis
    email = None
    sub = None
    name = None
    async with httpx.AsyncClient(timeout=6.0) as client:
        if body.provider == "google":
            r = await client.get("https://www.googleapis.com/oauth2/v3/userinfo",
                                 headers={"Authorization": f"Bearer {body.access_token}"})
            if r.status_code == 200:
                info = r.json()
                email = info.get("email"); sub = info.get("sub"); name = info.get("name")
        elif body.provider == "github":
            r = await client.get("https://api.github.com/user",
                                 headers={"Authorization": f"Bearer {body.access_token}"})
            if r.status_code == 200:
                info = r.json()
                sub = str(info.get("id")); name = info.get("name") or info.get("login")
                email = info.get("email")
                if not email:
                    r2 = await client.get("https://api.github.com/user/emails",
                                          headers={"Authorization": f"Bearer {body.access_token}"})
                    if r2.status_code == 200:
                        for e in r2.json():
                            if e.get("primary"):
                                email = e.get("email")
                                break
    if not (email and sub):
        raise HTTPException(status_code=401, detail="SSO failed")

    row = (await db.execute(text("SELECT id, is_admin FROM users WHERE email=:e OR (oauth_provider=:p AND oauth_sub=:s)"),
                            {"e": email, "p": body.provider, "s": sub})).first()
    if row:
        uid = str(row[0]); is_admin = bool(row[1])
    else:
        from core.security import hash_password
        uid = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO users (id, email, hashed_password, display_name, is_active, oauth_provider, oauth_sub)
            VALUES (:i, :e, :hp, :dn, true, :p, :s)
        """), {"i": uid, "e": email, "hp": hash_password(secrets.token_urlsafe(16)),
               "dn": name or email.split("@")[0], "p": body.provider, "s": sub})
        await db.execute(text("INSERT INTO user_preferences (user_id) VALUES (:u) ON CONFLICT DO NOTHING"),
                         {"u": uid})
        await db.commit()
        is_admin = False
    access = create_access_token(uid, is_admin)
    refresh = create_refresh_token(uid)
    return {"access_token": access, "refresh_token": refresh, "user_id": uid}


# ─── Streaks ─────────────────────────────────────────────
@router.get("/users/me/streak")
async def my_streak(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("SELECT * FROM user_streaks WHERE user_id=:u"),
                            {"u": str(user.id)})).mappings().first()
    if not row:
        await db.execute(text("INSERT INTO user_streaks (user_id) VALUES (:u)"), {"u": str(user.id)})
        await db.commit()
        return {"current_days": 0, "best_days": 0, "badges": []}
    return {**row, "user_id": str(row["user_id"]),
            "last_active_date": row["last_active_date"].isoformat() if row["last_active_date"] else None}


@router.post("/users/me/streak/tick")
async def tick_streak(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from datetime import date
    today = date.today()
    row = (await db.execute(text("SELECT * FROM user_streaks WHERE user_id=:u"),
                            {"u": str(user.id)})).mappings().first()
    if not row:
        await db.execute(text("""
            INSERT INTO user_streaks (user_id, current_days, best_days, last_active_date)
            VALUES (:u, 1, 1, :t)
        """), {"u": str(user.id), "t": today})
        await db.commit()
        return {"current_days": 1, "best_days": 1}
    last = row["last_active_date"]
    current = row["current_days"]
    if last == today:
        return {**row, "user_id": str(row["user_id"]),
                "last_active_date": last.isoformat() if last else None}
    if last == today - timedelta(days=1):
        current += 1
    else:
        current = 1
    best = max(current, row["best_days"])
    badges = set(row["badges"] or [])
    for milestone in (7, 30, 100):
        if current >= milestone:
            badges.add(f"streak_{milestone}")
    await db.execute(text("""
        UPDATE user_streaks SET current_days=:c, best_days=:b, last_active_date=:t, badges=:bd
        WHERE user_id=:u
    """), {"c": current, "b": best, "t": today, "bd": sorted(badges), "u": str(user.id)})
    await db.commit()
    return {"current_days": current, "best_days": best, "badges": sorted(badges)}


# ─── DMs ─────────────────────────────────────────────────
class MessageIn(BaseModel):
    recipient_id: uuid.UUID
    body: str = Field(min_length=1, max_length=2000)
    attached_content_id: uuid.UUID | None = None


@router.post("/messages")
async def send_message(
    body: MessageIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(text("""
        INSERT INTO messages (sender_id, recipient_id, body, attached_content_id)
        VALUES (:s, :r, :b, :c) RETURNING id
    """), {"s": str(user.id), "r": str(body.recipient_id), "b": body.body,
           "c": str(body.attached_content_id) if body.attached_content_id else None})
    await db.commit()
    return {"id": r.scalar_one()}


@router.get("/messages/with/{other_id}")
async def conversation(
    other_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, sender_id, recipient_id, body, attached_content_id, read, created_at
        FROM messages
        WHERE (sender_id=:u AND recipient_id=:o) OR (sender_id=:o AND recipient_id=:u)
        ORDER BY created_at ASC LIMIT 200
    """), {"u": str(user.id), "o": str(other_id)})).mappings().all()
    # mark read
    await db.execute(text(
        "UPDATE messages SET read=true WHERE recipient_id=:u AND sender_id=:o AND read=false"
    ), {"u": str(user.id), "o": str(other_id)})
    await db.commit()
    return {"items": [{**r, "sender_id": str(r["sender_id"]), "recipient_id": str(r["recipient_id"]),
                       "attached_content_id": str(r["attached_content_id"]) if r["attached_content_id"] else None,
                       "created_at": r["created_at"].isoformat()} for r in rows]}


# ─── Social activity feed ────────────────────────────────
@router.get("/users/me/feed")
async def feed(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(30, ge=1, le=100),
):
    rows = (await db.execute(text("""
        SELECT a.id, a.kind, a.metadata, a.created_at,
               u.display_name, c.title, c.thumbnail_url, c.id AS content_id
        FROM activity_feed a
        JOIN friendships f ON f.user_id = :u AND f.friend_id = a.user_id AND f.status = 'accepted'
        JOIN users u ON u.id = a.user_id
        LEFT JOIN content c ON c.id = a.content_id
        ORDER BY a.created_at DESC LIMIT :lim
    """), {"u": str(user.id), "lim": limit})).mappings().all()
    return {"items": [{**r, "content_id": str(r["content_id"]) if r["content_id"] else None,
                       "created_at": r["created_at"].isoformat()} for r in rows]}


# ─── Webhooks ────────────────────────────────────────────
class WebhookIn(BaseModel):
    url: str = Field(max_length=500)
    events: list[str] = Field(min_length=1, max_length=20)


@router.post("/webhooks")
async def create_webhook(
    body: WebhookIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    secret = secrets.token_urlsafe(24)
    r = await db.execute(text("""
        INSERT INTO webhook_subscriptions (user_id, url, events, secret)
        VALUES (:u, :url, :ev, :s) RETURNING id
    """), {"u": str(user.id), "url": body.url, "ev": body.events, "s": secret})
    await db.commit()
    return {"id": str(r.scalar_one()), "secret": secret}


@router.get("/webhooks")
async def list_webhooks(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text(
        "SELECT id, url, events, is_active, created_at FROM webhook_subscriptions WHERE user_id=:u"
    ), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"]),
                       "created_at": r["created_at"].isoformat()} for r in rows]}


# ─── Letterboxd / Trakt CSV import ───────────────────────
@router.post("/imports/csv")
async def import_csv(
    source: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import csv as csvmod
    if source not in ("letterboxd", "trakt"):
        raise HTTPException(status_code=400, detail="source must be letterboxd|trakt")
    raw = (await file.read()).decode(errors="ignore")
    reader = csvmod.DictReader(io.StringIO(raw))
    total = 0
    matched = 0
    for row in reader:
        total += 1
        title = row.get("Name") or row.get("title") or ""
        year = row.get("Year") or row.get("year")
        if not title:
            continue
        r = await db.execute(text(
            "SELECT id FROM content WHERE lower(title)=lower(:t) AND (release_year=:y OR :y IS NULL) LIMIT 1"
        ), {"t": title.strip(), "y": int(year) if year and year.isdigit() else None})
        cid = r.scalar_one_or_none()
        if cid:
            matched += 1
            await db.execute(text("""
                INSERT INTO watch_history (user_id, content_id, watch_pct, completed, last_watched_at)
                VALUES (:u, :c, 1.0, true, now()) ON CONFLICT DO NOTHING
            """), {"u": str(user.id), "c": str(cid)})
    await db.execute(text("""
        INSERT INTO import_jobs (user_id, source, status, rows_total, rows_matched)
        VALUES (:u, :s, 'done', :t, :m)
    """), {"u": str(user.id), "s": source, "t": total, "m": matched})
    await db.commit()
    return {"status": "done", "rows_total": total, "rows_matched": matched}


# ─── GDPR delete ─────────────────────────────────────────
class GDPRDelete(BaseModel):
    confirm: str


@router.post("/users/me/delete")
async def gdpr_delete(
    body: GDPRDelete,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.confirm != user.email:
        raise HTTPException(status_code=400, detail="Type your email exactly to confirm")
    await db.execute(text("DELETE FROM users WHERE id=:u"), {"u": str(user.id)})
    await db.commit()
    return {"status": "deleted"}


# ─── Public profile ──────────────────────────────────────
@router.get("/u/{email}")
async def public_profile(
    email: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("""
        SELECT id, email, display_name, dna_samples,
               dna_pace, dna_emotion, dna_darkness, dna_humor, dna_complexity, dna_spectacle
        FROM users WHERE email=:e
    """), {"e": email})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    picks = (await db.execute(text("""
        SELECT c.id, c.title, c.thumbnail_url FROM ratings r
        JOIN content c ON c.id = r.content_id
        WHERE r.user_id=:u AND r.rating >= 4
        ORDER BY r.rated_at DESC LIMIT 12
    """), {"u": str(row["id"])})).mappings().all()
    return {
        "id": str(row["id"]), "display_name": row["display_name"], "email": row["email"],
        "dna": {d: float(row[f"dna_{d}"]) for d in VIBE_DIMS},
        "samples": row["dna_samples"],
        "top_picks": [{**p, "id": str(p["id"])} for p in picks],
    }


# ─── Leaderboards ────────────────────────────────────────
@router.get("/leaderboards/{kind}")
async def leaderboards(
    kind: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    queries = {
        "top-raters": """
            SELECT u.display_name, u.email, COUNT(*) AS score
            FROM ratings r JOIN users u ON u.id = r.user_id
            GROUP BY u.id ORDER BY score DESC LIMIT 20
        """,
        "top-watchers": """
            SELECT u.display_name, u.email, COUNT(*) AS score
            FROM watch_history w JOIN users u ON u.id = w.user_id
            WHERE w.completed = true GROUP BY u.id ORDER BY score DESC LIMIT 20
        """,
        "top-reviewers": """
            SELECT u.display_name, u.email, COUNT(*) AS score
            FROM reviews r JOIN users u ON u.id = r.user_id
            GROUP BY u.id ORDER BY score DESC LIMIT 20
        """,
        "longest-streaks": """
            SELECT u.display_name, u.email, s.best_days AS score
            FROM user_streaks s JOIN users u ON u.id = s.user_id
            ORDER BY s.best_days DESC LIMIT 20
        """,
    }
    if kind not in queries:
        raise HTTPException(status_code=404, detail="unknown leaderboard")
    rows = (await db.execute(text(queries[kind]))).mappings().all()
    return {"kind": kind, "items": [dict(r) for r in rows]}


# ─── Proactive AI taste-shift notification ───────────────
@router.post("/users/me/taste-shift-check")
async def check_taste_shift(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT snapshot_date, dna_pace, dna_emotion, dna_darkness, dna_humor, dna_complexity, dna_spectacle
        FROM user_dna_snapshots WHERE user_id=:u ORDER BY snapshot_date DESC LIMIT 30
    """), {"u": str(user.id)})).mappings().all()
    if len(rows) < 2:
        return {"shift": None, "message": "not enough history"}
    recent = rows[0]; old = rows[-1]
    deltas = {d: float(recent[f"dna_{d}"]) - float(old[f"dna_{d}"]) for d in VIBE_DIMS}
    top_axis, top_delta = max(deltas.items(), key=lambda kv: abs(kv[1]))
    direction = "more" if top_delta > 0 else "less"
    msg = None
    if abs(top_delta) >= 0.10:
        msg = f"Your DNA moved {abs(top_delta)*100:.0f}% {direction} {top_axis} over the past {len(rows)} snapshots."
        await db.execute(text("""
            INSERT INTO notifications (user_id, kind, title, body)
            VALUES (:u, 'taste_shift', 'Your taste is evolving', :m)
        """), {"u": str(user.id), "m": msg})
        await db.commit()
    return {"shift": {"axis": top_axis, "delta": top_delta}, "message": msg}


# ─── Feature flags ───────────────────────────────────────
@router.get("/feature-flags")
async def get_flags(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("SELECT key, enabled, rollout_pct FROM feature_flags"))).mappings().all()
    # deterministic bucket
    bucket = int(hashlib.sha256(str(user.id).encode()).hexdigest()[:8], 16) % 100
    return {"flags": {r["key"]: (r["enabled"] and bucket < r["rollout_pct"]) for r in rows}, "bucket": bucket}


@router.put("/admin/feature-flags/{key}")
async def set_flag(
    key: str,
    enabled: bool = Query(...),
    rollout_pct: int = Query(100, ge=0, le=100),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("""
        INSERT INTO feature_flags (key, enabled, rollout_pct)
        VALUES (:k, :e, :p)
        ON CONFLICT (key) DO UPDATE SET enabled=EXCLUDED.enabled, rollout_pct=EXCLUDED.rollout_pct, updated_at=now()
    """), {"k": key, "e": enabled, "p": rollout_pct})
    await db.commit()
    return {"status": "ok"}


# ─── Stripe checkout stub ────────────────────────────────
@router.post("/billing/checkout")
async def checkout(
    user: Annotated[User, Depends(get_current_user)],
):
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        return {"status": "stub", "checkout_url": f"/billing/success?tier=pro&user={user.id}",
                "note": "Set STRIPE_SECRET_KEY to enable real checkout."}
    # Real Stripe call
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                headers={"Authorization": f"Bearer {stripe_key}"},
                data={
                    "mode": "subscription",
                    "success_url": os.getenv("APP_URL", "http://localhost:3000") + "/billing/success",
                    "cancel_url": os.getenv("APP_URL", "http://localhost:3000") + "/billing/cancel",
                    "line_items[0][price]": os.getenv("STRIPE_PRICE_ID", "price_pro_monthly"),
                    "line_items[0][quantity]": "1",
                    "customer_email": user.email,
                },
            )
            if r.status_code == 200:
                return {"checkout_url": r.json().get("url")}
    except Exception:
        pass
    raise HTTPException(status_code=502, detail="stripe error")


# ─── Awards-rich content metadata ────────────────────────
@router.get("/content/{content_id}/badges")
async def content_badges(
    content_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("""
        SELECT awards, imdb_rating, rt_score FROM content WHERE id=:c
    """), {"c": str(content_id)})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    badges = []
    if row["awards"] and "oscar" in (row["awards"] or "").lower():
        badges.append({"kind": "oscar", "label": "Oscar Winner"})
    if row["imdb_rating"] and row["imdb_rating"] >= 8.0:
        badges.append({"kind": "highly_rated", "label": f"IMDb {row['imdb_rating']}"})
    if row["rt_score"] and row["rt_score"] >= 90:
        badges.append({"kind": "rt_fresh", "label": f"Rotten Tomatoes {row['rt_score']}%"})
    return {"badges": badges}


# ─── Streaming availability ──────────────────────────────
@router.get("/content/{content_id}/streaming")
async def streaming(
    content_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT service, region, deep_link FROM streaming_availability WHERE content_id=:c
    """), {"c": str(content_id)})).mappings().all()
    return {"items": [dict(r) for r in rows]}


# ─── Conversational actions from chat ────────────────────
class ChatActionIn(BaseModel):
    intent: str  # add_to_queue | rate | mark_watched | add_to_list
    content_id: uuid.UUID
    queue_id: uuid.UUID | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    mood_tag: str | None = None


@router.post("/chat/action")
async def chat_action(
    body: ChatActionIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.intent == "add_to_queue":
        if not body.queue_id:
            raise HTTPException(status_code=400, detail="queue_id required")
        await db.execute(text("""
            INSERT INTO queue_items (queue_id, content_id) VALUES (:q, :c)
            ON CONFLICT DO NOTHING
        """), {"q": str(body.queue_id), "c": str(body.content_id)})
    elif body.intent == "rate":
        await db.execute(text("""
            INSERT INTO ratings (user_id, content_id, rating, mood_tag)
            VALUES (:u, :c, :r, :m)
            ON CONFLICT (user_id, content_id) DO UPDATE SET rating=EXCLUDED.rating, mood_tag=EXCLUDED.mood_tag
        """), {"u": str(user.id), "c": str(body.content_id),
               "r": body.rating or 3, "m": body.mood_tag})
    elif body.intent == "mark_watched":
        await db.execute(text("""
            INSERT INTO watch_history (user_id, content_id, watch_pct, completed, last_watched_at, watch_count)
            VALUES (:u, :c, 1.0, true, now(), 1)
            ON CONFLICT (user_id, content_id) DO UPDATE SET watch_pct=1.0, completed=true, last_watched_at=now(),
                watch_count=watch_history.watch_count + 1
        """), {"u": str(user.id), "c": str(body.content_id)})
    elif body.intent == "add_to_list":
        await db.execute(text("""
            INSERT INTO watchlist (user_id, content_id) VALUES (:u, :c) ON CONFLICT DO NOTHING
        """), {"u": str(user.id), "c": str(body.content_id)})
    else:
        raise HTTPException(status_code=400, detail="unknown intent")
    await db.commit()
    return {"status": "ok"}
