"""In-session navigation (no links that reload the app) and the button-only sign-in."""
import re
from pathlib import Path

import ui

ROOT = Path(__file__).resolve().parent.parent
TITLE = {"key": "movie:1", "id": 1, "media_type": "movie", "title": "Arrival", "year": "2016",
         "poster": "https://image.tmdb.org/t/p/w342/a.jpg", "backdrop": "https://image.tmdb.org/t/p/w1280/b.jpg"}


def test_posters_strips_hero_and_marquee_carry_no_links():
    html = (ui.poster_card(TITLE, stub=4.5, review="great", reasons=["Because"]) + ui.strip_item_html(TITLE)
            + ui.feature_html(TITLE, "tonight", "Tonight's feature", ["2016"], "why") + ui.header_html()
            + ui.reel_html([TITLE, TITLE], 1, "abc123"))
    assert "<a " not in html and "href" not in html


def test_ticket_is_html_plus_a_real_button():
    main = ui.ticket_main_html("Mon 23 Nov", "E5", invited=True)
    assert "CRITIQ" in main and "Movie night for two" in main and "<a " not in main
    assert "Sign in, then open your invite link again." in main
    css = re.sub(r"</?style>", "", ui.SIGNIN_CSS)
    assert not re.search(r"[<>]", css)              # st.html would strip the block
    assert ".st-key-google button" in css and "data:image/svg+xml," in css
    assert "<svg" not in ui.signin_wall_html(["https://image.tmdb.org/t/p/w342/p.jpg"])


def test_no_auto_login_anywhere():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert not re.search(r"""["']signin["']|\?signin|signin=""", app)   # no ?signin=1 handling or links
    assert app.count("st.login()") == 1                         # only in the button's callback
    assert re.search(r'st\.button\("Sign in with Google", key="google", on_click=start_login\)', app)
    for page in (ROOT / "landing").rglob("*.html"):
        if "shots" in page.parts or "chrome-check" in page.parts:
            continue
        assert "signin=1" not in page.read_text(encoding="utf-8", errors="ignore"), page


def test_type_and_width():
    css = ui.CSS + ui.HOME_CSS
    assert "max-width: 1300px" in css and "--serif:" in css and "font-synthesis: none" in css
    assert "max(480px, 58vh)" in ui.HOME_CSS
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "Instrument+Serif" in config and "family=Geist:wght@400;500" in config
    assert "headingFontWeights = [400, 400, 400, 400, 400, 400]" in config
    for rule in (ui.CSS + ui.HOME_CSS + ui.POLISH_CSS).split("}"):
        if "var(--sign)" in rule:                                 # Archivo signage keeps its weights
            continue
        for weight in re.findall(r"font-weight:\s*(\d+)", rule):
            assert weight in ("400", "500"), rule


def test_invites_are_not_matched_by_ip_or_browser():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    for gone in ("ip_address", "User-Agent", "pending_invites", "browser_id", "resume_invite"):
        assert gone not in app, gone
    assert 'token = qp.get("with")' in app                     # signed in, the link opens Movie night


def test_strips_have_fixed_width_items_and_scroll():
    css = re.sub(r"</?style>", "", ui.HOME_CSS)
    assert not re.search(r"[<>]", css)
    assert "--strip-w: 180px" in css and "--strip-w: 140px" in css and "--strip-w: 120px" in css
    assert "flex: 0 0 var(--strip-w) !important" in css and "max-width: var(--strip-w) !important" in css
    assert "scroll-snap-type: x mandatory" in css and "scroll-snap-align: start" in css
    assert "scrollbar-width: none" in css and "animation-timeline: scroll(self inline)" in css
    assert "font-family: var(--sans); font-weight: 500;" in css and "font-size: 15px" in css
    assert "-webkit-line-clamp: 2" in css and "font-size: 13px" in css
    assert "max(480px, 58vh)" in css
    item = ui.strip_item_html({"key": "tv:2", "media_type": "tv", "title": "Severance", "year": "2022"})
    assert 'class="n">Severance' in item and "Show, 2022" in item


def test_ticket_is_bigger_and_centred_on_desktop_only():
    css = re.sub(r"</?style>", "", ui.SIGNIN_CSS)
    desktop, phone = css.split("@media (max-width: 640px)")[0], css.split("@media (max-width: 640px)")[1]
    assert "width: min(820px, 100%) !important" in desktop and "margin-inline: auto !important" in desktop
    assert "circle var(--notch)" in desktop and "--notch: 16px" in desktop
    assert "font-size: 4.3rem" in desktop and "font-size: 1.1rem !important" in desktop
    assert ".cq-t-name { font-size: 2.8rem" in phone and "--cut: 100%" in phone    # phones unchanged, stacked


def test_labels_carry_no_counts():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'format_func=lambda p: f"{icons[p]} {p}",' in app             # nav pill: just "Library"
    shelf = app[app.index('st.segmented_control("Shelf"'):]
    assert "format_func" not in shelf[:shelf.index(")") + 1]            # tabs: just "Rated" / "Watchlist"
    assert 'st.markdown(f"#### {len(watched)} rated")' in app
    assert 'st.markdown(f"#### {len(watchlist)} saved")' in app and '"Nothing saved yet"' in app
