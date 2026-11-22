"""Storage tests against a throwaway SQLite database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage import Store, _fix_url  # noqa: E402
from test_recommender import INCEPTION, NOTEBOOK  # noqa: E402


def make_store(tmp_path):
    return Store(f"sqlite:///{tmp_path / 'test.db'}")


def test_ratings_persist_across_store_instances(tmp_path):
    make_store(tmp_path).upsert_rating("a@x.com", INCEPTION, 4.75, "great twist")
    reopened = make_store(tmp_path)  # simulates closing and reopening the app
    w = reopened.get_watched("a@x.com")
    assert len(w) == 1 and w[0]["rating"] == 4.75 and w[0]["review"] == "great twist"
    assert w[0]["title"]["title"] == "Inception"


def test_users_are_isolated(tmp_path):
    s = make_store(tmp_path)
    s.upsert_rating("a@x.com", INCEPTION, 5, "")
    s.upsert_rating("b@x.com", NOTEBOOK, 1, "")
    assert [w["title"]["title"] for w in s.get_watched("a@x.com")] == ["Inception"]
    assert [w["title"]["title"] for w in s.get_watched("b@x.com")] == ["The Notebook"]


def test_update_and_delete(tmp_path):
    s = make_store(tmp_path)
    s.upsert_rating("a@x.com", INCEPTION, 3, "ok")
    s.upsert_rating("a@x.com", INCEPTION, 4.25, "grew on me")
    w = s.get_watched("a@x.com")
    assert len(w) == 1 and w[0]["rating"] == 4.25
    s.delete_rating("a@x.com", INCEPTION["key"])
    assert s.get_watched("a@x.com") == []


def test_prefs_and_backup_roundtrip(tmp_path):
    s = make_store(tmp_path)
    assert s.get_prefs("a@x.com")["actors"] == [] and s.get_prefs("a@x.com")["genres"] == []
    s.save_prefs("a@x.com", {"actors": ["Cillian Murphy"], "directors": [], "vibe": "heists"})
    s.upsert_rating("a@x.com", INCEPTION, 5, "wow")
    backup = s.export_user("a@x.com")
    other = Store(f"sqlite:///{tmp_path / 'other.db'}")
    assert other.import_user("new@x.com", backup) == 1
    assert other.get_prefs("new@x.com")["actors"] == ["Cillian Murphy"]
    assert other.get_watched("new@x.com")[0]["review"] == "wow"


def test_postgres_url_fix():
    assert _fix_url("postgres://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert _fix_url("postgresql://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert _fix_url("sqlite:///x.db") == "sqlite:///x.db"


def test_watchlist_add_remove_and_cleared_when_rated(tmp_path):
    s = make_store(tmp_path)
    s.add_to_watchlist("a@x.com", INCEPTION)
    s.add_to_watchlist("a@x.com", NOTEBOOK)
    assert {w["title"]["title"] for w in s.get_watchlist("a@x.com")} == {"Inception", "The Notebook"}
    s.remove_from_watchlist("a@x.com", NOTEBOOK["key"])
    s.upsert_rating("a@x.com", INCEPTION, 4.5, "")          # rating it takes it off the list
    assert s.get_watchlist("a@x.com") == []


def test_share_tokens_are_stable_and_resolve(tmp_path):
    s = make_store(tmp_path)
    t1 = s.share_token("a@x.com", "Rayan")
    assert s.share_token("a@x.com") == t1
    assert s.user_by_token(t1) == ("a@x.com", "Rayan")
    assert s.user_by_token("nope") is None
    assert s.share_token("b@x.com") != t1
