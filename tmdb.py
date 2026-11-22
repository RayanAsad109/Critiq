"""Thin TMDB API client with an on-disk cache.

Movies and TV shows are normalized into the same dict shape ("Title")
so the recommender never has to care which one it is looking at.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE_URL = "https://api.themoviedb.org/3"
POSTER_URL = "https://image.tmdb.org/t/p/w342"
BACKDROP_URL = "https://image.tmdb.org/t/p/w1280"
LOGO_URL = "https://image.tmdb.org/t/p/w92"
CREW_JOBS = ["Director", "Screenplay", "Writer", "Novel", "Director of Photography",
             "Original Music Composer", "Editor", "Producer"]
CACHE_DIR = Path(__file__).parent / "data" / "cache"
CACHE_DAYS = 7          # titles, cast and where-to-watch change slowly
LIST_HOURS = 12         # trending / "new on" lists go stale faster


class TMDBError(RuntimeError):
    pass


class TMDB:
    def __init__(self, api_key: str | None = None, use_cache: bool = True, region: str = "CA"):
        self.region = region
        self.api_key = (api_key or os.environ.get("TMDB_API_KEY", "")).strip()
        if not self.api_key:
            raise TMDBError("No TMDB API key. Set TMDB_API_KEY or enter it in the sidebar.")
        self.use_cache = use_cache
        self.session = requests.Session()
        # v4 "read access tokens" are long JWTs; v3 keys are 32 hex chars.
        if self.api_key.startswith("eyJ"):
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
            self._params = {}
        else:
            self._params = {"api_key": self.api_key}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ http
    def _get(self, path: str, _max_age: float = CACHE_DAYS * 86400, **params) -> dict:
        params = {**self._params, "language": "en-US", **params}
        key = hashlib.md5((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()
        cache_file = CACHE_DIR / f"{key}.json"
        if (self.use_cache and cache_file.exists()
                and time.time() - cache_file.stat().st_mtime < _max_age):
            return json.loads(cache_file.read_text())

        resp = self.session.get(BASE_URL + path, params=params, timeout=15)
        if resp.status_code == 401:
            raise TMDBError("TMDB rejected the API key (401). Double-check it.")
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        data = resp.json()
        if self.use_cache:
            cache_file.write_text(json.dumps(data))
        return data

    # ---------------------------------------------------------------- search
    def search_titles(self, query: str) -> list[dict]:
        """Search movies and shows at once. Returns light result dicts."""
        data = self._get("/search/multi", query=query, include_adult="false")
        out = []
        for r in data.get("results", []):
            if r.get("media_type") not in ("movie", "tv"):
                continue
            date = r.get("release_date") or r.get("first_air_date") or ""
            out.append({
                "id": r["id"],
                "media_type": r["media_type"],
                "title": r.get("title") or r.get("name") or "?",
                "year": date[:4],
                "poster": POSTER_URL + r["poster_path"] if r.get("poster_path") else None,
                "popularity": r.get("popularity", 0),
            })
        return out

    def search_person(self, name: str) -> dict | None:
        data = self._get("/search/person", query=name)
        results = data.get("results", [])
        if not results:
            return None
        p = max(results[:5], key=lambda r: r.get("popularity", 0))
        return {"id": p["id"], "name": p["name"], "dept": p.get("known_for_department", "")}

    # --------------------------------------------------------------- details
    def details(self, media_type: str, tmdb_id: int) -> dict:
        """Full normalized Title for one movie/show (includes rec candidates)."""
        if media_type == "movie":
            raw = self._get(f"/movie/{tmdb_id}",
                            append_to_response="credits,keywords,recommendations,similar,watch/providers")
        else:
            raw = self._get(f"/tv/{tmdb_id}",
                            append_to_response="aggregate_credits,keywords,recommendations,similar,external_ids,watch/providers")
        if not raw:
            return {}
        return normalize(raw, media_type, self.region)

    def full_details(self, media_type: str, tmdb_id: int) -> dict:
        """Everything the details page shows: Title fields plus cast/crew, trailer,
        where-to-watch for self.region, and a light list of similar titles."""
        if media_type == "movie":
            raw = self._get(f"/movie/{tmdb_id}", append_to_response=
                            "credits,keywords,recommendations,similar,videos,watch/providers")
        else:
            raw = self._get(f"/tv/{tmdb_id}", append_to_response=
                            "aggregate_credits,keywords,recommendations,similar,videos,watch/providers,external_ids")
        if not raw:
            return {}
        return {**normalize(raw, media_type, self.region), **extras(raw, media_type, self.region)}

    # -------------------------------------------------------------- discover
    def genre_ids(self) -> dict[str, dict[str, int]]:
        """{"movie": {"Action": 28, ...}, "tv": {"Action & Adventure": 10759, ...}}"""
        return {mt: {g["name"]: g["id"] for g in self._get(f"/genre/{mt}/list").get("genres", [])}
                for mt in ("movie", "tv")}

    def streaming_services(self) -> list[str]:
        """Names of subscription services TMDB tracks in self.region, most popular first."""
        names: dict[str, int] = {}
        for mt in ("movie", "tv"):
            data = self._get(f"/watch/providers/{mt}", watch_region=self.region)
            for p in data.get("results", []):
                prio = p.get("display_priorities", {}).get(self.region, p.get("display_priority", 999))
                names[p["provider_name"]] = min(prio, names.get(p["provider_name"], 999))
        return [n for n, _ in sorted(names.items(), key=lambda kv: kv[1])][:40]

    def provider_ids(self, names: list[str]) -> list[int]:
        ids = set()
        for mt in ("movie", "tv"):
            data = self._get(f"/watch/providers/{mt}", watch_region=self.region)
            ids |= {p["provider_id"] for p in data.get("results", []) if p["provider_name"] in names}
        return sorted(ids)

    def search_movie(self, name: str, year: str | int | None = None) -> dict | None:
        """Best TMDB match for a movie title (+ year), used by the Letterboxd import."""
        params = {"query": name, "include_adult": "false"}
        if year:
            params["primary_release_year"] = year
        results = self._get("/search/movie", **params).get("results", [])
        if not results and year:       # Letterboxd and TMDB sometimes disagree by a year
            results = self._get("/search/movie", query=name, include_adult="false").get("results", [])
        return results[0] if results else None

    def discover(self, media_type: str, genres: list[str], year_min: int | None,
                 year_max: int | None, min_score: float = 0, pages: int = 2,
                 services: list[str] | None = None) -> list[tuple[str, int]]:
        """Well-known titles matching the filters, as (media_type, id) keys."""
        from recommender import TV_GENRE_ALIASES  # shared alias table
        ids = self.genre_ids()[media_type]
        names = genres if media_type == "movie" else [TV_GENRE_ALIASES.get(g, g) for g in genres]
        gids = sorted({ids[n] for n in names if n in ids})
        if genres and not gids:
            return []                      # e.g. "Horror" has no TV genre
        date_field = "primary_release_date" if media_type == "movie" else "first_air_date"
        params = {"sort_by": "vote_count.desc", "vote_count.gte": 150,
                  "include_adult": "false"}
        if gids:
            params["with_genres"] = "|".join(map(str, gids))   # any of
        if year_min:
            params[f"{date_field}.gte"] = f"{year_min}-01-01"
        if year_max:
            params[f"{date_field}.lte"] = f"{year_max}-12-31"
        if min_score:
            params["vote_average.gte"] = min_score
        if services:
            params["with_watch_providers"] = "|".join(map(str, self.provider_ids(services)))
            params["watch_region"] = self.region
            params["with_watch_monetization_types"] = "flatrate|free|ads"
        out = []
        for page in range(1, pages + 1):
            data = self._get(f"/discover/{media_type}", page=page, **params)
            out += [(media_type, r["id"]) for r in data.get("results", [])]
        return out

    # ------------------------------------------------------------ home rows
    def trending(self, limit: int = 18) -> list[dict]:
        """This week's most-watched movies and shows (light titles with posters)."""
        data = self._get("/trending/all/week", _max_age=LIST_HOURS * 3600)
        results = [r for r in data.get("results", []) if r.get("media_type") in ("movie", "tv")]
        return light_list(results, "movie", limit)

    def new_on_services(self, services: list[str], limit: int = 18) -> list[dict]:
        """Well-liked titles from the last year that are included with your services."""
        if not services:
            return []
        ids = "|".join(map(str, self.provider_ids(services)))
        since = (date.today() - timedelta(days=365)).isoformat()
        out = []
        for mt, field in (("movie", "primary_release_date"), ("tv", "first_air_date")):
            data = self._get(f"/discover/{mt}", _max_age=LIST_HOURS * 3600,
                             sort_by="popularity.desc", watch_region=self.region,
                             with_watch_providers=ids, with_watch_monetization_types="flatrate|free|ads",
                             **{f"{field}.gte": since, "vote_count.gte": 20})
            out += [{**r, "media_type": mt} for r in data.get("results", [])]
        out.sort(key=lambda r: r.get("popularity", 0), reverse=True)
        return light_list(out, "movie", limit)

    def details_many(self, items: list[tuple[str, int]], workers: int = 8) -> list[dict]:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda it: self._safe_details(*it), items))
        return [r for r in results if r]

    def _safe_details(self, media_type: str, tmdb_id: int) -> dict:
        try:
            return self.details(media_type, tmdb_id)
        except requests.RequestException:
            return {}

    def person_filmography(self, person_id: int, as_director: bool, limit: int = 60) -> list[tuple[str, int]]:
        """Titles a person acted in (or directed/created), best known first."""
        data = self._get(f"/person/{person_id}/combined_credits")
        if as_director:
            credits = [c for c in data.get("crew", []) if c.get("job") in ("Director", "Creator")]
        else:
            # skip talk shows / award shows where actors appear as themselves
            credits = [c for c in data.get("cast", [])
                       if "himself" not in (c.get("character") or "").lower()
                       and "herself" not in (c.get("character") or "").lower()]
        credits = [c for c in credits if c.get("media_type") in ("movie", "tv")]
        credits.sort(key=lambda c: c.get("vote_count", 0), reverse=True)
        out, seen = [], set()
        for c in credits:
            k = (c["media_type"], c["id"])
            if k not in seen:
                seen.add(k)
                out.append(k)
        return out[:limit]

    def person_credits(self, person_id: int, limit: int = 15) -> list[tuple[str, int]]:
        """Best-known movies/shows for a person, as acting or directing credits."""
        data = self._get(f"/person/{person_id}/combined_credits")
        credits = [c for c in data.get("cast", [])]
        credits += [c for c in data.get("crew", []) if c.get("job") in ("Director", "Creator")]
        credits = [c for c in credits if c.get("media_type") in ("movie", "tv")]
        # TV "appearances" on talk shows etc. have tiny vote counts; sorting handles that.
        credits.sort(key=lambda c: c.get("vote_count", 0), reverse=True)
        seen, out = set(), []
        for c in credits:
            k = (c["media_type"], c["id"])
            if k not in seen:
                seen.add(k)
                out.append(k)
            if len(out) >= limit:
                break
        return out


def streaming_on(raw: dict, region: str) -> list[str]:
    """Services in `region` where it's included with a subscription (or free)."""
    r = raw.get("watch/providers", {}).get("results", {}).get(region, {})
    return sorted({p["provider_name"] for kind in ("flatrate", "free", "ads") for p in r.get(kind, [])})


def normalize(raw: dict, media_type: str, region: str = "CA") -> dict:
    """Map a TMDB movie or TV payload onto one common shape."""
    if media_type == "movie":
        cast = raw.get("credits", {}).get("cast", [])
        directors = [c["name"] for c in raw.get("credits", {}).get("crew", [])
                     if c.get("job") == "Director"]
        keywords = raw.get("keywords", {}).get("keywords", [])
        date = raw.get("release_date") or ""
        title = raw.get("title", "?")
    else:
        cast = raw.get("aggregate_credits", {}).get("cast", [])
        directors = [c["name"] for c in raw.get("created_by", [])]
        keywords = raw.get("keywords", {}).get("results", [])
        date = raw.get("first_air_date") or ""
        title = raw.get("name", "?")

    def light(results):
        return [(r.get("media_type") or media_type, r["id"]) for r in results if r.get("id")]

    return {
        "key": f"{media_type}:{raw['id']}",
        "id": raw["id"],
        "media_type": media_type,
        "title": title,
        "year": date[:4],
        "overview": raw.get("overview", ""),
        "tagline": raw.get("tagline", ""),
        "genres": [g["name"] for g in raw.get("genres", [])],
        "keywords": [k["name"] for k in keywords][:25],
        "cast": [c["name"] for c in cast[:8]],
        "directors": directors,
        "imdb_id": raw.get("imdb_id") or raw.get("external_ids", {}).get("imdb_id"),
        "stream_on": streaming_on(raw, region),
        "backdrop": BACKDROP_URL + raw["backdrop_path"] if raw.get("backdrop_path") else None,
        "vote_average": raw.get("vote_average", 0.0),
        "vote_count": raw.get("vote_count", 0),
        "poster": POSTER_URL + raw["poster_path"] if raw.get("poster_path") else None,
        "related": light(raw.get("recommendations", {}).get("results", []))
                   + light(raw.get("similar", {}).get("results", [])),
    }


def light_list(results: list[dict], media_type: str, limit: int = 12) -> list[dict]:
    out, seen = [], set()
    for r in results:
        k = f"{r.get('media_type') or media_type}:{r.get('id')}"
        if not r.get("id") or k in seen:
            continue
        seen.add(k)
        date = r.get("release_date") or r.get("first_air_date") or ""
        out.append({"id": r["id"], "media_type": r.get("media_type") or media_type,
                    "key": f"{r.get('media_type') or media_type}:{r['id']}",
                    "title": r.get("title") or r.get("name") or "?", "year": date[:4],
                    "poster": POSTER_URL + r["poster_path"] if r.get("poster_path") else None})
        if len(out) >= limit:
            break
    return out


def extras(raw: dict, media_type: str, region: str) -> dict:
    """Detail-page-only fields."""
    # cast with characters
    if media_type == "movie":
        cast = [{"name": c["name"], "character": c.get("character", "")}
                for c in raw.get("credits", {}).get("cast", [])]
        crew_raw = [(c.get("job"), c["name"]) for c in raw.get("credits", {}).get("crew", [])]
    else:
        cast = [{"name": c["name"],
                 "character": ", ".join(r.get("character", "") for r in c.get("roles", [])[:1])}
                for c in raw.get("aggregate_credits", {}).get("cast", [])]
        crew_raw = [(j.get("job"), c["name"]) for c in raw.get("aggregate_credits", {}).get("crew", [])
                    for j in c.get("jobs", [])]
        crew_raw = [("Creator", c["name"]) for c in raw.get("created_by", [])] + crew_raw
    crew: dict[str, list[str]] = {}
    for job, name in crew_raw:
        if job in CREW_JOBS + ["Creator"] and name not in crew.setdefault(job, []):
            crew[job].append(name)
    order = ["Creator"] + CREW_JOBS
    crew_list = [(job, crew[job][:4]) for job in order if crew.get(job)]

    # runtime / dates
    if media_type == "movie":
        mins = raw.get("runtime") or 0
        runtime = f"{mins // 60}h {mins % 60}m" if mins >= 60 else (f"{mins}m" if mins else "")
        released = raw.get("release_date") or ""
    else:
        seasons, eps = raw.get("number_of_seasons") or 0, raw.get("number_of_episodes") or 0
        runtime = (f"{seasons} season{'s' * (seasons != 1)}, {eps} episodes" if seasons else "")
        released = raw.get("first_air_date") or ""
        if raw.get("last_air_date") and raw.get("status") in ("Ended", "Canceled"):
            released += f" to {raw['last_air_date']}"

    lang_code = raw.get("original_language", "")
    language = next((l.get("english_name") for l in raw.get("spoken_languages", [])
                     if l.get("iso_639_1") == lang_code), lang_code.upper())
    countries = [c.get("name") for c in raw.get("production_countries", [])][:3]

    # trailer: prefer official YouTube trailers
    vids = [v for v in raw.get("videos", {}).get("results", []) if v.get("site") == "YouTube"]
    vids.sort(key=lambda v: (v.get("type") != "Trailer", not v.get("official", False)))
    trailer = vids[0]["key"] if vids else None

    # where to watch (TMDB data powered by JustWatch)
    region_data = raw.get("watch/providers", {}).get("results", {}).get(region, {})

    def provs(kind):
        return [{"name": p["provider_name"],
                 "logo": LOGO_URL + p["logo_path"] if p.get("logo_path") else None}
                for p in region_data.get(kind, [])][:6]

    providers = {"link": region_data.get("link"), "stream": provs("flatrate"),
                 "rent": provs("rent"), "buy": provs("buy")}

    return {
        "backdrop": BACKDROP_URL + raw["backdrop_path"] if raw.get("backdrop_path") else None,
        "cast_full": cast[:30],
        "crew": crew_list,
        "runtime": runtime,
        "released": released,
        "language": language,
        "countries": countries,
        "status": raw.get("status", ""),
        "networks": [n["name"] for n in raw.get("networks", [])][:3],
        "trailer": trailer,
        "providers": providers,
        "region": region,
        "similar": light_list(raw.get("recommendations", {}).get("results", [])
                              + raw.get("similar", {}).get("results", []), media_type),
    }
