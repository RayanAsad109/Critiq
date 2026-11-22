"""OMDb parsing and rating-filter tests (no network)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from omdb import attach_and_filter, parse, taste_vs_imdb  # noqa: E402
from recommender import Recommendation, recommend  # noqa: E402
from test_recommender import INTERSTELLAR, POOL, TENET, WATCHED  # noqa: E402


def test_parse_omdb_payload():
    data = {"imdbRating": "8.7", "imdbVotes": "2,112,345",
            "Ratings": [{"Source": "Internet Movie Database", "Value": "8.7/10"},
                        {"Source": "Rotten Tomatoes", "Value": "73%"}]}
    assert parse(data) == {"imdb": 8.7, "imdb_votes": 2112345, "rt": 73}
    assert parse({"imdbRating": "N/A", "imdbVotes": "N/A", "Ratings": []}) == \
        {"imdb": None, "imdb_votes": 0, "rt": None}


class FakeOMDb:
    def __init__(self, table):
        self.table, self.calls = table, 0

    def ratings_many(self, ids):
        self.calls += len(ids)
        return [self.table.get(i, {"imdb": None, "imdb_votes": 0, "rt": None}) for i in ids]


def rec(title, imdb_id):
    return Recommendation({**title, "imdb_id": imdb_id}, 1.0, [])


def test_min_imdb_and_rt_filters_and_lazy_lookup():
    recs = [rec(INTERSTELLAR, "tt1"), rec(TENET, "tt2")] + [rec(INTERSTELLAR, f"tt{i}") for i in range(3, 40)]
    fake = FakeOMDb({"tt1": {"imdb": 8.7, "imdb_votes": 1, "rt": 73},
                     "tt2": {"imdb": 7.3, "imdb_votes": 1, "rt": 69}})
    kept = attach_and_filter(recs, fake, min_imdb=8.0, want=1, batch=12)
    assert [r.title["imdb_id"] for r in kept] == ["tt1"]
    assert fake.calls == 12                      # stopped after the first batch
    kept = attach_and_filter(recs[:2], FakeOMDb(fake.table), min_rt=70)
    assert [r.title["imdb_id"] for r in kept] == ["tt1"]
    assert kept[0].title["rt"] == 73


def test_no_omdb_key_just_trims():
    recs = [rec(INTERSTELLAR, "tt1"), rec(TENET, "tt2")]
    assert attach_and_filter(recs, None, min_imdb=9, want=1) == recs[:1]


def test_actor_director_filter_restricts_pool():
    got = {r.title["title"] for r in recommend(WATCHED, POOL, allowed_keys={"movie:11", "tv:13"})}
    assert got == {"Tenet", "Dark"}


def test_taste_vs_imdb():
    # you: 3, 4, 2 stars ; IMDb 8.0, 8.0, 6.0  ->  diffs -1, 0, -1  -> -0.667
    assert round(taste_vs_imdb([(3, 8.0), (4, 8.0), (2, 6.0), (5, None)]), 3) == -0.667
    assert taste_vs_imdb([(3, 8.0)]) is None
