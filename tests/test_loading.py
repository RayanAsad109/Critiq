"""Skeleton loading and the "Admitted" stamp shown right after sign-in."""
import re
from datetime import date

import ui


def _style_body(css: str) -> str:
    return re.sub(r"</?style>", "", css)


def test_skeleton_css_is_safe_for_st_html_and_calm():
    body = _style_body(ui.SKELETON_CSS)
    assert not re.search(r"[<>]", body)                  # st.html drops a style block with raw brackets
    assert "#2A1722" in body and "#3A2030" in body
    assert "D9A956" not in body.upper() and "F6D58E" not in body.upper()   # no gold in the shimmer
    assert "prefers-reduced-motion" in body
    assert "aspect-ratio: 2 / 3" in body


def test_home_skeleton_has_hero_and_poster_rows():
    html = ui.skeleton_html("home")
    assert 'aria-busy="true"' in html and 'role="status"' in html
    assert "cq-sk-hero" in html and "cq-sk-title" in html
    assert html.count("cq-sk-strip\"") == 2
    assert html.count("cq-sk-poster") == 18


def test_grid_skeleton_has_cards():
    html = ui.skeleton_html("grid")
    assert html.count('class="cq-sk-card"') == 8


def test_admitted_stamp():
    html = ui.admitted_html("Mon 23 Nov", "E5")
    assert "ADMITTED" in html and "CRITIQ" in html and "Mon 23 Nov" in html and "E5" in html
    assert 'aria-hidden="true"' in html
    assert "<svg" not in html and "<script" not in html
    css = _style_body(ui.ADMIT_CSS)
    assert not re.search(r"[<>]", css)
    assert "pointer-events: none" in css and "visibility: hidden" in css
    assert "#9E2A2B" in css and "scale(1.6)" in css
    assert "prefers-reduced-motion" in css


def test_ticket_seat_matches_the_sign_in_ticket():
    day = date(2026, 11, 23)
    n = day.toordinal()
    assert ui.ticket_seat(day) == f"{'DEFGHJK'[n % 7]}{n % 17 + 4}"


def test_countdown_is_gone():
    for name in ("lights_down_html", "curtain_reveal_html"):
        assert not hasattr(ui, name)
    assert "cq-leader" not in ui.EFFECTS_CSS and "cq-curtain" not in ui.EFFECTS_CSS
    assert "@keyframes cq-fade" in ui.EFFECTS_CSS            # the reel result still fades in
