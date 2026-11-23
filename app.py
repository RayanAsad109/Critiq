"""Critiq - rate what you've watched, get movie & show recommendations.

Run:  streamlit run app.py
"""

from __future__ import annotations

import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

import streamlit as st

import letterboxd
import ui
from blend import blend
from omdb import OMDb, OMDbError, attach_and_filter
from recommender import FILTER_GENRES, Recommendation, build_candidate_keys, recommend
from storage import Store
from tmdb import TMDB, TMDBError

st.set_page_config(page_title="Critiq", page_icon="🎬", layout="wide",
                   initial_sidebar_state="collapsed")
st.html(ui.CSS)
st.html(ui.EFFECTS_CSS)
st.html(ui.HOME_CSS)
st.html(ui.ATMOS_CSS)
st.html(ui.WALL_CSS)
st.html(ui.SKELETON_CSS)
st.html(ui.POLISH_CSS)

# Which film tints the page background. Pages set this as they render; the
# footer draws the atmosphere at the end of every run.
AMBIENT: dict = {"backdrop": None}


def ambient(t: dict | None):
    if t and t.get("backdrop") and not AMBIENT["backdrop"]:
        AMBIENT["backdrop"] = t["backdrop"]


def footer(wall: list[str] | None = None):
    """The page background and the TMDB credit. A details page keeps its film's backdrop
    atmosphere; the signed-in pages pass `wall` and get the faint poster wall instead."""
    if wall is None:
        st.html(ui.atmosphere_html(AMBIENT["backdrop"]) + ui.FOOTER)
    else:
        st.html(ui.app_wall_html(wall) + ui.FOOTER)


ADMIT_WINDOW = 20   # seconds: a sign-in token issued this recently means "just came back from Google"


def just_signed_in() -> bool:
    """True once, on the first run of a session that has just come back from Google sign-in.
    Uses the ID token's issued-at time; without it, falls back to having seen the sign-in
    page earlier in this same session. Never true on later runs of the session."""
    if st.session_state.get("admit_checked"):
        return False
    st.session_state.admit_checked = True
    iat = st.user.get("iat")
    if isinstance(iat, (int, float)):
        return 0 <= time.time() - iat < ADMIT_WINDOW
    return bool(st.session_state.pop("saw_signin", False))


WALL_MIN = 12       # fewer of the user's own posters than this: top up with trending


def wall_posters(own: list[dict], key: str) -> list[str]:
    """Posters for the signed-in wall: the user's rated and saved titles, then this week's
    trending ones until there are WALL_MIN."""
    seen, out = set(), []
    for t in own:
        url = t.get("poster")
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    for url in (signin_posters(key) if len(out) < WALL_MIN else []):
        if len(out) >= WALL_MIN:
            break
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out

GRID = 6            # posters per row in Rate / Library / More like this
REC_GRID = 4        # wider cards for recommendations (they carry reasons)
PAGES = ["Home", "Rate", "Library", "Discover", "Movie night"]

# One-tap moods on the home page: (what to look for, genres, movies/shows)
MOODS = {
    "Something mind-bending": ("mind-bending twist reality memory time travel puzzle", [], "Both"),
    "Edge-of-my-seat tense": ("tense suspense survival chase hostage", ["Thriller"], "Both"),
    "A slow-burn crime story": ("slow-burn investigation detective murder", ["Crime"], "Both"),
    "Make me laugh": ("funny friendship misadventure", ["Comedy"], "Both"),
    "Something heartfelt": ("family friendship love coming-of-age", ["Drama"], "Both"),
    "A show I can binge": ("", [], "Shows"),
}
THIS_YEAR = date.today().year
YEAR_FLOOR = 1920
KIND = {"Both": "both", "Movies": "movie", "Shows": "tv"}


# ------------------------------------------------------------------ config
def get_secret(name: str, default: str = "") -> str:
    """Environment variable first, then .streamlit/secrets.toml."""
    if os.environ.get(name):
        return os.environ[name]
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def auth_configured() -> bool:
    try:
        return "auth" in st.secrets
    except Exception:
        return False


@st.cache_resource
def get_store() -> Store:
    return Store(get_secret("DATABASE_URL") or None)


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def signin_posters(key: str) -> list[str]:
    """Poster URLs for the sign-in wall: this week's trending titles."""
    if not key:
        return []
    try:
        return [t["poster"] for t in TMDB(key).trending(limit=28) if t.get("poster")]
    except Exception:
        return []


@st.cache_resource
def rec_memory() -> dict:
    """Last recommendations per user (and per movie night), kept in server memory so
    they survive opening a details page (which reloads the page) and coming back."""
    return {}


def split_names(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def rows(items: list, n: int):
    for i in range(0, len(items), n):
        yield items[i:i + n], st.columns(n, gap="medium")


# ------------------------------------------------------------------ routing
# The URL is the source of truth so poster links, refresh, invite links and the
# browser's back button all work:  ?page=Discover&title=movie:329865
qp = st.query_params
if "page" not in st.session_state:
    st.session_state.page = qp.get("page") if qp.get("page") in PAGES else "Home"
for field in ("q", "dq"):
    if field not in st.session_state:
        st.session_state[field] = qp.get(field, "")


def link(key: str) -> str:
    """URL for a title's details page, remembering where you came from."""
    params = {"page": st.session_state.page, "title": key}
    if st.session_state.page == "Rate" and st.session_state.q:
        params["q"] = st.session_state.q
    if st.session_state.page == "Discover" and st.session_state.dq:
        params["dq"] = st.session_state.dq
    if st.session_state.page == "Movie night" and qp.get("with"):
        params["with"] = qp["with"]
    return "?" + urlencode(params)


def on_page_change():
    st.query_params.clear()
    st.query_params["page"] = st.session_state.page


def on_search_change(field: str = "q"):
    if st.session_state[field]:
        st.query_params[field] = st.session_state[field]
    else:
        st.query_params.pop(field, None)


def close_details():
    st.query_params.pop("title", None)


def go_to(page_name: str, autorun: bool = False):
    st.session_state.page = page_name
    st.query_params.clear()
    st.query_params["page"] = page_name
    if autorun:
        st.session_state.autorun = True


def part_of_day() -> str:
    try:
        tz = st.context.timezone
        now = datetime.now(ZoneInfo(tz)) if tz else datetime.now()
    except Exception:
        now = datetime.now()
    if 5 <= now.hour < 12:
        return "this morning"
    if 12 <= now.hour < 17:
        return "this afternoon"
    return "tonight"


# ------------------------------------------------------------------- login
if auth_configured():
    if not st.user.is_logged_in and qp.get("signin"):
        st.login()             # the ticket (or the landing page) links here: go straight to Google
    if not st.user.is_logged_in:
        st.html(ui.SIGNIN_CSS)
        today = date.today()
        seat = ui.ticket_seat(today)
        st.session_state.saw_signin = True      # fallback for the stamp when there is no iat claim
        href = "?" + urlencode({"with": qp["with"], "signin": 1} if qp.get("with") else {"signin": 1})
        st.html(ui.signin_html(signin_posters(get_secret("TMDB_API_KEY")),
                               today.strftime("%a %d %b"), seat, href, invited=bool(qp.get("with"))))
        st.html(ui.FOOTER)
        st.stop()
    if "signin" in qp:
        del qp["signin"]
    user_id = st.user.email
    user_label = st.user.get("name") or user_id
    if just_signed_in():
        today = date.today()
        st.html(ui.admitted_html(today.strftime("%a %d %b"), ui.ticket_seat(today)))
else:
    user_id = "local"          # no login configured: single-user mode on your own machine
    user_label = None

store = get_store()
watched = store.get_watched(user_id)
watched_by_key = {w["title"]["key"]: w for w in watched}
watchlist = store.get_watchlist(user_id)
saved_keys = {w["title"]["key"] for w in watchlist}
prefs = store.get_prefs(user_id)

api_key = get_secret("TMDB_API_KEY") or st.session_state.get("api_key", "")
try:
    tmdb = TMDB(api_key, region=get_secret("REGION", "CA")) if api_key else None
except TMDBError:
    tmdb = None

omdb_key = get_secret("OMDB_API_KEY")
omdb = OMDb(omdb_key) if omdb_key else None


# ------------------------------------------------------- letterboxd import
@st.dialog("Import from Letterboxd", width="medium")
def letterboxd_dialog():
    if st.session_state.pop("lb_close", False):
        st.rerun()                                  # full rerun closes the dialog, shows new ratings
    st.markdown("On Letterboxd go to **Settings → Data → Export your data**. You'll get a "
                "`.zip` file; upload it here as is.")
    up = st.file_uploader("Letterboxd export", type=["zip", "csv"], label_visibility="collapsed")
    keep_mine = st.checkbox("Keep my Critiq rating when a film is in both", value=True)
    with_watchlist = st.checkbox("Also bring over my Letterboxd watchlist", value=True)
    if not up or not st.button("Import", type="primary", icon=":material/download:"):
        return
    try:
        rated, wish = letterboxd.parse(letterboxd.read_upload(up.name, up.getvalue()))
    except Exception as e:                       # a corrupt zip or a non-Letterboxd csv
        st.error(f"Couldn't read that file. {e}")
        return
    if not with_watchlist:
        wish = []
    jobs = [("rate", e) for e in rated] + [("save", e) for e in wish]
    if not jobs:
        st.warning("No ratings or watchlist entries found in that file.")
        return

    def match(job):
        kind, entry = job
        m = tmdb.search_movie(entry.name, entry.year)
        return kind, entry, (tmdb.details("movie", m["id"]) if m else None)

    bar = st.progress(0.0, text="Matching films on TMDB…")
    done = imported = reviews = saved = skipped = 0
    missed: list[str] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fut in as_completed([pool.submit(match, j) for j in jobs]):
            done += 1
            try:
                kind, entry, t = fut.result()
            except Exception:
                continue
            if not t:
                missed.append(f"{entry.name} ({entry.year})")
            elif kind == "rate":
                if keep_mine and t["key"] in watched_by_key:
                    skipped += 1
                else:
                    store.upsert_rating(user_id, t, entry.rating, entry.review)
                    imported += 1
                    reviews += bool(entry.review)
            elif t["key"] not in watched_by_key:
                store.add_to_watchlist(user_id, t)
                saved += 1
            bar.progress(done / len(jobs), text=f"Matching films on TMDB… {done}/{len(jobs)}")
    bar.empty()
    def n(k, word):
        return f"{k} {word}{'' if k == 1 else 's'}"

    msg = f"Imported {n(imported, 'rating')} ({reviews} with reviews)"
    if saved:
        msg += f" and {n(saved, 'film')} for your watchlist"
    if skipped:
        msg += f". Kept your Critiq rating for {n(skipped, 'film')} you'd already rated"
    st.success(msg + ".")
    if missed:
        with st.expander(f"{len(missed)} couldn't be matched"):
            st.write(", ".join(missed))
    st.button("Done", type="primary", on_click=lambda: st.session_state.update(lb_close=True))


# ------------------------------------------------------------------ header
head_l, head_r = st.columns([5, 1], vertical_alignment="center")
with head_l:
    st.html(ui.header_html())
with head_r:
    with st.popover(user_label.split()[0] if user_label else "Account", icon=":material/person:",
                    width="stretch"):
        if user_label:
            st.caption(f"Signed in as {st.user.email}")
        else:
            st.caption("Local mode. Ratings are saved on this computer.")
        if tmdb and st.button("Import from Letterboxd", icon=":material/upload:", width="stretch"):
            letterboxd_dialog()
        st.download_button("Download my ratings", icon=":material/download:", width="stretch",
                           data=json.dumps(store.export_user(user_id), indent=2),
                           file_name="critiq-ratings.json", mime="application/json")
        upload = st.file_uploader("Restore from a backup", type="json")
        if upload and st.button("Import backup", width="stretch"):
            n = store.import_user(user_id, json.load(upload))
            st.session_state.flash = f"Imported {n} ratings"
            st.rerun()
        if user_label:
            st.button("Log out", on_click=st.logout, width="stretch", type="tertiary")

if not tmdb:
    st.markdown("#### Connect to TMDB")
    st.write("Critiq needs a free TMDB API key to search titles. Get one at "
             "themoviedb.org under Settings, API. To skip this step next time, put "
             "`TMDB_API_KEY` in `.streamlit/secrets.toml`.")
    key_in = st.text_input("TMDB API key", type="password")
    if key_in:
        st.session_state.api_key = key_in
        st.rerun()
    st.stop()

if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"), icon=":material/check:")


# ------------------------------------------------------------ rating dialog
@st.dialog("Rate it", width="medium")
def rate_dialog(media_type: str, tmdb_id: int):
    try:
        t = tmdb.details(media_type, tmdb_id)
    except TMDBError as e:
        st.error(str(e))
        return
    existing = watched_by_key.get(t["key"])
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.html(ui.poster_card(t, show_text=False))
    with right:
        st.markdown(f"### {t['title']}")
        st.caption(ui.meta_line(t, ", ".join(t.get("directors", [])[:2])))
        rating = st.slider("Your rating", 0.0, 5.0, existing["rating"] if existing else 3.5,
                           step=0.25, label_visibility="collapsed")
        st.html(ui.score_html(rating))
        review = st.text_area("What did you think?", value=existing["review"] if existing else "",
                              height=120, placeholder="The twist reframes the whole first act, "
                                                      "the alien language idea, the score…")
        st.caption("Write about what it is (themes, plot, style). The stars already say how much "
                   "you liked it.")
        with st.container(horizontal=True, horizontal_alignment="right"):
            if existing and st.button("Remove from library", type="tertiary"):
                store.delete_rating(user_id, t["key"])
                st.session_state.flash = f"Removed {t['title']}"
                st.rerun()
            if st.button("Save rating", type="primary", icon=":material/check:"):
                store.upsert_rating(user_id, t, rating, review)
                st.session_state.flash = f"Saved {t['title']} at {rating:g}/5"
                st.rerun()


def remove_rating(key: str, title: str):
    store.delete_rating(user_id, key)
    st.session_state.flash = f"Removed {title} from your library"


def rating_actions(t: dict, where: str):
    """Edit + remove (with a confirm step) for a title you've rated."""
    with st.container(horizontal=True, gap="small", wrap=False):
        if st.button("Edit", key=f"edit-{where}-{t['key']}", width="stretch",
                     help="Change your rating or review"):
            rate_dialog(t["media_type"], t["id"])
        with st.popover("", icon=":material/delete:", help="Remove from your library",
                        key=f"del-{where}-{t['key']}", width="content"):
            st.markdown(f"Remove **{t['title']}** and your review?")
            st.button("Remove", key=f"delok-{where}-{t['key']}", type="primary", width="stretch",
                      on_click=remove_rating, args=(t["key"], t["title"]))


# ----------------------------------------------------------------- watchlist
def toggle_saved(media_type: str, tmdb_id: int):
    key = f"{media_type}:{tmdb_id}"
    if key in saved_keys:
        store.remove_from_watchlist(user_id, key)
        st.session_state.flash = "Removed from your watchlist"
    else:
        t = tmdb.details(media_type, tmdb_id)
        store.add_to_watchlist(user_id, t)
        st.session_state.flash = f"Saved {t['title']} for later"


def save_button(t: dict, where: str, label: bool = False, stretch: bool | None = None):
    saved = t["key"] in saved_keys
    st.button(("Saved" if saved else "Save for later") if label else "",
              key=f"save-{where}-{t['key']}",
              icon=":material/bookmark_added:" if saved else ":material/bookmark_add:",
              help="Remove from watchlist" if saved else "Save for later",
              type="secondary", width="stretch" if (label if stretch is None else stretch) else "content",
              on_click=toggle_saved, args=(t["media_type"], t["id"]))


# --------------------------------------------------------------- skeletons
def load_into(stage, layout: str, work):
    """Show the page's skeleton in `stage` (a st.empty) while `work()` runs, and return its
    result. The caller then renders the real content with `stage.container()`, which
    replaces the skeleton in place, as soon as the data is ready."""
    stage.html(ui.skeleton_html(layout))
    try:
        return work()
    except Exception:
        stage.empty()
        raise


# --------------------------------------------------------------- spin the reel
@st.dialog("Spin the reel", width="small")
def spin_dialog(titles: list[dict], weights: list[float]):
    winner = random.choices(range(len(titles)), weights=[max(w, 0.01) for w in weights])[0]
    spin_id = f"{random.randrange(16 ** 6):06x}"
    st.html(ui.reel_html(titles, winner, link(titles[winner]["key"]), spin_id))
    st.button("Spin again", icon=":material/casino:", width="stretch")   # reruns the dialog


def spin_button(titles: list[dict], weights: list[float], key: str):
    if len(titles) >= 2 and st.button("Can't decide? Spin the reel", icon=":material/casino:", key=key):
        spin_dialog(titles, weights)


# ------------------------------------------------------- candidate gathering
def gather_candidates(rated: list[dict], p: dict, media_filter: str):
    """Pick ~100 titles worth scoring. Returns (candidates, allowed_keys_or_None)."""
    allowed, extra = None, []
    # actors / directors are hard filters: a title must feature one of them
    for names, as_director in ((p.get("actors") or [], False), (p.get("directors") or [], True)):
        if not names:
            continue
        keys_for_field = set()
        for name in names:
            person = tmdb.search_person(name)
            if person:
                films = tmdb.person_filmography(person["id"], as_director)
                extra += films
                keys_for_field |= {f"{m}:{i}" for m, i in films}
        allowed = keys_for_field if allowed is None else allowed & keys_for_field
    filters_on = bool(p.get("genres") or p.get("year_min") or p.get("year_max")
                      or p.get("min_imdb") or p.get("min_rt") or p.get("services"))
    discovered = []
    if (filters_on or not rated) and allowed is None:
        kinds = ["movie", "tv"] if media_filter == "both" else [media_filter]
        for mt in kinds:
            discovered += tmdb.discover(mt, p.get("genres") or [], p.get("year_min"),
                                        p.get("year_max"), 0, services=p.get("services") or [])
    if allowed is not None:
        keys = [(k.split(":")[0], int(k.split(":")[1])) for k in allowed][:120]
    else:
        keys = build_candidate_keys(rated, extra, discovered, limit=100)
    return tmdb.details_many(keys), allowed


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def service_names(region: str) -> list[str]:
    try:
        return tmdb.streaming_services()
    except Exception:
        return []


def card_meta(t: dict) -> str:
    return ", ".join(b.replace("Rotten Tomatoes", "RT") for b in ui.score_bits(t)[:2])


# ---------------------------------------------------------------- navigation
counts = {p: "" for p in PAGES}
counts["Library"] = f"  {len(watched)}"
icons = {"Home": ":material/home:", "Rate": ":material/star:", "Library": ":material/movie:",
         "Discover": ":material/explore:", "Movie night": ":material/group:"}
with st.container(key="nav"):
    page = st.pills("Section", PAGES, key="page", required=True, on_change=on_page_change,
                    format_func=lambda p: f"{icons[p]} {p}{counts[p]}",
                    label_visibility="collapsed")
st.write("")


# ============================================================ DETAILS PAGE
def details_page(key: str):
    try:
        media_type, tmdb_id = key.split(":")
        t = tmdb.full_details(media_type, int(tmdb_id))
    except (ValueError, TMDBError) as e:
        st.error(f"Couldn't load that title. {e}")
        t = {}
    if not t:
        st.button("Back", icon=":material/arrow_back:", on_click=close_details)
        return

    omdb_problem = None
    if not omdb:
        omdb_problem = ("IMDb and Rotten Tomatoes scores need an OMDb key: add OMDB_API_KEY to "
                        ".streamlit/secrets.toml and restart the app.")
    else:
        try:
            t.update(omdb.ratings(t.get("imdb_id")))
        except OMDbError as e:
            omdb_problem = (f"Couldn't get IMDb / Rotten Tomatoes scores. OMDb said: “{e}”. "
                            "If you just signed up, click the activation link in OMDb's email.")
    ambient(t)
    back = "home" if page == "Home" else page
    st.button(f"Back to {back}", icon=":material/arrow_back:", type="tertiary", on_click=close_details)
    st.html(ui.screen_html(t))
    if omdb_problem:
        st.caption(omdb_problem)
    mine = watched_by_key.get(t["key"])
    rec = next((r for r in rec_memory().get(user_id, []) if r.title["key"] == t["key"]), None)

    # actions sit right under the screen
    with st.container(horizontal=True, vertical_alignment="center"):
        if mine:
            st.html(ui.score_html(mine["rating"]), width="content")
            if st.button("Edit rating", icon=":material/edit:"):
                rate_dialog(media_type, int(tmdb_id))
            with st.popover("Remove rating", icon=":material/delete:", type="tertiary"):
                st.markdown(f"Remove **{t['title']}** and your review?")
                st.button("Remove", type="primary", on_click=remove_rating, args=(t["key"], t["title"]))
        else:
            if st.button("I've seen it, rate it", type="primary", icon=":material/star:"):
                rate_dialog(media_type, int(tmdb_id))
            save_button(t, "details", label=True, stretch=False)
        if t.get("trailer"):
            st.link_button("Watch the trailer", f"https://www.youtube.com/watch?v={t['trailer']}",
                           icon=":material/play_arrow:")
    st.write("")

    main, side = st.columns([2.3, 1], gap="large")
    with main:
        st.html(ui.synopsis_html(t))
        if mine and mine["review"]:
            st.write("")
            with st.container(border=True):
                st.markdown("**What you wrote**")
                st.html(f'<div class="cq-review" style="-webkit-line-clamp:12;font-size:1.05rem">'
                        f'“{ui.escape(mine["review"])}”</div>')
        cast = t.get("cast_full", [])
        if cast:
            st.markdown("#### Starring")
            st.html(ui.billing_html(cast[:12]))
            if len(cast) > 12:
                with st.expander(f"Full cast ({len(cast)})"):
                    st.html(ui.billing_html(cast[12:]))
        if t.get("crew"):
            st.markdown("#### Behind the camera")
            st.html(ui.crew_html(t["crew"]))
        if t.get("keywords"):
            st.markdown("#### Themes")
            st.html(ui.chips(t["keywords"][:18]))

    with side:
        st.html(ui.poster_card(t, show_text=False))
        if rec and rec.reasons:
            with st.container(border=True):
                st.markdown("**Why Critiq picked it**")
                st.html('<ul class="cq-reasons">' +
                        "".join(f"<li>{ui.escape(x)}</li>" for x in rec.reasons) + "</ul>")
        st.html(ui.providers_html(t["providers"], t["region"]))
        st.html('<div class="cq-panel"><h5>Details</h5>' + ui.rows_html([
            ("Released" if media_type == "movie" else "Aired", ui.escape(t.get("released", ""))),
            ("Language", ui.escape(t.get("language", ""))),
            ("Country", ui.escape(", ".join(t.get("countries", [])))),
            ("Network", ui.escape(", ".join(t.get("networks", [])))),
            ("Status", ui.escape(t.get("status", ""))),
        ]) + "</div>")

    similar = [s for s in t.get("similar", []) if s["key"] not in watched_by_key][:GRID]
    if similar:
        st.write("")
        st.markdown("#### If you like this")
        for chunk, cols in rows(similar, GRID):
            for s, col in zip(chunk, cols):
                with col:
                    st.html(ui.poster_card(s, href=link(s["key"])))


if qp.get("title"):
    details_page(qp["title"])
    footer()
    st.stop()


# ===================================================================== HOME
def start_from_home():
    """Apply the chosen mood (if any) to saved preferences, then open Discover and run it."""
    mood = st.session_state.get("mood")
    if mood:
        vibe, genres, media = MOODS[mood]
        p = store.get_prefs(user_id)
        p.update(vibe=vibe, genres=genres)
        store.save_prefs(user_id, p)
        st.session_state.rec_kind = media
    go_to("Discover", autorun=True)


def home_sig() -> tuple:
    """What the home picks depend on: your ratings and your streaming services."""
    services = prefs.get("services") or []
    return (len(watched), round(sum(w["rating"] for w in watched), 2), tuple(services))


def home_picks_ready() -> bool:
    mem = rec_memory().get(f"{user_id}|home")
    return bool(mem) and mem[0] == home_sig()


def home_picks() -> list:
    """Your top picks for the home screen, recomputed only when your ratings or
    streaming services change (the home skeleton covers that wait)."""
    if home_picks_ready():
        return rec_memory()[f"{user_id}|home"][1]
    p = {"services": prefs.get("services") or []}
    candidates, _ = gather_candidates(watched, p, "both")
    picks = attach_and_filter(recommend(watched, candidates, p, "both", top_n=40), omdb, want=10)
    rec_memory()[f"{user_id}|home"] = (home_sig(), picks)
    return picks


def next_feature(n: int):
    st.session_state.feature_idx = (st.session_state.get("feature_idx", 0) + 1) % max(n, 1)


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def vs_imdb(pairs: tuple) -> float | None:
    """Average gap between your stars and IMDb (/2) over up to 40 recent ratings."""
    if not omdb:
        return None
    from omdb import taste_vs_imdb
    scores = omdb.ratings_many([imdb_id for imdb_id, _ in pairs])
    return taste_vs_imdb([(mine, s["imdb"]) for (_, mine), s in zip(pairs, scores)])


def safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


if page == "Home":
    when = part_of_day()
    stage = st.empty()

    def home_data() -> dict:
        """Everything Home shows, fetched before anything is drawn, so the skeleton can stand in."""
        d = {"trending": [t for t in safe(tmdb.trending, []) if t["key"] not in watched_by_key]}
        if watched:
            picks = [r for r in safe(home_picks, []) if r.title["key"] not in watched_by_key]
            top = max((r.score for r in picks), default=1) or 1
            d["features"] = [(r.title, "Tonight's feature", r.reasons[0] if r.reasons else "",
                              f"{max(1, min(99, round(100 * r.score / top)))}% match") for r in picks]
        else:
            d["features"] = [(t, "Trending this week", "Rate a few things and this becomes your own pick.", "")
                             for t in d["trending"][:8]]
        d["feature"] = None
        if d["features"]:
            idx = st.session_state.get("feature_idx", 0) % len(d["features"])
            base, label, why, match = d["features"][idx]
            t = {**base, **safe(lambda: tmdb.full_details(base["media_type"], base["id"]), {})}
            for k in ("imdb", "rt"):                       # keep scores already looked up
                if base.get(k) is not None:
                    t[k] = base[k]
            facts = [", ".join(x for x in [t.get("year", ""), ui.kind(t), t.get("runtime", "")] if x),
                     ", ".join(ui.score_bits(t) + ([match] if match else []))]
            d["feature"] = (t, label, why, facts)
        d["fav"], d["more"] = None, []
        if watched:
            d["fav"] = max(watched, key=lambda w: (w["rating"], w.get("updated_at", "")))
            fav_t = d["fav"]["title"]
            similar = safe(lambda: tmdb.full_details(fav_t["media_type"], fav_t["id"]), {})
            d["more"] = [s for s in similar.get("similar", []) if s["key"] not in watched_by_key]
        d["services"] = prefs.get("services") or []
        d["fresh"] = ([t for t in safe(lambda: tmdb.new_on_services(d["services"]), [])
                       if t["key"] not in watched_by_key] if d["services"] else [])
        return d

    # the skeleton shows on the first Home of a session (right after sign-in) and whenever the
    # picks have to be worked out again; otherwise the data is cached and Home draws at once
    if not st.session_state.get("home_drawn") or (watched and not home_picks_ready()):
        home = load_into(stage, "home", home_data)
    else:
        home = home_data()
    trending = home["trending"]

    with stage.container():
        # ---------- tonight's feature ----------
        if home["feature"]:
            t, label, why, facts = home["feature"]
            ambient(t)
            st.html(ui.feature_html(t, when, label, facts, why, link(t["key"])))
            with st.container(key="feature_actions", horizontal=True, gap="small"):
                if t.get("trailer"):
                    st.link_button("Watch the trailer", f"https://www.youtube.com/watch?v={t['trailer']}",
                                   icon=":material/play_arrow:", type="primary")
                save_button(t, "feature", label=True, stretch=False)
                if len(home["features"]) > 1:
                    st.button("Not tonight", icon=":material/skip_next:", on_click=next_feature,
                              args=(len(home["features"]),), help="Show the next pick")
        else:
            st.html(ui.home_html(when, len(watched)))

        # ---------- moods + main actions ----------
        st.write("")
        st.pills("Mood", list(MOODS), key="mood", label_visibility="collapsed")
        with st.container(horizontal=True, vertical_alignment="center"):
            st.button("Find my next watch", type="primary", icon=":material/auto_awesome:",
                      on_click=start_from_home)
            st.button("Movie night with a friend", icon=":material/group:", on_click=go_to,
                      args=("Movie night",))
            if watched:
                recent = sorted(watched, key=lambda w: w.get("updated_at", ""), reverse=True)[:40]
                pairs = tuple((w["title"].get("imdb_id"), w["rating"]) for w in recent
                              if w["title"].get("imdb_id"))
                avg = sum(w["rating"] for w in watched) / len(watched)
                st.html(ui.stats_line(len(watched), avg, vs_imdb(pairs) if pairs else None), width="content")

        # ---------- film strips ----------
        if watchlist:
            st.html(ui.strip_html("Your watchlist", [w["title"] for w in watchlist[:24]], link))
        if home["more"]:
            st.html(ui.strip_html(f"Because you loved {home['fav']['title']['title']}", home["more"], link))
        if home["fresh"]:
            services = home["services"]
            names = " & ".join(services[:2]) + (" and more" if len(services) > 2 else "")
            st.html(ui.strip_html(f"New on {names}", home["fresh"], link))
        if trending:
            st.html(ui.strip_html("Trending this week", trending, link))
        last = [r.title for r in rec_memory().get(user_id, []) if r.title["key"] not in watched_by_key]
        if last:
            st.html(ui.strip_html("From your last search", last, link))
        if not watched and not watchlist:
            st.write("")
            st.caption("New here? Rate three to five things you've watched, or bring your history over "
                       "from Letterboxd in the Account menu.")
    st.session_state.home_drawn = True

# ===================================================================== RATE
if page in ("Rate", "Library"):
    for w in sorted(watched, key=lambda w: w.get("updated_at", ""), reverse=True):
        if w["title"].get("backdrop"):
            ambient(w["title"])
            break

if page == "Rate":
    query = st.text_input("Search", key="q", on_change=on_search_change,
                          placeholder="Search for a movie or show you've watched",
                          icon=":material/search:", label_visibility="collapsed")
    if query:
        try:
            results = tmdb.search_titles(query)[:12]
        except TMDBError as e:
            st.error(str(e))
            results = []
        if not results:
            st.html(ui.empty_html(f"Nothing found for “{query}”",
                                  "Check the spelling, or try the original title."))
        for chunk, cols in rows(results, GRID):
            for r, col in zip(chunk, cols):
                key = f"{r['media_type']}:{r['id']}"
                mine = watched_by_key.get(key)
                with col:
                    st.html(ui.poster_card(r, stub=mine["rating"] if mine else None, href=link(key)))
                    if st.button("Edit rating" if mine else "Rate", key=f"rate-{key}",
                                 type="tertiary" if mine else "secondary", width="stretch"):
                        rate_dialog(r["media_type"], r["id"])
    else:
        if not watched:
            st.html(ui.empty_html("Start with something you loved", "Search it, rate it, say why."))
            st.write("")
            if st.button("Or import from Letterboxd", icon=":material/upload:"):
                letterboxd_dialog()
        else:
            st.markdown("#### Recently rated")
            recent = sorted(watched, key=lambda w: w.get("updated_at", ""), reverse=True)[:GRID]
            for chunk, cols in rows(recent, GRID):
                for w, col in zip(chunk, cols):
                    with col:
                        st.html(ui.poster_card(w["title"], stub=w["rating"], review=w["review"],
                                               href=link(w["title"]["key"]), even=True))
                        rating_actions(w["title"], "recent")

# ================================================================== LIBRARY
elif page == "Library":
    shelf = st.segmented_control("Shelf", ["Rated", "Watchlist"], default="Rated", required=True,
                                 key="lib_shelf", label_visibility="collapsed",
                                 format_func=lambda s: f"{s}  {len(watched) if s == 'Rated' else len(watchlist)}")
    st.write("")
    if shelf == "Watchlist":
        if not watchlist:
            st.html(ui.empty_html("Nothing saved yet",
                                  "Hit “Save for later” on any title and it waits for you here."))
        for chunk, cols in rows(watchlist, GRID):
            for w, col in zip(chunk, cols):
                t = w["title"]
                with col:
                    st.html(ui.poster_card(t, href=link(t["key"])))
                    with st.container(horizontal=True, gap="small", wrap=False):
                        if st.button("Watched it", key=f"wl-rate-{t['key']}", width="stretch",
                                     help="Rate it, and it moves to your Rated shelf"):
                            rate_dialog(t["media_type"], t["id"])
                        save_button(t, "wl")
    elif not watched:
        st.html(ui.empty_html("Your library is empty",
                              "Everything you rate lands here, with your review."))
    else:
        c1, c2, c3 = st.columns([2, 3, 2], vertical_alignment="center")
        with c1:
            st.markdown(f"#### {len(watched)} rated")
        with c2:
            sort = st.segmented_control("Sort", ["Highest rated", "Lowest rated", "Recent", "A to Z"],
                                        default="Highest rated", required=True,
                                        label_visibility="collapsed", key="lib_sort")
        with c3:
            kind_filter = st.segmented_control("Type", ["All", "Movies", "Shows"], default="All",
                                               required=True, label_visibility="collapsed",
                                               key="lib_kind")
        items = [w for w in watched if kind_filter == "All"
                 or (kind_filter == "Movies") == (w["title"]["media_type"] == "movie")]
        sorters = {
            "Highest rated": lambda w: (-w["rating"], w["title"]["title"]),
            "Lowest rated": lambda w: (w["rating"], w["title"]["title"]),
            "Recent": lambda w: w.get("updated_at", ""),
            "A to Z": lambda w: w["title"]["title"].lower(),
        }
        items.sort(key=sorters[sort], reverse=(sort == "Recent"))
        st.write("")
        for chunk, cols in rows(items, GRID):
            for w, col in zip(chunk, cols):
                t = w["title"]
                with col:
                    st.html(ui.poster_card(t, stub=w["rating"], review=w["review"], even=True,
                                           href=link(t["key"])))
                    rating_actions(t, "lib")


# ================================================================= DISCOVER
def clear_filters():
    p = store.get_prefs(user_id)
    p.update(actors=[], directors=[], vibe="", genres=[], year_min=None, year_max=None,
             min_score=0.0, min_imdb=0.0, min_rt=0, services=[])
    store.save_prefs(user_id, p)
    st.session_state.rec_kind = "Both"


def rec_grid(recs, where: str, fit=None, friend_name: str = ""):
    """Recommendation cards. `fit` maps key -> (you%, friend%) on movie nights."""
    top = max(r.score for r in recs) or 1
    for chunk, cols in rows(recs, REC_GRID):
        for r, col in zip(chunk, cols):
            t = r.title
            with col:
                if fit:
                    st.html(ui.poster_card(t, href=link(t["key"]), extra_meta=card_meta(t)))
                    st.html(ui.fit_html(*fit[t["key"]], friend_name))
                    st.html('<ul class="cq-reasons">' + "".join(
                        f"<li>{ui.escape(x)}</li>" for x in r.reasons) + "</ul>")
                else:
                    pct = max(1, min(99, round(100 * r.score / top)))
                    st.html(ui.poster_card(t, match=pct, reasons=r.reasons, href=link(t["key"]),
                                           extra_meta=card_meta(t)))
                with st.container(horizontal=True, gap="small", wrap=False):
                    if st.button("Seen it? Rate it", key=f"seen-{where}-{t['key']}", width="stretch",
                                 icon=":material/star:"):
                        rate_dialog(t["media_type"], t["id"])
                    save_button(t, where)


if page == "Discover":
    # ---------- 1. search anything ----------
    dq = st.text_input("Search", key="dq", on_change=on_search_change, args=("dq",),
                       placeholder="Search any movie or show",
                       icon=":material/search:", label_visibility="collapsed")
    if dq:
        try:
            found = tmdb.search_titles(dq)[:12]
        except TMDBError as e:
            st.error(str(e))
            found = []
        if not found:
            st.html(ui.empty_html(f"Nothing found for “{dq}”",
                                  "Check the spelling, or try the original title."))
        for chunk, cols in rows(found, GRID):
            for r, col in zip(chunk, cols):
                key = f"{r['media_type']}:{r['id']}"
                mine = watched_by_key.get(key)
                with col:
                    st.html(ui.poster_card({**r, "key": key}, stub=mine["rating"] if mine else None,
                                           href=link(key)))
                    if not mine:
                        save_button({**r, "key": key}, "search", label=True)
        st.write("")
        st.caption("Click a poster for the full details, ratings and where to watch.")
        st.divider()

    # ---------- 2. filters, tucked away until you want them ----------
    services_all = service_names(tmdb.region)
    active = sum(bool(x) for x in [prefs["actors"], prefs["directors"], prefs["vibe"], prefs["genres"],
                                    prefs["year_min"] or prefs["year_max"],
                                    prefs.get("min_imdb"), prefs.get("min_rt"), prefs.get("services")])
    st.session_state.setdefault("rec_kind", "Both")
    # static label + key so the panel stays open while you change things
    with st.expander("Filters", icon=":material/tune:", key="filters_box"):
        if active:
            st.caption(f"{active} filter{'s' * (active != 1)} on. They're saved for next time.")
        a_col, d_col = st.columns(2)
        actors_raw = a_col.text_input("Actors", value=", ".join(prefs["actors"]),
                                      placeholder="Cillian Murphy, Zendaya",
                                      help="Only titles with at least one of these actors")
        dirs_raw = d_col.text_input("Directors", value=", ".join(prefs["directors"]),
                                    placeholder="Christopher Nolan, Vince Gilligan",
                                    help="Only titles directed or created by one of these people")
        vibe = st.text_input("In the mood for", value=prefs.get("vibe", ""),
                             placeholder="A slow-burn crime thriller with a twist ending")
        g_col, y_col = st.columns([1.2, 1], gap="medium")
        genres = g_col.multiselect("Genres", FILTER_GENRES,
                                   default=[x for x in prefs.get("genres", []) if x in FILTER_GENRES],
                                   placeholder="Any genre")
        years = y_col.slider("Released between", YEAR_FLOOR, THIS_YEAR,
                             (prefs.get("year_min") or YEAR_FLOOR, prefs.get("year_max") or THIS_YEAR))
        services = st.multiselect(
            f"Only what's on my streaming services ({tmdb.region})", services_all,
            default=[s for s in prefs.get("services", []) if s in services_all],
            placeholder="Any service, or none at all",
            help="Included with your subscription (or free). Rentals and purchases don't count.")
        i_col, r_col, k_col = st.columns([1, 1, 1.1], gap="medium")
        no_omdb = "Add a free OMDB_API_KEY to secrets.toml to use this" if not omdb else None
        min_imdb = i_col.slider("Minimum IMDb rating", 0.0, 9.5, float(prefs.get("min_imdb") or 0.0),
                                step=0.5, format="%.1f", disabled=not omdb, help=no_omdb)
        min_rt = r_col.slider("Minimum Rotten Tomatoes", 0, 100, int(prefs.get("min_rt") or 0),
                              step=5, format="%d%%", disabled=not omdb,
                              help=no_omdb or "Titles without a Rotten Tomatoes score (most shows) "
                                              "are skipped when this is above 0%")
        with k_col:
            st.segmented_control("Show me", ["Both", "Movies", "Shows"], required=True, key="rec_kind")
        st.button("Clear all filters", type="tertiary", icon=":material/close:", on_click=clear_filters)

        current = {
            "actors": split_names(actors_raw), "directors": split_names(dirs_raw), "vibe": vibe,
            "genres": genres,
            "year_min": years[0] if years[0] > YEAR_FLOOR else None,   # full range = no filter
            "year_max": years[1] if years[1] < THIS_YEAR else None,
            "min_score": 0.0, "min_imdb": min_imdb, "min_rt": min_rt, "services": services,
        }
        if current != prefs:
            store.save_prefs(user_id, current)   # saves as you go
            prefs = current
    media = st.session_state.rec_kind

    # ---------- 3. recommendations ----------
    go = st.button("Find my next watch", type="primary", icon=":material/auto_awesome:")
    go = go or st.session_state.pop("autorun", False)

    has_signal = (watched or prefs["actors"] or prefs["directors"] or prefs["vibe"] or prefs["genres"]
                  or prefs["year_min"] or prefs["year_max"] or prefs.get("services")
                  or prefs.get("min_imdb") or prefs.get("min_rt"))
    stage = st.empty()               # the results area: skeleton cards while picks are worked out
    if go and has_signal:
        media_filter = KIND[media]

        def work():
            candidates, allowed = gather_candidates(watched, prefs, media_filter)
            ranked = recommend(watched, candidates, prefs, media_filter, top_n=60, allowed_keys=allowed)
            return attach_and_filter(ranked, omdb, prefs.get("min_imdb") or 0,
                                     prefs.get("min_rt") or 0, want=12)

        rec_memory()[user_id] = load_into(stage, "grid", work)

    recs = [r for r in rec_memory().get(user_id, []) if r.title["key"] not in watched_by_key]
    with stage.container():
        if go and not has_signal:
            st.html(ui.empty_html("Nothing to go on yet",
                                  "Rate a few titles, or open Filters and pick a genre, actor or director."))
        elif go and not rec_memory()[user_id]:
            st.html(ui.empty_html("No matches with these filters",
                                  "Try more genres, a wider year range, more services or lower "
                                  "minimum scores."))
        if recs:
            ambient(recs[0].title)
            st.write("")
            spin_button([r.title for r in recs], [r.score for r in recs], "spin-discover")
            rec_grid(recs, "disc")
        elif not go:
            st.caption("Recommendations use your ratings, the words in your reviews and any filters "
                       "you set. Click any poster for details.")


# ============================================================== MOVIE NIGHT
def friend_from_upload():
    up = st.session_state.get("friend_file")
    if not up:
        st.session_state.pop("friend_backup", None)
        return
    try:
        data = json.load(up)
        name = up.name.rsplit(".", 1)[0].replace("critiq-ratings", "").strip(" -_") or "Your friend"
        st.session_state.friend_backup = {"name": name.title(), "watched": data.get("watched", [])}
    except Exception:
        st.session_state.friend_backup = None


if page == "Movie night":
    st.markdown("### Movie night")
    st.caption("Blend your taste with a friend's and find something you'll both enjoy.")

    # ---- who's the friend? an invite link (deployed) or their backup file (anywhere)
    friend_name, friend_watched, friend_problem = None, None, None
    token = qp.get("with")
    if token:
        found = store.user_by_token(token)
        if not found:
            friend_problem = "That invite link isn't valid any more. Ask your friend for a new one."
        elif found[0] == user_id:
            friend_problem = "That's your own invite link. Send it to a friend instead."
        else:
            friend_name = found[1] or found[0].split("@")[0]
            friend_watched = store.get_watched(found[0])
    elif st.session_state.get("friend_backup"):
        fb = st.session_state.friend_backup
        friend_name, friend_watched = fb["name"], fb["watched"]

    invite, upload_col = st.columns(2, gap="large")
    with invite:
        with st.container(border=True):
            st.markdown("**Invite a friend**")
            if auth_configured():
                my_token = store.share_token(user_id, user_label or "")
                base = "{0.scheme}://{0.netloc}{0.path}".format(urlsplit(st.context.url or ""))
                st.caption("Send them this link. Once they sign in, you'll both see the same picks.")
                st.code(f"{base}?{urlencode({'page': 'Movie night', 'with': my_token})}", language=None)
            else:
                st.caption("Invite links work once Critiq is online with sign-in. For now, swap "
                           "backups: send them yours, and load theirs on the right.")
                st.download_button("Download my ratings to send", icon=":material/download:",
                                   data=json.dumps(store.export_user(user_id), indent=2),
                                   file_name="critiq-ratings.json", mime="application/json")
    with upload_col:
        with st.container(border=True):
            st.markdown("**Or use a friend's backup**")
            st.caption("They download it from Account → Download my ratings.")
            st.file_uploader("Friend's critiq-ratings.json", type="json", key="friend_file",
                             on_change=friend_from_upload, label_visibility="collapsed")
            if st.session_state.get("friend_backup") is None and st.session_state.get("friend_file"):
                st.error("That doesn't look like a Critiq backup file.")

    if friend_problem:
        st.warning(friend_problem)
    night_key = f"{user_id}|night|{token or friend_name or ''}"

    if friend_watched is not None:
        st.write("")
        if not watched or not friend_watched:
            who = "You haven't" if not watched else f"{friend_name} hasn't"
            st.html(ui.empty_html(f"{who} rated anything yet",
                                  "Movie night needs a few ratings from both of you."))
        else:
            st.markdown(f"#### You ({len(watched)} ratings) + {friend_name} ({len(friend_watched)} ratings)")
            st.session_state.setdefault("night_kind", "Both")
            with st.container(horizontal=True, vertical_alignment="bottom"):
                st.segmented_control("Show me", ["Both", "Movies", "Shows"], required=True,
                                     key="night_kind")
                only_mine = st.toggle("Only on my streaming services",
                                      disabled=not prefs.get("services"),
                                      help=None if prefs.get("services") else
                                      "Pick your services under Discover → Filters first")
                st.space("stretch")
                go_night = st.button("Find something for both of us", type="primary",
                                     icon=":material/auto_awesome:")
            stage = st.empty()       # skeleton cards while the blend is worked out
            if go_night:
                media_filter = KIND[st.session_state.night_kind]
                night_prefs = {"services": prefs.get("services") if only_mine else []}

                def night_work():
                    both_rated = watched + friend_watched
                    keys = build_candidate_keys(both_rated, [], [], limit=140)
                    if night_prefs["services"]:
                        for mt in (["movie", "tv"] if media_filter == "both" else [media_filter]):
                            keys += tmdb.discover(mt, [], None, None, 0, services=night_prefs["services"])
                    candidates = tmdb.details_many(list(dict.fromkeys(keys)))
                    mine = recommend(watched, candidates, night_prefs, media_filter, top_n=500)
                    theirs = recommend(friend_watched, candidates, night_prefs, media_filter, top_n=500)
                    picks = blend(mine, theirs, top_n=24)
                    if omdb:
                        for p, s in zip(picks, omdb.ratings_many([p.title.get("imdb_id") for p in picks])):
                            p.title.update(imdb=s["imdb"], rt=s["rt"])
                    return picks[:12]

                rec_memory()[night_key] = load_into(stage, "grid", night_work)

            with stage.container():
                if go_night and not rec_memory()[night_key]:
                    st.html(ui.empty_html("Nothing you'd both like",
                                          "Try Movies and Shows together, or turn off the services filter."))
                picks = [p for p in rec_memory().get(night_key, []) if p.title["key"] not in watched_by_key]
                if picks:
                    def theirs(reason: str) -> str:
                        return (reason.replace("Because you rated", f"{friend_name} rated")
                                      .replace("You wrote about", f"{friend_name} wrote about"))

                    as_recs = [Recommendation(p.title, p.score,
                                              [x.replace("Because you rated", "You rated") for x in p.reasons_you[:1]]
                                              + [theirs(x) for x in p.reasons_friend[:1]])
                               for p in picks]
                    fit = {p.title["key"]: (p.you, p.friend) for p in picks}
                    ambient(picks[0].title)
                    st.write("")
                    spin_button([p.title for p in picks], [p.score for p in picks], "spin-night")
                    rec_grid(as_recs, "night", fit=fit, friend_name=friend_name)

footer(wall=wall_posters([w["title"] for w in watched] + [w["title"] for w in watchlist], api_key))
