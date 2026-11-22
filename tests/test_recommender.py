"""Offline tests for the recommender using hand-made titles (no API needed).

Run:  python -m pytest tests
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recommender import build_candidate_keys, rating_weight, recommend  # noqa: E402


def T(i, title, genres, keywords, cast, directors, overview, media="movie", votes=(7.5, 1000)):
    return {
        "key": f"{media}:{i}", "id": i, "media_type": media, "title": title, "year": "2010",
        "overview": overview, "tagline": "", "genres": genres, "keywords": keywords,
        "cast": cast, "directors": directors, "vote_average": votes[0], "vote_count": votes[1],
        "poster": None, "related": [],
    }


INCEPTION = T(1, "Inception", ["Science Fiction", "Thriller"], ["dream", "heist", "twist ending"],
              ["Leonardo DiCaprio"], ["Christopher Nolan"],
              "A thief who steals secrets through dream-sharing technology plans one last heist.")
NOTEBOOK = T(2, "The Notebook", ["Romance", "Drama"], ["love", "letters"],
             ["Ryan Gosling"], ["Nick Cassavetes"],
             "A poor young man falls in love with a rich young woman in the 1940s.")

INTERSTELLAR = T(10, "Interstellar", ["Science Fiction", "Drama"], ["space", "time travel", "twist ending"],
                 ["Matthew McConaughey"], ["Christopher Nolan"],
                 "Explorers travel through a wormhole in space in a mind-bending twist on time.")
TENET = T(11, "Tenet", ["Science Fiction", "Thriller", "Action"], ["time", "heist", "spy"],
          ["John David Washington"], ["Christopher Nolan"],
          "A secret agent manipulates the flow of time to prevent a heist that could end the world.")
LOVE_ACTUALLY = T(12, "Love Actually", ["Romance", "Comedy"], ["love", "christmas"],
                  ["Hugh Grant"], ["Richard Curtis"],
                  "Interwoven love stories in London in the weeks before Christmas.")
DARK = T(13, "Dark", ["Science Fiction", "Mystery"], ["time travel", "twist ending", "small town"],
         ["Louis Hofmann"], ["Baran bo Odar"],
         "A missing child sets four families on a frantic hunt across time.", media="tv")
WOLF = T(14, "The Wolf of Wall Street", ["Comedy", "Crime"], ["stock market", "fraud"],
         ["Leonardo DiCaprio"], ["Martin Scorsese"],
         "A stockbroker rises to wealth through fraud and corruption on Wall Street.")

WATCHED = [
    {"title": INCEPTION, "rating": 5.0, "review": "Loved the twist ending and the mind-bending time stuff"},
    {"title": NOTEBOOK, "rating": 1.0, "review": "Too sappy, cheesy love story"},
]
POOL = [INTERSTELLAR, TENET, LOVE_ACTUALLY, DARK, WOLF, INCEPTION]


def titles(recs):
    return [r.title["title"] for r in recs]


def test_rating_weight_range():
    assert rating_weight(0) == -1 and rating_weight(5) == 1 and rating_weight(2.5) == 0
    assert rating_weight(3.75) == 0.5


def test_likes_rank_above_dislikes_and_watched_excluded():
    recs = titles(recommend(WATCHED, POOL))
    assert "Inception" not in recs
    assert recs.index("Interstellar") < recs.index("Love Actually")
    assert recs[-1] == "Love Actually"  # closest to the 1/5 Notebook


def test_review_text_matters():
    """Same ratings, no reviews: Dark (twist/time travel, show) should drop vs. with reviews."""
    no_reviews = [{**w, "review": ""} for w in WATCHED]
    score_with = {r.title["title"]: r.score for r in recommend(WATCHED, POOL)}
    score_without = {r.title["title"]: r.score for r in recommend(no_reviews, POOL)}
    assert score_with["Dark"] > score_without["Dark"]


def test_favourite_actor_boost():
    base = {r.title["title"]: r.score for r in recommend(WATCHED, POOL)}
    boosted = {r.title["title"]: r.score for r in recommend(WATCHED, POOL, {"actors": ["leonardo dicaprio"]})}
    assert boosted["The Wolf of Wall Street"] > base["The Wolf of Wall Street"]
    assert boosted["Tenet"] == base["Tenet"]


def test_media_filter_and_reasons():
    recs = recommend(WATCHED, POOL, media_filter="tv")
    assert titles(recs) == ["Dark"]
    assert any("Because you rated Inception" in r for r in recs[0].reasons)
    assert any("You wrote about" in r for r in recs[0].reasons)


def test_vibe_only_cold_start():
    recs = recommend([], POOL, {"vibe": "christmas love story"})
    assert titles(recs)[0] == "Love Actually"


def test_candidate_keys_ignore_disliked_related():
    liked = {**WATCHED[0], "title": {**INCEPTION, "related": [("movie", 10), ("movie", 11)]}}
    disliked = {**WATCHED[1], "title": {**NOTEBOOK, "related": [("movie", 12)]}}
    keys = build_candidate_keys([liked, disliked], [("tv", 13)])
    assert ("movie", 10) in keys and ("tv", 13) in keys
    assert ("movie", 12) not in keys


def test_opinion_words_never_become_reasons():
    """Regression: 'loved' alone used to show up as a reason."""
    watched = [{"title": INCEPTION, "rating": 5.0, "review": "Loved it, amazing movie, really great"}]
    for r in recommend(watched, POOL):
        assert not any("loved" in x.lower() or "amazing" in x.lower() for x in r.reasons)
        assert not any("You wrote about" in x for x in r.reasons)


def test_review_phrase_reason():
    watched = [{"title": INCEPTION, "rating": 5.0, "review": "Loved the time travel and the twist ending"}]
    dark = next(r for r in recommend(watched, POOL) if r.title["title"] == "Dark")
    line = next(x for x in dark.reasons if x.startswith("You wrote about"))
    assert "time travel" in line or "twist ending" in line
    assert "“time”" not in line
    assert "travel twist" not in line          # a fake phrase glued together across "and the"


def test_genre_year_score_filters():
    titles_ = lambda p: {r.title["title"] for r in recommend(WATCHED, POOL, p)}
    assert titles_({"genres": ["Romance"]}) == {"Love Actually"}
    # TV uses "Sci-Fi & Fantasy"; picking "Science Fiction" must still include it
    dark_scifi = {**DARK, "genres": ["Sci-Fi & Fantasy", "Mystery"]}
    got = {r.title["title"] for r in recommend(WATCHED, [dark_scifi, LOVE_ACTUALLY], {"genres": ["Science Fiction"]})}
    assert got == {"Dark"}
    old = {**TENET, "key": "movie:99", "year": "1985"}
    assert "Tenet" not in {r.title["title"] for r in recommend(WATCHED, [old, INTERSTELLAR], {"year_min": 2000})}
    low = {**WOLF, "vote_average": 5.0}
    assert {r.title["title"] for r in recommend(WATCHED, [low, INTERSTELLAR], {"min_score": 7})} == {"Interstellar"}


def test_streaming_services_filter():
    on_netflix = {**INTERSTELLAR, "stream_on": ["Netflix"]}
    on_crave = {**TENET, "stream_on": ["Crave"]}
    nowhere = {**DARK}
    got = {r.title["title"] for r in recommend(WATCHED, [on_netflix, on_crave, nowhere],
                                               {"services": ["Netflix", "Disney Plus"]})}
    assert got == {"Interstellar"}
