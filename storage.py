"""Persistent storage for ratings and preferences.

Uses SQLAlchemy so the same code talks to:
  * a local SQLite file (data/critiq.db) when you run it on your laptop
  * a hosted Postgres database (e.g. Neon / Supabase) when deployed,
    by setting DATABASE_URL in Streamlit secrets or the environment.

Every row is keyed by user_id (the signed-in user's email), so each person
only ever sees their own ratings.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (Column, DateTime, Float, MetaData, String, Table, Text,
                        create_engine, delete, select)
from sqlalchemy.engine import Engine

DEFAULT_URL = f"sqlite:///{Path(__file__).parent / 'data' / 'critiq.db'}"

metadata = MetaData()

ratings = Table(
    "ratings", metadata,
    Column("user_id", String(320), primary_key=True),
    Column("title_key", String(64), primary_key=True),   # e.g. "movie:27205"
    Column("title_json", Text, nullable=False),           # cached TMDB details
    Column("rating", Float, nullable=False),
    Column("review", Text, nullable=False, default=""),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

prefs = Table(
    "prefs", metadata,
    Column("user_id", String(320), primary_key=True),
    Column("prefs_json", Text, nullable=False),
)

watchlist = Table(
    "watchlist", metadata,
    Column("user_id", String(320), primary_key=True),
    Column("title_key", String(64), primary_key=True),
    Column("title_json", Text, nullable=False),
    Column("added_at", DateTime(timezone=True), nullable=False),
)

# One row per user: the private token behind their Movie night invite link.
profiles = Table(
    "profiles", metadata,
    Column("user_id", String(320), primary_key=True),
    Column("share_token", String(32), nullable=False, unique=True),
    Column("display_name", String(200), nullable=False, default=""),
)

EMPTY_PREFS = {"actors": [], "directors": [], "vibe": "",
               "genres": [], "year_min": None, "year_max": None, "min_score": 0.0,
               "min_imdb": 0.0, "min_rt": 0, "services": []}


def _fix_url(url: str) -> str:
    # Hosts often hand out "postgres://"; SQLAlchemy wants "postgresql+psycopg2://".
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


class Store:
    def __init__(self, url: str | None = None):
        url = _fix_url(url or DEFAULT_URL)
        if url.startswith("sqlite:///"):
            Path(url[len("sqlite:///"):]).parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(url, pool_pre_ping=True)
        metadata.create_all(self.engine)

    # --------------------------------------------------------------- ratings
    def get_watched(self, user_id: str) -> list[dict]:
        with self.engine.connect() as conn:
            rows = conn.execute(select(ratings).where(ratings.c.user_id == user_id)).mappings().all()
        return [{"title": json.loads(r["title_json"]), "rating": r["rating"], "review": r["review"],
                 "updated_at": r["updated_at"].isoformat() if r["updated_at"] else ""}
                for r in rows]

    def upsert_rating(self, user_id: str, title: dict, rating: float, review: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(ratings).where((ratings.c.user_id == user_id)
                                               & (ratings.c.title_key == title["key"])))
            conn.execute(ratings.insert().values(
                user_id=user_id, title_key=title["key"], title_json=json.dumps(title),
                rating=float(rating), review=review or "",
                updated_at=datetime.now(timezone.utc)))
            # once you've rated it, it's no longer "for later"
            conn.execute(delete(watchlist).where((watchlist.c.user_id == user_id)
                                                 & (watchlist.c.title_key == title["key"])))

    def delete_rating(self, user_id: str, title_key: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(ratings).where((ratings.c.user_id == user_id)
                                               & (ratings.c.title_key == title_key)))

    # ----------------------------------------------------------------- prefs
    def get_prefs(self, user_id: str) -> dict:
        with self.engine.connect() as conn:
            row = conn.execute(select(prefs.c.prefs_json).where(prefs.c.user_id == user_id)).first()
        return {**EMPTY_PREFS, **json.loads(row[0])} if row else dict(EMPTY_PREFS)

    def save_prefs(self, user_id: str, p: dict) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(prefs).where(prefs.c.user_id == user_id))
            conn.execute(prefs.insert().values(user_id=user_id, prefs_json=json.dumps(p)))

    # ------------------------------------------------------------- watchlist
    def get_watchlist(self, user_id: str) -> list[dict]:
        with self.engine.connect() as conn:
            rows = conn.execute(select(watchlist).where(watchlist.c.user_id == user_id)
                                .order_by(watchlist.c.added_at.desc())).mappings().all()
        return [{"title": json.loads(r["title_json"]),
                 "added_at": r["added_at"].isoformat() if r["added_at"] else ""} for r in rows]

    def add_to_watchlist(self, user_id: str, title: dict) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(watchlist).where((watchlist.c.user_id == user_id)
                                                 & (watchlist.c.title_key == title["key"])))
            conn.execute(watchlist.insert().values(user_id=user_id, title_key=title["key"],
                                                   title_json=json.dumps(title),
                                                   added_at=datetime.now(timezone.utc)))

    def remove_from_watchlist(self, user_id: str, title_key: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(watchlist).where((watchlist.c.user_id == user_id)
                                                 & (watchlist.c.title_key == title_key)))

    # --------------------------------------------------------- movie night
    def share_token(self, user_id: str, display_name: str = "") -> str:
        """The user's invite token, created the first time it's asked for."""
        with self.engine.begin() as conn:
            row = conn.execute(select(profiles.c.share_token)
                               .where(profiles.c.user_id == user_id)).first()
            if row:
                if display_name:
                    conn.execute(profiles.update().where(profiles.c.user_id == user_id)
                                 .values(display_name=display_name))
                return row[0]
            token = secrets.token_urlsafe(9)
            conn.execute(profiles.insert().values(user_id=user_id, share_token=token,
                                                  display_name=display_name or ""))
            return token

    def user_by_token(self, token: str) -> tuple[str, str] | None:
        """(user_id, display_name) for an invite token, or None."""
        with self.engine.connect() as conn:
            row = conn.execute(select(profiles.c.user_id, profiles.c.display_name)
                               .where(profiles.c.share_token == token)).first()
        return (row[0], row[1]) if row else None

    # ------------------------------------------------------- import / export
    def export_user(self, user_id: str) -> dict:
        return {"watched": self.get_watched(user_id), "prefs": self.get_prefs(user_id),
                "watchlist": self.get_watchlist(user_id)}

    def import_user(self, user_id: str, data: dict) -> int:
        for w in data.get("watched", []):
            self.upsert_rating(user_id, w["title"], w["rating"], w.get("review", ""))
        rated = {w["title"]["key"] for w in data.get("watched", [])}
        for item in data.get("watchlist", []):
            if item["title"]["key"] not in rated:
                self.add_to_watchlist(user_id, item["title"])
        if data.get("prefs"):
            self.save_prefs(user_id, data["prefs"])
        return len(data.get("watched", []))
