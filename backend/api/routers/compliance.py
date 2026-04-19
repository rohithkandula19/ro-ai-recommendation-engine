"""Compliance + business: consent, age gate, geo, blocks, gifts, affiliates, stripe webhooks."""
import hashlib
import hmac
import os
import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user, require_admin
from models.user import User

router = APIRouter(tags=["compliance"])


# ─── Consent (cookies, analytics, marketing, personalization) ─
class ConsentIn(BaseModel):
    analytics: bool = False
    marketing: bool = False
    personalization: bool = True
    age_confirmed_over: int = Field(ge=0, le=100)
    region: str = Field(min_length=2, max_length=5, default="US")


@router.put("/users/me/consent")
async def set_consent(
    body: ConsentIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO consent_records (user_id, analytics, marketing, personalization, age_confirmed_over, region)
        VALUES (:u, :a, :m, :p, :age, :r)
        ON CONFLICT (user_id) DO UPDATE SET
            analytics=EXCLUDED.analytics,
            marketing=EXCLUDED.marketing,
            personalization=EXCLUDED.personalization,
            age_confirmed_over=EXCLUDED.age_confirmed_over,
            region=EXCLUDED.region,
            updated_at=now()
    """), {"u": str(user.id), "a": body.analytics, "m": body.marketing,
           "p": body.personalization, "age": body.age_confirmed_over, "r": body.region})
    await db.commit()
    return {"status": "ok"}


@router.get("/users/me/consent")
async def get_consent(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("SELECT * FROM consent_records WHERE user_id=:u"),
                            {"u": str(user.id)})).mappings().first()
    if not row:
        return {"analytics": False, "marketing": False, "personalization": True,
                "age_confirmed_over": 13, "region": "US"}
    return {**row, "user_id": str(row["user_id"]),
            "updated_at": row["updated_at"].isoformat()}


# ─── Geo region check ─────────────────────────────────────
@router.get("/content/{content_id}/available-in/{region}")
async def availability_check(
    content_id: uuid.UUID, region: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("""
        SELECT allowed_regions FROM content_regions WHERE content_id=:c
    """), {"c": str(content_id)})).first()
    if not row:
        return {"available": True, "region": region}
    return {"available": region.upper() in (row[0] or []), "region": region}


# ─── User blocks ──────────────────────────────────────────
class BlockIn(BaseModel):
    blocked_id: uuid.UUID


@router.post("/users/me/blocks")
async def block(
    body: BlockIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO user_blocks (user_id, blocked_id) VALUES (:u, :b) ON CONFLICT DO NOTHING
    """), {"u": str(user.id), "b": str(body.blocked_id)})
    await db.execute(text("""
        DELETE FROM friendships WHERE (user_id=:u AND friend_id=:b) OR (user_id=:b AND friend_id=:u)
    """), {"u": str(user.id), "b": str(body.blocked_id)})
    await db.commit()
    return {"status": "blocked"}


@router.delete("/users/me/blocks/{blocked_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock(
    blocked_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("DELETE FROM user_blocks WHERE user_id=:u AND blocked_id=:b"),
                     {"u": str(user.id), "b": str(blocked_id)})
    await db.commit()


# ─── Gift codes ───────────────────────────────────────────
class GiftCreate(BaseModel):
    tier: str = "pro"
    months: int = Field(default=1, ge=1, le=12)


@router.post("/gifts/create")
async def create_gift(
    body: GiftCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    code = secrets.token_urlsafe(8)[:12].upper()
    await db.execute(text("""
        INSERT INTO gift_codes (code, purchaser_id, tier, months) VALUES (:c, :u, :t, :m)
    """), {"c": code, "u": str(user.id), "t": body.tier, "m": body.months})
    await db.commit()
    return {"code": code, "share_url": f"/gifts/redeem?code={code}"}


@router.post("/gifts/redeem/{code}")
async def redeem_gift(
    code: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text(
        "SELECT tier, months, redeemer_id FROM gift_codes WHERE code=:c"
    ), {"c": code})).first()
    if not row:
        raise HTTPException(status_code=404, detail="invalid code")
    if row[2] is not None:
        raise HTTPException(status_code=400, detail="already redeemed")
    await db.execute(text("""
        UPDATE gift_codes SET redeemer_id=:u, redeemed_at=now() WHERE code=:c
    """), {"u": str(user.id), "c": code})
    await db.execute(text("""
        INSERT INTO entitlements (user_id, tier) VALUES (:u, :t)
        ON CONFLICT (user_id) DO UPDATE SET tier=EXCLUDED.tier, renewed_at=now()
    """), {"u": str(user.id), "t": row[0]})
    await db.commit()
    return {"status": "redeemed", "tier": row[0], "months": row[1]}


# ─── Affiliate click ──────────────────────────────────────
@router.post("/content/{content_id}/click-affiliate/{service}")
async def click_affiliate(
    content_id: uuid.UUID, service: str,
    user: Annotated[User, Depends(get_current_user)],
    region: str = Query("US"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    row = (await db.execute(text("""
        SELECT link, commission_bps FROM affiliate_links WHERE content_id=:c AND service=:s
    """), {"c": str(content_id), "s": service})).first()
    if not row:
        raise HTTPException(status_code=404, detail="no affiliate link")
    await db.execute(text("""
        INSERT INTO content_availability_log (content_id, region, user_id, clicked_service)
        VALUES (:c, :r, :u, :s)
    """), {"c": str(content_id), "r": region, "u": str(user.id), "s": service})
    await db.commit()
    return {"redirect_to": row[0]}


# ─── Review reactions ─────────────────────────────────────
class ReactionIn(BaseModel):
    emoji: str = Field(min_length=1, max_length=10)


@router.post("/reviews/{review_id}/react")
async def react(
    review_id: uuid.UUID, body: ReactionIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO review_reactions (review_id, user_id, emoji) VALUES (:r, :u, :e)
        ON CONFLICT (review_id, user_id) DO UPDATE SET emoji=EXCLUDED.emoji
    """), {"r": str(review_id), "u": str(user.id), "e": body.emoji})
    await db.commit()
    return {"status": "ok"}


@router.get("/reviews/{review_id}/reactions")
async def review_reactions(
    review_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT emoji, COUNT(*) AS n FROM review_reactions WHERE review_id=:r GROUP BY emoji
    """), {"r": str(review_id)})).mappings().all()
    return {"reactions": [{"emoji": r["emoji"], "count": int(r["n"])} for r in rows]}


# ─── Stripe webhook ───────────────────────────────────────
@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Process checkout.session.completed / invoice.paid events."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    if secret:
        # Lightweight sig check
        try:
            timestamp = sig_header.split(",")[0].split("=")[1]
            expected = hmac.new(secret.encode(), f"{timestamp}.{body.decode()}".encode(), hashlib.sha256).hexdigest()
            if expected not in sig_header:
                raise HTTPException(status_code=400, detail="bad signature")
        except Exception:
            raise HTTPException(status_code=400, detail="bad signature")
    try:
        import json as _json
        event = _json.loads(body.decode() or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="bad payload")
    kind = event.get("type")
    obj = event.get("data", {}).get("object", {})
    email = obj.get("customer_email")
    if not email:
        return {"status": "ignored"}
    if kind in ("checkout.session.completed", "invoice.paid"):
        await db.execute(text("""
            UPDATE entitlements SET tier='pro', ai_quota_daily=500, renewed_at=now()
            WHERE user_id IN (SELECT id FROM users WHERE email=:e)
        """), {"e": email})
        await db.commit()
    return {"status": "ok", "kind": kind}


# ─── Privacy / TOS content (admin-editable) ──────────────
TOS = {
    "privacy": "RO AI Rec Engine collects: account data, watch history, ratings, chat messages. Used for personalization. Export or delete anytime.",
    "terms": "By using RO Rec you agree to use it for personal viewing. Content is fictional demo data from public APIs (TVMaze, Trakt).",
    "cookies": "We use essential cookies for auth and optional cookies for analytics. Toggle anytime in Security settings.",
}


@router.get("/legal/{kind}")
async def legal(kind: str):
    if kind not in TOS:
        raise HTTPException(status_code=404, detail="not found")
    return {"kind": kind, "text": TOS[kind]}
