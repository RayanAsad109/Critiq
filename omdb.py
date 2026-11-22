"""OMDb client for IMDb and Rotten Tomatoes scores.

TMDB gives us each title's IMDb id; OMDb turns that into ratings. The free key
allows 1,000 lookups a day, so every answer is cached on disk for a week.
Free key: https://www.omdbapi.com/apikey.aspx
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

URL = "https://www.omdbapi.com/"
CACHE_DIR = Path(__file__).parent / "data" / "omdb_cache"
CACHE_SECONDS = 7 * 24 * 3600
EMPTY = {"imdb": None, "imdb_votes": 0, "rt": None}


class OMDbError(RuntimeError):
    pass


class OMDb:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def ratings(self, imdb_id: str | None) -> dict:
        """{"imdb": 7.9 | None, "imdb_votes": 756123, "rt": 94 | None}"""
        if not imdb_id:
            return dict(EMPTY)
        cache = CACHE_DIR / f"{imdb_id}.json"
        if cache.exists() and time.time() - cache.stat().st_mtime < CACHE_SECONDS:
            return json.loads(cache.read_text())
        try:
            resp = self.session.get(URL, params={"i": imdb_id, "apikey": self.api_key}, timeout=10)
            data = resp.json()
        except (requests.RequestException, ValueError):
            return dict(EMPTY)                     # network hiccup: just show no score
        if data.get("Response") == "False":
            err = data.get("Error", "")
            if "not found" in err.lower() or "incorrect imdb id" in err.lower():
                return dict(EMPTY)                 # OMDb just doesn't know this title
            raise OMDbError(err or "OMDb returned an error")   # bad / inactive key, daily limit…
        out = parse(data)
        cache.write_text(json.dumps(out))
        return out

    def ratings_many(self, imdb_ids: list[str | None], workers: int = 8) -> list[dict]:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(self._safe, imdb_ids))

    def _safe(self, imdb_id):
        try:
            return self.ratings(imdb_id)
        except OMDbError:
            return dict(EMPTY)


def parse(data: dict) -> dict:
    def num(x, cast=float):
        try:
            return cast(str(x).replace(",", "").replace("%", "").split("/")[0])
        except (TypeError, ValueError):
            return None

    rt = next((r["Value"] for r in data.get("Ratings", []) if r.get("Source") == "Rotten Tomatoes"), None)
    return {"imdb": num(data.get("imdbRating")),
            "imdb_votes": num(data.get("imdbVotes"), int) or 0,
            "rt": num(rt, int) if rt else None}


def attach_and_filter(recs: list, omdb: OMDb | None, min_imdb: float = 0, min_rt: int = 0,
                      want: int = 12, batch: int = 12) -> list:
    """Walk the ranked recommendations, look up scores in small batches, and keep
    the first `want` that clear the IMDb / Rotten Tomatoes minimums. Looking up
    only as many as needed keeps us well inside the daily OMDb quota."""
    if omdb is None:
        return recs[:want]
    kept = []
    for i in range(0, len(recs), batch):
        chunk = recs[i:i + batch]
        for r, scores in zip(chunk, omdb.ratings_many([r.title.get("imdb_id") for r in chunk])):
            r.title.update(imdb=scores["imdb"], imdb_votes=scores["imdb_votes"], rt=scores["rt"])
            if min_imdb and (r.title["imdb"] is None or r.title["imdb"] < min_imdb):
                continue
            if min_rt and (r.title["rt"] is None or r.title["rt"] < min_rt):
                continue
            kept.append(r)
            if len(kept) == want:
                return kept
    return kept


def taste_vs_imdb(pairs: list[tuple[float, float | None]]) -> float | None:
    """Average of (your stars - IMDb/2) over titles that have an IMDb score.
    Negative = you're harsher than IMDb, positive = kinder. None if under 3 titles."""
    diffs = [mine - imdb / 2 for mine, imdb in pairs if imdb]
    return sum(diffs) / len(diffs) if len(diffs) >= 3 else None
