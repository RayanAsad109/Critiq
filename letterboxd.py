"""Read a Letterboxd data export.

Letterboxd → Settings → Data → Export your data gives a .zip containing, among
others:
  ratings.csv    Date, Name, Year, Letterboxd URI, Rating          (0.5–5)
  reviews.csv    Date, Name, Year, Letterboxd URI, Rating, Rewatch, Review, Tags, Watched Date
  watchlist.csv  Date, Name, Year, Letterboxd URI

Films are matched across files by (Name, Year), because review rows link to
the review page while rating rows link to the film.
"""

from __future__ import annotations

import csv
import html
import io
import re
import zipfile
from dataclasses import dataclass


@dataclass
class Entry:
    name: str
    year: str
    rating: float | None = None
    review: str = ""


def _rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))


def _clean_review(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)          # drop <i>, <b>, links…
    return html.unescape(text).strip()


def _rating(value: str) -> float | None:
    try:
        r = float(value)
    except (TypeError, ValueError):
        return None
    return r if 0 < r <= 5 else None


def parse(files: dict[str, str]) -> tuple[list[Entry], list[Entry]]:
    """files: {"ratings.csv": text, ...}. Returns (rated films, watchlist)."""
    rated: dict[tuple[str, str], Entry] = {}
    for row in _rows(files.get("ratings.csv", "")):
        r = _rating(row.get("Rating"))
        if row.get("Name") and r is not None:
            rated[(row["Name"], row.get("Year", ""))] = Entry(row["Name"], row.get("Year", ""), r)

    # reviews: newest wins; a review can also carry a rating the ratings file lacks
    review_rows = sorted(_rows(files.get("reviews.csv", "")), key=lambda r: r.get("Date", ""))
    for row in review_rows:
        key = (row.get("Name", ""), row.get("Year", ""))
        if not key[0]:
            continue
        entry = rated.get(key)
        if entry is None:
            r = _rating(row.get("Rating"))
            if r is None:
                continue                         # a review with no rating: nothing to learn from
            entry = rated[key] = Entry(key[0], key[1], r)
        review = _clean_review(row.get("Review", ""))
        if review:
            entry.review = review

    watch = [Entry(r["Name"], r.get("Year", "")) for r in _rows(files.get("watchlist.csv", ""))
             if r.get("Name") and (r["Name"], r.get("Year", "")) not in rated]
    return list(rated.values()), watch


def read_upload(name: str, data: bytes) -> dict[str, str]:
    """Accept the export .zip, or a single ratings/reviews/watchlist .csv."""
    if name.lower().endswith(".zip"):
        out = {}
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for member in z.namelist():
                base = member.rsplit("/", 1)[-1].lower()
                # skip the copies in likes/, deleted/, orphaned/ folders
                skip = any(f in member.lower() for f in ("likes/", "deleted/", "orphaned/"))
                if base in ("ratings.csv", "reviews.csv", "watchlist.csv") and not skip:
                    out[base] = z.read(member).decode("utf-8", errors="replace")
        return out
    base = name.rsplit("/", 1)[-1].lower()
    if base not in ("ratings.csv", "reviews.csv", "watchlist.csv"):
        base = "ratings.csv"
    return {base: data.decode("utf-8", errors="replace")}
