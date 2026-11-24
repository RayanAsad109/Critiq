"""The poster wall behind the sign-in page and the signed-in pages."""
import re

import ui

POSTERS = [f"https://image.tmdb.org/t/p/w342/p{i}.jpg" for i in range(12)]


def test_wall_has_seven_drifting_columns():
    html = ui.poster_wall_html(POSTERS)
    assert html.count('class="cq-wall-col"') == 7
    assert 'aria-hidden="true"' in html


def test_no_posters_no_wall():
    assert ui.poster_wall_html([]) == ""
    assert "cq-wall-app" not in ui.app_wall_html([])


def test_app_wall_is_held_faint_and_uses_small_posters():
    html = ui.app_wall_html(POSTERS)
    assert html.startswith('<div class="cq-wall-app" aria-hidden="true"><div class="cq-wall"')
    assert "/w185/" in html and "/w342/" not in html
    assert 'class="cq-grain"' in html


def test_signin_keeps_its_full_wall():
    html = ui.signin_wall_html(POSTERS)
    assert '<div class="cq-wall" aria-hidden="true">' in html
    assert "cq-wall-app" not in html and "/w342/" in html


def test_wall_css_is_safe_for_st_html():
    # raw angle brackets inside a style block get the whole block stripped by st.html
    body = ui.WALL_CSS.replace("<style>", "").replace("</style>", "")
    assert not re.search(r"[<>]", body)
    assert "prefers-reduced-motion" in body and "repeat(4, 1fr)" in body
    assert "pointer-events: none" in body
