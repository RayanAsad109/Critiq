"""Movie night blending and Letterboxd parsing."""

import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blend import blend  # noqa: E402
from letterboxd import parse, read_upload  # noqa: E402
from recommender import Recommendation  # noqa: E402


def R(key, score):
    return Recommendation({"key": key, "title": key}, score, [f"why {key}"])


def test_blend_prefers_titles_both_people_like():
    you = [R("a", 1.0), R("b", 0.9), R("c", 0.2), R("only-you", 0.95)]
    friend = [R("a", 0.3), R("b", 0.8), R("c", 0.9)]
    picks = blend(you, friend)
    assert [p.title["key"] for p in picks][0] == "b"          # both like it a lot
    assert "only-you" not in [p.title["key"] for p in picks]   # friend's taste wasn't scored on it
    b = picks[0]
    assert b.you == 90 and b.friend == round(100 * 0.8 / 0.9)
    assert b.reasons_you == ["why b"]


def test_blend_least_misery_beats_one_sided_love():
    you = [R("love-hate", 1.0), R("both-ok", 0.7)]
    friend = [R("love-hate", 0.1), R("both-ok", 0.7)]
    assert blend(you, friend)[0].title["key"] == "both-ok"


RATINGS = "Date,Name,Year,Letterboxd URI,Rating\n2024-01-02,Arrival,2016,https://boxd.it/a,4.5\n" \
          "2024-01-03,Cats,2019,https://boxd.it/c,0.5\n2024-01-04,Unrated,2020,https://boxd.it/u,\n"
REVIEWS = "Date,Name,Year,Letterboxd URI,Rating,Rewatch,Review,Tags,Watched Date\n" \
          "2024-01-02,Arrival,2016,https://letterboxd.com/x/film/arrival/,4.5,,\"The <i>language</i> twist<br/>wow &amp; more\",,\n" \
          "2024-02-01,Heat,1995,https://letterboxd.com/x/film/heat/,5,,Best shootout,,\n" \
          "2024-02-02,Opinion Only,2001,https://letterboxd.com/x/film/o/,,,no rating here,,\n"
WATCHLIST = "Date,Name,Year,Letterboxd URI\n2024-03-01,Dune: Part Two,2024,https://boxd.it/d\n" \
            "2024-03-01,Arrival,2016,https://boxd.it/a\n"


def test_parse_letterboxd_export():
    rated, watch = parse({"ratings.csv": RATINGS, "reviews.csv": REVIEWS, "watchlist.csv": WATCHLIST})
    by_name = {e.name: e for e in rated}
    assert set(by_name) == {"Arrival", "Cats", "Heat"}          # unrated / rating-less review skipped
    assert by_name["Arrival"].rating == 4.5
    assert by_name["Arrival"].review == "The language twist\nwow & more"   # HTML cleaned
    assert by_name["Heat"].rating == 5.0 and by_name["Heat"].review == "Best shootout"
    assert [w.name for w in watch] == ["Dune: Part Two"]       # already-rated films not re-added


def test_read_upload_zip_and_single_csv():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ratings.csv", RATINGS)
        z.writestr("reviews.csv", REVIEWS)
        z.writestr("likes/films.csv", "ignored")
        z.writestr("deleted/reviews.csv", "ignored")
    files = read_upload("letterboxd-rayan-2026.zip", buf.getvalue())
    assert set(files) == {"ratings.csv", "reviews.csv"}
    assert set(read_upload("ratings.csv", RATINGS.encode())) == {"ratings.csv"}
