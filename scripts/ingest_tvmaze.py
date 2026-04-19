"""Fetch TV shows from TVMaze (no API key required) in the real_content.json shape.

Usage:
    python scripts/ingest_tvmaze.py --count 200 --output scripts/tvmaze_ingested.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
from pathlib import Path

import httpx
from loguru import logger


TVMAZE_BASE = "https://api.tvmaze.com"


def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def _cast(client: httpx.Client, show_id: int, n: int = 4) -> list[str]:
    try:
        r = client.get(f"{TVMAZE_BASE}/shows/{show_id}/cast", timeout=10)
        if r.status_code == 200:
            return [c["person"]["name"] for c in r.json()[:n] if c.get("person", {}).get("name")]
    except Exception:
        pass
    return []


def fetch(count: int) -> list[dict]:
    out: list[dict] = []
    page = 0
    with httpx.Client() as client:
        while len(out) < count:
            try:
                r = client.get(f"{TVMAZE_BASE}/shows", params={"page": page}, timeout=15)
            except Exception as e:
                logger.warning(f"page {page} failed: {e}")
                break
            if r.status_code == 404:
                break
            r.raise_for_status()
            shows = r.json()
            if not shows:
                break
            for s in shows:
                if len(out) >= count:
                    break
                if not s.get("summary") or not s.get("premiered"):
                    continue
                rating_raw = (s.get("rating") or {}).get("average") or 0
                if rating_raw and rating_raw < 7.0:
                    continue  # focus on decent-rated shows
                runtime = s.get("averageRuntime") or s.get("runtime") or 45
                premiered = s["premiered"][:4] if s.get("premiered") else None
                poster_path = ""
                if s.get("image") and s["image"].get("original"):
                    poster_path = s["image"]["original"]  # full URL (not just path)
                out.append({
                    "title": s["name"],
                    "type": "series",
                    "year": int(premiered) if premiered else None,
                    "runtime_min": int(runtime),
                    "genres": s.get("genres") or ["Drama"],
                    "rating": "TV-14",
                    "director": (s.get("network") or {}).get("name") or (s.get("webChannel") or {}).get("name") or "",
                    "cast": _cast(client, s["id"]),
                    "tvmaze_id": s["id"],
                    "poster": poster_path,
                    "description": _strip_html(s.get("summary")),
                })
                time.sleep(0.05)
            logger.info(f"tvmaze page {page}: total={len(out)}")
            page += 1
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--output", default=str(Path(__file__).parent / "tvmaze_ingested.json"))
    args = parser.parse_args()
    titles = fetch(args.count)
    payload = {"genres": sorted({g for t in titles for g in t.get("genres", [])}), "titles": titles}
    Path(args.output).write_text(json.dumps(payload, indent=2))
    logger.success(f"Wrote {len(titles)} TV shows → {args.output}")


if __name__ == "__main__":
    main()
