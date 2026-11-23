"""Visual layer for Critiq: global CSS and small HTML builders.

Palette (screening room):
  velvet  #1C0F17  page background
  curtain #2A1722  raised surfaces
  seam    #45293A  borders
  brass   #D9A956  accent, ratings, the marquee
  light   #F2E8DA  text (projector light)
  usher   #A38E99  secondary text
"""

from __future__ import annotations

from html import escape

CSS = """
<style>
:root {
  --velvet: #1C0F17; --curtain: #2A1722; --seam: #45293A;
  --brass: #D9A956; --bulb: #F6D58E; --light: #F2E8DA; --usher: #A38E99;
  --sign: "Archivo", "Arial Narrow", sans-serif;     /* signage only: marquee, numbers, badges */
  --wine: #C4437C; --wine-empty: #4A2C3D;             /* rating stars */
}
.block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stHeaderActionElements"] { display: none !important; }   /* no link icons on headings */

/* ---- rating stars: each star fills independently, so quarter stars are exact ---- */
.cq-stars { display: inline-flex; align-items: center; gap: .06em; line-height: 1; white-space: nowrap; }
.cq-star {
  font-family: "Segoe UI Symbol", "Apple Symbols", "DejaVu Sans", sans-serif;
  background: linear-gradient(90deg, var(--wine) var(--p), var(--wine-empty) var(--p));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.cq-stars-num { margin-left: .5em; font-family: var(--sign); font-weight: 700; color: var(--usher); font-size: .78em; }
.cq-cardstars { margin-top: .3rem; font-size: 1rem; }
h1, h2, h3, h4 { letter-spacing: -.005em; }

/* ---- the marquee: the one loud thing on the page ---- */
.cq-head { display: flex; align-items: center; gap: 1.6rem; flex-wrap: wrap; padding: .6rem 0 .2rem; }
.cq-marquee {
  position: relative; display: inline-block; padding: .35rem 1.3rem .25rem;
  border: 2px solid var(--brass); border-radius: 6px; background: #241320;
}
.cq-marquee::before {               /* ring of bulbs around the sign */
  content: ""; position: absolute; inset: -11px; border-radius: 11px; padding: 6px;
  background: radial-gradient(circle, var(--bulb) 0 2px, transparent 2.6px) 0 0 / 13px 13px;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  animation: cq-power-on 1.4s steps(1) 1;
}
a.cq-home-link { text-decoration: none; }
.cq-word {
  font-family: var(--sign); font-weight: 900; font-stretch: 62%; font-size: clamp(2.4rem, 5.5vw, 3.6rem);
  letter-spacing: .14em; line-height: 1; color: var(--brass);
  text-shadow: 0 0 22px rgba(217,169,86,.35);
}
.cq-tag { color: var(--usher); max-width: 30ch; line-height: 1.4; font-size: 1.02rem; font-style: italic; }
@keyframes cq-power-on { 0% {opacity: .15} 20% {opacity: 1} 32% {opacity: .3} 45% {opacity: 1} }
/* phones: two posters per row instead of one giant one */
@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"]:has(.cq-card) { flex-direction: row !important; flex-wrap: wrap !important; gap: .9rem !important; }
  [data-testid="stHorizontalBlock"]:has(.cq-card) > [data-testid="stColumn"] {
    width: calc(50% - .45rem) !important; flex: 0 0 calc(50% - .45rem) !important; min-width: 0 !important;
  }
  [data-testid="stHorizontalBlock"]:has(.cq-card) > [data-testid="stColumn"]:not(:has(.cq-card)) { display: none; }
}
@media (prefers-reduced-motion: reduce) { .cq-marquee::before { animation: none; } }

/* ---- top navigation: separate rounded pills ---- */
.st-key-nav [data-testid="stButtonGroup"] > div,
.st-key-nav [data-baseweb="button-group"] { gap: .7rem !important; flex-wrap: wrap; }
.st-key-nav button {
  border-radius: 999px !important; padding: .5rem 1.25rem !important; min-height: 2.6rem;
  font-size: 1.02rem !important; border: 1px solid var(--seam) !important;
  background: var(--curtain) !important;
}
.st-key-nav button:hover { border-color: var(--brass) !important; }
.st-key-nav button[aria-checked="true"], .st-key-nav button[kind="pillsActive"] {
  background: var(--brass) !important; color: var(--velvet) !important; border-color: var(--brass) !important;
}
.st-key-nav button[aria-checked="true"] *, .st-key-nav button[kind="pillsActive"] * { color: var(--velvet) !important; }

/* ---- posters ---- */
.cq-card { position: relative; }
.cq-poster {
  display: block; width: 100%; aspect-ratio: 2 / 3; object-fit: cover;
  border-radius: 6px; border: 1px solid var(--seam); background: var(--curtain);
}
.cq-noposter {
  display: flex; align-items: flex-end; padding: .8rem; box-sizing: border-box;
  color: var(--usher); font-weight: 600; font-size: 1.1rem;
}
.cq-stub {                          /* ticket stub with a punched notch */
  position: absolute; top: 10px; left: -5px; padding: .12rem .55rem .12rem .75rem;
  background: var(--brass); color: var(--velvet); font-family: var(--sign); font-weight: 800; font-stretch: 80%;
  font-size: .95rem; border-radius: 2px;
  -webkit-mask: radial-gradient(circle at 0 50%, transparent 4px, #000 4.5px);
          mask: radial-gradient(circle at 0 50%, transparent 4px, #000 4.5px);
  box-shadow: 0 2px 6px rgba(0,0,0,.35);
}
.cq-match {
  position: absolute; top: 10px; right: 8px; padding: .12rem .5rem;
  background: rgba(28,15,23,.88); color: var(--bulb); border: 1px solid var(--brass);
  border-radius: 3px; font-family: var(--sign); font-weight: 700; font-size: .8rem;
}
.cq-title { font-weight: 600; margin-top: .6rem; line-height: 1.2; font-size: 1.08rem; }
.cq-meta { color: var(--usher); font-size: .86rem; margin-top: .1rem; }
.cq-text { min-height: 8.9rem; }     /* keeps buttons under cards in line */
.cq-review {
  font-style: italic; color: #D8CBBE; font-size: .92rem; margin-top: .35rem; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.cq-reasons { list-style: none; padding: 0 !important; margin: .45rem 0 .2rem !important; font-size: .9rem; color: #CDBFB3; }
.cq-reasons li { position: relative; padding-left: .95rem; margin: .2rem 0; line-height: 1.35; }
.cq-reasons li::before {
  content: ""; position: absolute; left: 0; top: .5em; width: 5px; height: 5px;
  border-radius: 50%; background: var(--brass);
}

/* ---- rating readout in the dialog ---- */
.cq-score { display: flex; align-items: center; gap: .9rem; margin: -.2rem 0 .5rem; flex-wrap: wrap; }
.cq-score .cq-stars { font-size: 2.3rem; }
.cq-score .cq-stars-num { font-size: .55em; color: var(--light); }
.cq-big { font-family: var(--sign); font-size: 3.2rem; font-weight: 900; font-stretch: 62%; color: var(--brass); line-height: 1; }
.cq-big small { font-size: 1.3rem; color: var(--usher); font-weight: 600; }
.cq-verdict { color: var(--light); font-size: 1.1rem; font-style: italic; }

/* ---- links on cards ---- */
a.cq-link { color: inherit; text-decoration: none; }
a.cq-link:hover { color: var(--bulb); }
a.cq-cardlink { display: block; }
a.cq-cardlink .cq-poster { transition: border-color .15s; }
a.cq-cardlink:hover .cq-poster { border-color: var(--brass); }
a.cq-link:focus-visible { outline: 2px solid var(--bulb); outline-offset: 3px; border-radius: 6px; }

/* ---- home ---- */
.cq-home { padding: 2.6rem 0 .6rem; max-width: 820px; }
.cq-ask { font-size: clamp(2.7rem, 6.4vw, 4.8rem); line-height: 1.02; font-weight: 500;
          letter-spacing: -.02em; margin: 0; font-variation-settings: "opsz" 72; }
.cq-ask-sub { color: var(--usher); font-size: 1.25rem; line-height: 1.5; margin: 1.1rem 0 0; max-width: 48ch; }

/* ---- details page: the title is projected onto its own backdrop ---- */
.cq-screen {
  position: relative; min-height: 460px; border-radius: 10px; overflow: hidden;
  border: 1px solid var(--seam); display: flex; align-items: flex-end;
  background: radial-gradient(120% 90% at 80% 10%, #3a2030, var(--velvet)) center / cover no-repeat;
}
.cq-screen::before {
  content: ""; position: absolute; inset: 0;
  background:
    linear-gradient(90deg, rgba(28,15,23,.97) 0%, rgba(28,15,23,.86) 36%, rgba(28,15,23,.3) 70%, rgba(28,15,23,.05) 100%),
    linear-gradient(0deg, rgba(28,15,23,.92) 0%, rgba(28,15,23,0) 50%);
}
.cq-screen-body { position: relative; padding: 2.4rem 2.6rem 2.2rem; max-width: 640px; }
.cq-dtitle { font-size: clamp(2.4rem, 5vw, 3.9rem); font-weight: 600; line-height: 1.02;
             letter-spacing: -.015em; margin: 0; font-variation-settings: "opsz" 72; }
.cq-facts { color: #D8CBBE; font-size: 1.12rem; margin: .7rem 0 .2rem; }
.cq-facts b { color: var(--light); font-weight: 600; }
.cq-score-pill { display: inline-block; margin-left: .5rem; padding: .05rem .45rem; border: 1px solid var(--brass);
                 border-radius: 3px; color: var(--bulb); font-family: var(--sign); font-weight: 700;
                 font-size: .85rem; vertical-align: 2px; }
.cq-screen .cq-chips { margin-top: .9rem; }
.cq-tagline { font-style: italic; color: var(--bulb); font-size: 1.35rem; line-height: 1.35; margin: 0 0 .8rem; }
.cq-overview { font-size: 1.15rem; line-height: 1.65; max-width: 64ch; }
.cq-billing { display: grid; grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)); gap: 1rem 1.6rem; }
.cq-billing .n { font-weight: 600; font-size: 1.05rem; line-height: 1.25; }
.cq-billing .c { font-style: italic; color: var(--usher); font-size: .92rem; line-height: 1.3; }
.cq-billing .r { color: var(--usher); font-size: .85rem; }
.cq-chips { display: flex; flex-wrap: wrap; gap: .4rem; }
.cq-chip { background: rgba(42,23,34,.85); border: 1px solid var(--seam); border-radius: 3px;
           padding: .18rem .55rem; font-size: .9rem; line-height: 1.3; }
.cq-rows { margin: 0; padding: 0; display: grid; grid-template-columns: max-content 1fr; gap: .45rem 1.1rem; }
.cq-rows dt { color: var(--usher); font-size: .92rem; }
.cq-rows dd { margin: 0; font-size: .98rem; }
.cq-panel { border: 1px solid var(--seam); border-radius: 6px; padding: .9rem 1rem; margin-top: 1rem; }
.cq-panel h5 { margin: 0 0 .6rem; font-size: 1.05rem; }
.cq-prov { display: flex; align-items: center; gap: .6rem; margin: .35rem 0; font-size: .98rem; }
.cq-prov img { width: 28px; height: 28px; border-radius: 6px; }
.cq-prov span.k { margin-left: auto; color: var(--usher); font-size: .85rem; font-style: italic; }
.cq-fine { color: var(--usher); font-size: .8rem; margin-top: .5rem; }
.cq-fine a { color: var(--usher); }
@media (max-width: 640px) { .cq-screen { min-height: 380px; } .cq-screen-body { padding: 1.4rem; } }

/* ---- empty states, footer ---- */
.cq-empty {
  border: 1px dashed var(--seam); border-radius: 6px; padding: 2.2rem 1.6rem;
  color: var(--usher); line-height: 1.5; max-width: 60ch;
}
.cq-empty strong { color: var(--light); display: block; font-size: 1.2rem; margin-bottom: .3rem; }
.cq-foot {
  margin-top: 4rem; padding-top: 1rem; border-top: 1px solid var(--seam);
  color: var(--usher); font-size: .84rem; line-height: 1.5;
}
.cq-foot a { color: var(--usher); }
</style>
"""


def header_html(tagline: str = "Write it down. We'll take it from there.") -> str:
    return (f'<div class="cq-head"><a class="cq-home-link" href="?page=Home" target="_self" '
            f'aria-label="Critiq home"><div class="cq-marquee"><span class="cq-word">CRITIQ</span></div></a>'
            f'<div class="cq-tag">{escape(tagline)}</div></div>')


def kind(t: dict) -> str:
    return "Show" if t.get("media_type") == "tv" else "Movie"


def meta_line(t: dict, extra: str = "") -> str:
    parts = [kind(t)] + ([t["year"]] if t.get("year") else []) + ([extra] if extra else [])
    return ", ".join(parts)


def poster_card(t: dict, *, stub: float | None = None, match: int | None = None,
                review: str = "", reasons: list[str] | None = None, extra_meta: str = "",
                show_text: bool = True, even: bool = False, href: str | None = None) -> str:
    title = escape(t.get("title", "?"))
    if t.get("poster"):
        img = f'<img class="cq-poster" src="{escape(t["poster"])}" alt="Poster for {title}" loading="lazy">'
    else:
        img = f'<div class="cq-poster cq-noposter">{title}</div>'
    badges = ""
    if match is not None:
        badges += f'<span class="cq-match">{match}% match</span>'
    body = ""
    if show_text:
        title_html = f'<a class="cq-link" href="{escape(href)}" target="_self">{title}</a>' if href else title
        body = (f'<div class="cq-title">{title_html}</div>'
                f'<div class="cq-meta">{escape(meta_line(t, extra_meta))}</div>')
        if stub is not None:
            body += f'<div class="cq-cardstars">{stars_html(stub)}</div>'
        if review:
            body += f'<div class="cq-review">“{escape(review)}”</div>'
        if reasons:
            body += '<ul class="cq-reasons">' + "".join(f"<li>{escape(r)}</li>" for r in reasons) + "</ul>"
    if even:
        body = f'<div class="cq-text">{body}</div>'
    card = f'<div class="cq-card">{img}{badges}</div>'
    if href:
        card = (f'<a class="cq-link cq-cardlink" href="{escape(href)}" target="_self" '
                f'aria-label="Details for {title}">{card}</a>')
    return f'{card}{body}'


def home_html(when: str, n_rated: int) -> str:
    sub = ("Pick a mood, or let your reviews decide." if n_rated
           else "Rate a few things first, and say why.")
    return (f'<div class="cq-home"><h1 class="cq-ask">What\'s your next watch {escape(when)}?</h1>'
            f'<p class="cq-ask-sub">{escape(sub)}</p></div>')


def score_bits(t: dict) -> list[str]:
    """['IMDb 8.1', 'Rotten Tomatoes 94%']; empty if OMDb has no scores for it."""
    bits = []
    if t.get("imdb"):
        bits.append(f"IMDb {t['imdb']:.1f}")
    if t.get("rt") is not None:
        bits.append(f"Rotten Tomatoes {t['rt']}%")
    return bits


def screen_html(t: dict) -> str:
    """Title, facts and genres laid over the backdrop."""
    style = f' style="background-image:url({escape(t["backdrop"])})"' if t.get("backdrop") else ""
    facts = ", ".join(x for x in [t.get("year", ""), kind(t), t.get("runtime", "")] if x)
    score = "".join(f'<span class="cq-score-pill">{escape(b)}</span>' for b in score_bits(t))
    people = t.get("directors", [])
    by = ""
    if people:
        label = "Created by" if t.get("media_type") == "tv" else "Directed by"
        by = f'<div class="cq-facts">{label} <b>{escape(", ".join(people[:2]))}</b></div>'
    return (f'<div class="cq-screen"{style}><div class="cq-screen-body">'
            f'<h1 class="cq-dtitle">{escape(t["title"])}</h1>'
            f'<div class="cq-facts">{escape(facts)}{score}</div>{by}'
            f'{chips(t.get("genres", []))}</div></div>')


def synopsis_html(t: dict) -> str:
    tag = f'<p class="cq-tagline">{escape(t["tagline"])}</p>' if t.get("tagline") else ""
    return f'{tag}<div class="cq-overview">{escape(t.get("overview") or "No summary on TMDB yet.")}</div>'


def billing_html(cast: list[dict]) -> str:
    cells = "".join(f'<div><div class="n">{escape(c["name"])}</div>'
                    f'<div class="c">{escape(c.get("character") or "")}</div></div>' for c in cast)
    return f'<div class="cq-billing">{cells}</div>'


def crew_html(crew: list[tuple[str, list[str]]]) -> str:
    cells = "".join(f'<div><div class="r">{escape(job)}</div>'
                    f'<div class="n">{escape(", ".join(names))}</div></div>' for job, names in crew)
    return f'<div class="cq-billing">{cells}</div>'


def chips(items: list) -> str:
    out = [f'<span class="cq-chip">{escape(name)}</span>' for name in items]
    return f'<div class="cq-chips">{"".join(out)}</div>' if out else ""


def rows_html(pairs: list[tuple[str, str]]) -> str:
    """pairs of (label, already-safe HTML)."""
    body = "".join(f"<dt>{escape(k)}</dt><dd>{v}</dd>" for k, v in pairs if v)
    return f'<dl class="cq-rows">{body}</dl>'


def providers_html(p: dict, region: str) -> str:
    sections = [("stream", "Stream"), ("rent", "Rent"), ("buy", "Buy")]
    rows, seen = [], set()
    for k, label in sections:
        for prov in p.get(k, []):
            if (prov["name"], label) in seen:
                continue
            seen.add((prov["name"], label))
            logo = f'<img src="{escape(prov["logo"])}" alt="">' if prov.get("logo") else ""
            rows.append(f'<div class="cq-prov">{logo}{escape(prov["name"])}<span class="k">{label}</span></div>')
    if not rows:
        body = f'<div class="cq-meta">Not available to stream, rent or buy in {escape(region)} right now.</div>'
    else:
        body = "".join(rows[:8])
    link = (f' <a href="{escape(p["link"])}" target="_blank" rel="noopener">All options</a>.'
            if p.get("link") else "")
    return (f'<div class="cq-panel"><h5>Where to watch in {escape(region)}</h5>{body}'
            f'<div class="cq-fine">Availability from JustWatch via TMDB.{link}</div></div>')


def stars_html(rating: float, show_num: bool = True) -> str:
    """Five stars filled in wine colour, to the quarter star."""
    spans = "".join(
        f'<span class="cq-star" style="--p:{max(0.0, min(1.0, rating - i)) * 100:.0f}%">★</span>'
        for i in range(5))
    num = f'<span class="cq-stars-num">{rating:g}</span>' if show_num else ""
    return (f'<span class="cq-stars" role="img" aria-label="{rating:g} out of 5 stars">'
            f'{spans}{num}</span>')


def score_html(rating: float) -> str:
    return (f'<div class="cq-score">{stars_html(rating)}'
            f'<span class="cq-verdict">{verdict(rating)}</span></div>')


def verdict(r: float) -> str:
    if r >= 4.75:
        return "All-time favourite"
    if r >= 4:
        return "Loved it"
    if r >= 3:
        return "Liked it"
    if r >= 2.25:
        return "It was fine"
    if r >= 1.25:
        return "Didn't like it"
    return "Hated it"


def empty_html(headline: str, body: str) -> str:
    return f'<div class="cq-empty"><strong>{escape(headline)}</strong>{escape(body)}</div>'


FOOTER = (
    '<div class="cq-foot">Titles, posters and cast data from '
    '<a href="https://www.themoviedb.org" target="_blank" rel="noopener">TMDB</a>. '
    'This product uses the TMDB API but is not endorsed or certified by TMDB.</div>'
)


# =====================================================================
# The slot-machine reel and the movie night fit bars.
# =====================================================================
EFFECTS_CSS = """
<style>
@keyframes cq-fade { to { opacity: 1; } }   /* the reel result fades in */

/* slot-machine reel */
.cq-reel-window {
  position: relative; width: 220px; height: 330px; margin: .4rem auto 1rem; overflow: hidden;
  border-radius: 8px; border: 2px solid var(--brass);
  box-shadow: 0 0 0 6px #241320, 0 0 0 8px var(--seam), 0 0 30px rgba(217,169,86,.25);
}
.cq-reel-window::after {   /* glass shading so the strip reads as a drum */
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(0,0,0,.7), rgba(0,0,0,0) 22%, rgba(0,0,0,0) 78%, rgba(0,0,0,.7));
}
.cq-reel-strip .cq-poster { width: 220px; height: 330px; aspect-ratio: auto; border-radius: 0; border: 0; }
.cq-reel-result { text-align: center; opacity: 0; }
.cq-reel-result .t { font-size: 1.6rem; font-weight: 600; line-height: 1.15; }
.cq-reel-result .m { color: var(--usher); margin-top: .2rem; }
a.cq-btnlink {
  display: inline-block; margin-top: .9rem; padding: .5rem 1.1rem; border-radius: 4px;
  background: var(--brass); color: var(--velvet) !important; text-decoration: none; font-weight: 600;
}

/* movie night: two fit bars */
.cq-fit { display: grid; grid-template-columns: 3.6rem 1fr 2.4rem; align-items: center; gap: .45rem;
          font-size: .85rem; color: var(--usher); margin-top: .3rem; }
.cq-fit .bar { height: 6px; border-radius: 3px; background: var(--wine-empty); overflow: hidden; }
.cq-fit .bar i { display: block; height: 100%; background: var(--wine); }
.cq-fit .bar.f i { background: var(--brass); }
.cq-share { font-family: var(--sign); background: var(--curtain); border: 1px dashed var(--brass);
            border-radius: 6px; padding: .7rem .9rem; word-break: break-all; color: var(--bulb); }

@media (prefers-reduced-motion: reduce) {
  .cq-reel-strip { animation-duration: .01s !important; }
}
</style>
"""


def reel_html(titles: list[dict], winner: int, href: str, spin_id: str) -> str:
    """A strip of posters that spins and lands on titles[winner]."""
    laps = 5
    strip = titles * (laps + 1)
    stop = laps * len(titles) + winner
    cells = "".join(poster_card(t, show_text=False) for t in strip)
    w = titles[winner]
    meta = escape(meta_line(w))
    return (f'<style>@keyframes cq-spin-{spin_id} {{ from {{ transform: translateY(0); }} '
            f'to {{ transform: translateY(-{stop * 330}px); }} }}'
            f'.cq-reel-strip.s{spin_id} {{ animation: cq-spin-{spin_id} 3.4s cubic-bezier(.1,.55,.12,1) forwards; }}'
            f'.cq-reel-result.s{spin_id} {{ animation: cq-fade .4s ease 3.4s forwards; }}</style>'
            f'<div class="cq-reel-window"><div class="cq-reel-strip s{spin_id}">{cells}</div></div>'
            f'<div class="cq-reel-result s{spin_id}"><div class="t">{escape(w["title"])}</div>'
            f'<div class="m">{meta}</div>'
            f'<a class="cq-btnlink" href="{escape(href)}" target="_self">Tonight\'s feature: see details</a></div>')


def fit_html(you: int, friend: int, friend_name: str) -> str:
    return (f'<div class="cq-fit"><span>You</span><span class="bar"><i style="width:{you}%"></i></span>'
            f'<span>{you}%</span></div>'
            f'<div class="cq-fit"><span>{escape(friend_name[:8])}</span><span class="bar f">'
            f'<i style="width:{friend}%"></i></span><span>{friend}%</span></div>')


# =====================================================================
# Home: tonight's feature + film-strip rows
# =====================================================================
HOME_CSS = """
<style>
.cq-feature {
  position: relative; min-height: 520px; border-radius: 10px; overflow: hidden;
  border: 1px solid var(--seam); display: flex; align-items: flex-end;
  background-color: var(--velvet); background-repeat: no-repeat;
  background-size: cover; background-position: center 25%;
  background-image:
    linear-gradient(90deg, rgba(28,15,23,.97) 0%, rgba(28,15,23,.86) 38%, rgba(28,15,23,.25) 72%, rgba(28,15,23,.05) 100%),
    linear-gradient(0deg, rgba(28,15,23,.95) 0%, rgba(28,15,23,0) 55%),
    radial-gradient(120% 90% at 80% 10%, #3a2030, var(--velvet));
  animation: cq-feature-in .9s cubic-bezier(.6,.05,.3,1);
}
/* velvet curtains gathered at both edges of the screen */
.cq-feature::before, .cq-feature::after {
  content: ""; position: absolute; top: 0; bottom: 0; width: 34px; z-index: 1;
  background:
    linear-gradient(180deg, rgba(0,0,0,.45), rgba(0,0,0,0) 25%, rgba(0,0,0,0) 75%, rgba(0,0,0,.6)),
    repeating-linear-gradient(90deg, #4c0f26 0 7px, #66173a 7px 11px, #3a0a1c 11px 17px);
}
.cq-feature::before { left: 0; box-shadow: 6px 0 14px rgba(0,0,0,.5); }
.cq-feature::after { right: 0; box-shadow: -6px 0 14px rgba(0,0,0,.5); }
@keyframes cq-feature-in { from { clip-path: inset(0 50% 0 50%); } to { clip-path: inset(0 0 0 0); } }
.cq-feature-body { position: relative; z-index: 2; padding: 2.4rem 3.4rem 6.2rem; max-width: 700px; }
.cq-feature-ask { font-size: clamp(2.2rem, 4.6vw, 3.4rem); line-height: 1.04; font-weight: 500;
                  letter-spacing: -.02em; margin: 0 0 1.6rem; font-variation-settings: "opsz" 72; }
.cq-feature-label { color: var(--bulb); font-style: italic; font-size: 1.1rem; margin-bottom: .2rem; }
.cq-feature-title { font-size: clamp(2rem, 3.6vw, 2.8rem); font-weight: 600; line-height: 1.05; margin: 0;
                    font-variation-settings: "opsz" 72; }
.cq-feature-title a { color: var(--light); text-decoration: none; }
.cq-feature-title a:hover { color: var(--bulb); }
.cq-feature-facts { color: #D8CBBE; font-size: 1.05rem; margin: .55rem 0 0; }
.cq-feature-facts + .cq-feature-facts { margin-top: .15rem; color: var(--bulb); }
.cq-feature-why { margin-top: .45rem; }
.cq-feature-why { color: #D8CBBE; font-style: italic; font-size: 1.05rem; }
/* the action buttons are Streamlit widgets, lifted up into the bottom of the screen */
.st-key-feature_actions { margin-top: -5.4rem; padding: 0 3.4rem; position: relative; z-index: 5; }

.cq-stats-line { color: var(--usher); font-style: italic; font-size: 1.05rem; margin: .2rem 0 0; }

/* horizontal rows styled as a strip of film, sprocket holes and all */
.cq-strip-title { font-size: 1.35rem; font-weight: 600; margin: 1.4rem 0 .5rem; }
.cq-strip {
  display: flex; gap: .9rem; overflow-x: auto; scroll-snap-type: x proximity;
  padding: 24px 16px 22px; border-radius: 6px; border: 1px solid #2a1620;
  background:
    repeating-linear-gradient(90deg, rgba(242,232,218,.15) 0 10px, transparent 10px 22px) 8px 7px / 100% 8px no-repeat local,
    repeating-linear-gradient(90deg, rgba(242,232,218,.15) 0 10px, transparent 10px 22px) 8px calc(100% - 7px) / 100% 8px no-repeat local,
    #110910;
  scrollbar-width: thin; scrollbar-color: var(--brass) transparent;
}
.cq-strip::-webkit-scrollbar { height: 6px; }
.cq-strip::-webkit-scrollbar-thumb { background: var(--brass); border-radius: 3px; }
a.cq-strip-item { flex: 0 0 148px; scroll-snap-align: start; color: var(--light); text-decoration: none; }
a.cq-strip-item .cq-poster { width: 148px; }
a.cq-strip-item:hover .cq-poster { border-color: var(--brass); }
a.cq-strip-item:focus-visible { outline: 2px solid var(--bulb); outline-offset: 3px; border-radius: 6px; }
.cq-strip-item .n { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
                    margin-top: .45rem; font-size: .95rem; line-height: 1.2; }
.cq-strip-item .y { color: var(--usher); font-size: .8rem; }

@media (max-width: 640px) {
  .cq-feature { min-height: 520px; }
  .cq-feature-body { padding: 1.6rem 1.6rem 7.6rem 2.6rem; }
  .st-key-feature_actions { padding: 0 1.2rem 0 2.6rem; margin-top: -7rem; }
  a.cq-strip-item { flex-basis: 118px; }  a.cq-strip-item .cq-poster { width: 118px; }
}
@media (prefers-reduced-motion: reduce) { .cq-feature { animation: none; } }
</style>
"""


FEATURE_SHADE = ("linear-gradient(90deg, rgba(28,15,23,.97) 0%, rgba(28,15,23,.86) 38%, "
                 "rgba(28,15,23,.25) 72%, rgba(28,15,23,.05) 100%), "
                 "linear-gradient(0deg, rgba(28,15,23,.95) 0%, rgba(28,15,23,0) 55%)")


def feature_html(t: dict, when: str, label: str, facts: list[str], why: str, href: str) -> str:
    bg = (f' style="background-image:{FEATURE_SHADE}, url({escape(t["backdrop"])})"'
          if t.get("backdrop") else "")
    why_html = f'<div class="cq-feature-why">{escape(why)}</div>' if why else ""
    return (f'<section class="cq-feature"{bg}><div class="cq-feature-body">'
            f'<p class="cq-feature-ask">What\'s your next watch {escape(when)}?</p>'
            f'<div class="cq-feature-label">{escape(label)}</div>'
            f'<h2 class="cq-feature-title"><a href="{escape(href)}" target="_self">{escape(t["title"])}</a></h2>'
            + "".join(f'<div class="cq-feature-facts">{escape(f)}</div>' for f in facts if f)
            + f'{why_html}</div></section>')


def strip_html(title: str, items: list[dict], link_fn) -> str:
    cells = []
    for t in items:
        poster = (f'<img class="cq-poster" src="{escape(t["poster"])}" alt="" loading="lazy">'
                  if t.get("poster") else f'<div class="cq-poster cq-noposter">{escape(t["title"])}</div>')
        cells.append(f'<a class="cq-strip-item" href="{escape(link_fn(t["key"]))}" target="_self">{poster}'
                     f'<span class="n">{escape(t["title"])}</span><span class="y">{escape(meta_line(t))}</span></a>')
    return (f'<h3 class="cq-strip-title">{escape(title)}</h3>'
            f'<div class="cq-strip">{"".join(cells)}</div>')


def stats_line(n: int, avg: float, vs_imdb: float | None) -> str:
    text = f"{n} rated, averaging {avg:.1f}★."
    if vs_imdb is not None:
        if abs(vs_imdb) < 0.1:
            text += " Right in line with IMDb."
        else:
            word = "harsher" if vs_imdb < 0 else "kinder"
            text += f" You're {abs(vs_imdb):.1f}★ {word} than IMDb."
    return f'<p class="cq-stats-line">{escape(text)}</p>'


# =====================================================================
# Atmosphere: the page background. Behind everything, in this order:
#   ambient  - a heavily blurred copy of the film on screen
#   beam     - a projector cone from the top, with drifting dust
#   vignette - edges fading to black
# and on top of everything (but click-through): fine film grain.
# =====================================================================
GRAIN_SVG_RAW = ("<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
             "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' "
             "stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .6 0'/>"
             "</filter><rect width='100%' height='100%' filter='url(#n)'/></svg>")
# fully percent-encoded: raw < > inside a <style> block get the whole block stripped
GRAIN_SVG = "data:image/svg+xml," + __import__("urllib.parse", fromlist=["quote"]).quote(GRAIN_SVG_RAW, safe="")

ATMOS_CSS = """
<style>
/* let the atmosphere show through Streamlit's own backgrounds */
html, body { background: #1C0F17 !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"] > div {
  background: transparent !important;
}
.cq-atmos { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }
.cq-ambient {
  position: absolute; inset: -10%; background-size: cover; background-position: center;
  filter: blur(70px) saturate(1.35) brightness(.5); opacity: .75;
  animation: cq-amb-in 1.4s ease both;
}
@keyframes cq-amb-in { from { opacity: 0; } to { opacity: .75; } }
.cq-tint {     /* keeps text readable whatever colour the film is */
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(28,15,23,.45) 0%, rgba(28,15,23,.72) 45%, rgba(28,15,23,.9) 100%);
}
.cq-beam {
  position: absolute; left: 50%; top: -4vh; width: 140vw; height: 115vh; transform: translateX(-50%);
  background: conic-gradient(from 166deg at 50% 0%, rgba(246,213,142,0) 0deg,
              rgba(246,213,142,.1) 10deg, rgba(246,213,142,.1) 18deg, rgba(246,213,142,0) 28deg,
              rgba(246,213,142,0) 360deg);
  -webkit-mask-image: linear-gradient(180deg, #000 0%, rgba(0,0,0,.6) 55%, transparent 92%);
          mask-image: linear-gradient(180deg, #000 0%, rgba(0,0,0,.6) 55%, transparent 92%);
  filter: blur(14px);
}
.cq-lamp {    /* the projector itself, a soft hot spot at the top */
  position: absolute; left: 50%; top: -60px; width: 260px; height: 120px; transform: translateX(-50%);
  background: radial-gradient(ellipse at center, rgba(246,213,142,.22), rgba(246,213,142,0) 70%);
}
.cq-dust i {
  position: absolute; top: 0; width: 3px; height: 3px; border-radius: 50%;
  background: rgba(246,213,142,.55); box-shadow: 0 0 6px rgba(246,213,142,.5);
  animation: cq-drift linear infinite; opacity: 0;
}
@keyframes cq-drift {
  0% { transform: translate(0, 4vh); opacity: 0; }
  15% { opacity: .9; }
  85% { opacity: .5; }
  100% { transform: translate(var(--dx), 78vh); opacity: 0; }
}
.cq-vignette { position: absolute; inset: 0;
  background: radial-gradient(ellipse 85% 75% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%); }
.cq-grain {
  position: fixed; inset: -50%; z-index: 2147483000; pointer-events: none; opacity: .07;
  background-image: url("__GRAIN__"); background-size: 180px 180px; mix-blend-mode: overlay;
  animation: cq-grain 1s steps(6) infinite;
}
@keyframes cq-grain {
  0% { transform: translate(0, 0); }   20% { transform: translate(-3%, 2%); }
  40% { transform: translate(2%, -3%); } 60% { transform: translate(-2%, -1%); }
  80% { transform: translate(3%, 3%); } 100% { transform: translate(0, 0); }
}
@media (prefers-reduced-motion: reduce) {
  .cq-grain, .cq-dust i, .cq-ambient { animation: none !important; }
  .cq-dust { display: none; }
}
</style>
""".replace("__GRAIN__", GRAIN_SVG)

# a fixed handful of dust motes: (left %, delay s, duration s, sideways drift vw)
_DUST = [(48, 0, 16, -3), (51, 3, 19, 4), (46, 6, 15, -6), (53, 1.5, 21, 7), (50, 9, 17, -2),
         (49, 12, 20, 5), (47, 4.5, 18, -8), (52, 7.5, 22, 3), (50.5, 10.5, 16, -5), (48.5, 13.5, 19, 6)]


def atmosphere_html(backdrop: str | None = None) -> str:
    ambient = ""
    if backdrop:
        small = backdrop.replace("/w1280/", "/w300/")      # it's blurred anyway: save bandwidth
        ambient = f'<div class="cq-ambient" style="background-image:url({escape(small)})"></div>'
    dust = "".join(f'<i style="left:{x}%;animation-delay:{d}s;animation-duration:{t}s;--dx:{dx}vw"></i>'
                   for x, d, t, dx in _DUST)
    return (f'<div class="cq-atmos" aria-hidden="true">{ambient}<div class="cq-tint"></div>'
            f'<div class="cq-beam"></div><div class="cq-lamp"></div><div class="cq-dust">{dust}</div>'
            f'<div class="cq-vignette"></div></div><div class="cq-grain" aria-hidden="true"></div>')


# =====================================================================
# Polish: motion and finish on top of the styles above, CSS only (st.html
# strips scripts). Loaded last. Ideas borrowed from React Bits, done in CSS:
#   BlurText    - headings sharpen into place
#   AnimatedContent - poster grids rise in as they scroll into view
#   TiltedCard / glare - posters lift and catch a sweep of light on hover
#   ShinyText   - the home question and the match badges carry a slow sheen
# Plus a frosted sticky nav, warmer buttons, inputs, dialogs and popovers.
# No raw angle brackets in here: they get the whole <style> block stripped.
# =====================================================================
POLISH_CSS = """
<style>
html { scroll-behavior: smooth; }
::selection { background: rgba(217,169,86,.35); color: var(--light); }
* { scrollbar-width: thin; scrollbar-color: #5a3a4b transparent; }

/* ---- BlurText: big headings sharpen into place ---- */
.cq-ask, .cq-dtitle, .cq-feature-ask, .cq-feature-title, .cq-home .cq-ask-sub, .cq-reel-result .t {
  animation: cq-blur-in .95s cubic-bezier(.2,.8,.2,1) both;
}
.cq-feature-title { animation-delay: .25s; }
.cq-feature-label, .cq-feature-facts, .cq-feature-why, .cq-ask-sub { animation: cq-rise-in .8s cubic-bezier(.2,.8,.2,1) .35s both; }
.cq-screen .cq-facts, .cq-screen .cq-chips { animation: cq-rise-in .8s cubic-bezier(.2,.8,.2,1) .3s both; }
@keyframes cq-blur-in { from { opacity: 0; filter: blur(12px); transform: translateY(.35em); } to { opacity: 1; filter: blur(0); transform: none; } }
@keyframes cq-rise-in { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* ---- ShinyText: a slow sheen across the home question ---- */
.cq-ask {
  background: linear-gradient(100deg, var(--light) 0%, var(--light) 40%, var(--bulb) 50%, var(--light) 60%, var(--light) 100%);
  background-size: 250% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: cq-blur-in .95s cubic-bezier(.2,.8,.2,1) both, cq-sheen 7s ease-in-out 1.2s infinite;
}
@keyframes cq-sheen { 0%, 55% { background-position: 100% 0; } 100% { background-position: -50% 0; } }

/* ---- the feature screen and the details screen: a slow push-in on the backdrop ---- */
.cq-feature, .cq-screen { background-size: cover; animation: cq-feature-in .9s cubic-bezier(.6,.05,.3,1), cq-push 24s ease-in-out 1s infinite alternate; }
@keyframes cq-push { from { background-position: center 25%; } to { background-position: center 40%; } }
.cq-feature { box-shadow: 0 30px 80px rgba(0,0,0,.45), 0 0 0 1px rgba(217,169,86,.08); }

/* ---- AnimatedContent: grid posters rise in as they enter the screen ---- */
@supports (animation-timeline: view()) {
  .cq-card { animation: cq-card-in linear both; animation-timeline: view(); animation-range: entry 0% entry 55%; }
  @keyframes cq-card-in { from { opacity: 0; transform: translateY(40px) scale(.96); } to { opacity: 1; transform: none; } }
}
/* never inside the reel: its strip moves through a clipped window, so view() would keep them hidden */
.cq-reel-strip .cq-card { animation: none !important; opacity: 1; transform: none; }
/* film strips: items deal in one after another on load */
.cq-strip-item { animation: cq-rise-in .7s cubic-bezier(.2,.8,.2,1) both; }
.cq-strip-item:nth-child(2) { animation-delay: .05s; } .cq-strip-item:nth-child(3) { animation-delay: .1s; }
.cq-strip-item:nth-child(4) { animation-delay: .15s; } .cq-strip-item:nth-child(5) { animation-delay: .2s; }
.cq-strip-item:nth-child(6) { animation-delay: .25s; } .cq-strip-item:nth-child(7) { animation-delay: .3s; }
.cq-strip-item:nth-child(n+8) { animation-delay: .35s; }

/* ---- TiltedCard + glare: posters lift and catch light on hover ---- */
.cq-card { border-radius: 6px; transition: transform .45s cubic-bezier(.2,.8,.2,1), box-shadow .45s ease; }
.cq-card .cq-poster { transition: border-color .3s ease, filter .45s ease; }
.cq-card::after {
  content: ""; position: absolute; inset: 0; border-radius: 6px; pointer-events: none;
  background: linear-gradient(115deg, transparent 35%, rgba(255,246,225,.28) 50%, transparent 65%);
  background-size: 250% 100%; background-position: 130% 0; opacity: 0;
  transition: background-position .8s cubic-bezier(.2,.8,.2,1), opacity .3s ease;
}
.cq-card .cq-stub, .cq-card .cq-match { z-index: 2; }
a.cq-cardlink:hover .cq-card, a.cq-cardlink:focus-visible .cq-card {
  transform: translateY(-6px) rotate(-.4deg) scale(1.02);
  box-shadow: 0 18px 40px rgba(0,0,0,.55), 0 0 0 1px rgba(217,169,86,.5), 0 0 30px rgba(217,169,86,.18);
}
a.cq-cardlink:hover .cq-card::after { opacity: 1; background-position: -30% 0; }
a.cq-cardlink:hover .cq-poster { filter: brightness(1.06) saturate(1.08); }
a.cq-strip-item .cq-poster { transition: transform .45s cubic-bezier(.2,.8,.2,1), box-shadow .45s ease, border-color .3s ease; }
a.cq-strip-item:hover .cq-poster { transform: translateY(-5px) scale(1.04); box-shadow: 0 14px 30px rgba(0,0,0,.55), 0 0 22px rgba(217,169,86,.2); }
.cq-strip { padding-top: 28px; }

/* ---- match badges carry a slow sheen ---- */
.cq-match, .cq-score-pill {
  background-color: rgba(28,15,23,.88);
  background-image: linear-gradient(100deg, transparent 46%, rgba(246,213,142,.22) 50%, transparent 54%);
  background-size: 400% 100%; background-repeat: no-repeat; animation: cq-badge 5s ease-in-out infinite;
}
@keyframes cq-badge { 0%, 70% { background-position: 100% 0; } 100% { background-position: 0 0; } }
.cq-reasons li { animation: cq-rise-in .6s cubic-bezier(.2,.8,.2,1) both; }
.cq-reasons li:nth-child(2) { animation-delay: .08s; } .cq-reasons li:nth-child(3) { animation-delay: .16s; }

/* ---- frosted sticky navigation ---- */
.st-key-nav {
  position: sticky; top: .6rem; z-index: 50; padding: .55rem .7rem; border-radius: 999px;
  background: rgba(28,15,23,.62); border: 1px solid rgba(69,41,58,.8);
  -webkit-backdrop-filter: blur(14px) saturate(1.2); backdrop-filter: blur(14px) saturate(1.2);
  box-shadow: 0 10px 30px rgba(0,0,0,.35); width: fit-content; max-width: 100%;
}
.st-key-nav button { transition: background-color .25s ease, border-color .25s ease, transform .2s ease, box-shadow .25s ease !important; }
.st-key-nav button:hover { transform: translateY(-1px); }
.st-key-nav button[aria-checked="true"], .st-key-nav button[kind="pillsActive"] {
  box-shadow: 0 0 0 1px var(--brass), 0 6px 22px rgba(217,169,86,.35) !important;
}

/* ---- buttons: brass primary that glows, quiet secondary that lights its edge ---- */
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(180deg, #E4B865, var(--brass)) !important; color: var(--velvet) !important;
  border: 0 !important; font-weight: 600 !important;
  box-shadow: 0 1px 0 rgba(255,255,255,.35) inset, 0 6px 18px rgba(217,169,86,.25);
  transition: transform .2s ease, box-shadow .25s ease, filter .2s ease !important;
}
[data-testid="stBaseButton-primary"]:hover { transform: translateY(-2px); filter: brightness(1.05);
  box-shadow: 0 1px 0 rgba(255,255,255,.35) inset, 0 10px 28px rgba(217,169,86,.42); }
[data-testid="stBaseButton-primary"]:active { transform: translateY(0) scale(.98); }
[data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primary"] span { color: var(--velvet) !important; }
[data-testid="stBaseButton-secondary"], [data-testid="stPopover"] button {
  background: rgba(42,23,34,.78) !important; border: 1px solid var(--seam) !important;
  transition: transform .2s ease, border-color .25s ease, box-shadow .25s ease, background-color .25s ease !important;
}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stPopover"] button:hover {
  border-color: var(--brass) !important; transform: translateY(-1px); background: rgba(58,32,48,.9) !important;
  box-shadow: 0 6px 20px rgba(0,0,0,.35), 0 0 0 1px rgba(217,169,86,.25);
}
[data-testid="stBaseButton-secondary"]:active { transform: scale(.98); }
.st-key-feature_actions [data-testid="stBaseButton-secondary"] {
  background: rgba(28,15,23,.55) !important; -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
}

/* ---- inputs, selects, sliders ---- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] div[data-baseweb] {
  border-radius: 8px !important; transition: box-shadow .25s ease, border-color .25s ease !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--brass) !important; box-shadow: 0 0 0 3px rgba(217,169,86,.22) !important;
}
[data-testid="stSlider"] [role="slider"] { box-shadow: 0 0 0 4px rgba(217,169,86,.22), 0 0 14px rgba(217,169,86,.45) !important;
  transition: transform .15s ease; }
[data-testid="stSlider"] [role="slider"]:hover { transform: scale(1.15); }

/* ---- dialogs and popovers: a velvet card with a lit top edge ---- */
[data-testid="stDialog"] [role="dialog"] {
  background: radial-gradient(120% 60% at 50% 0%, #34192a 0%, var(--velvet) 60%) !important;
  border: 1px solid var(--seam) !important; border-radius: 16px !important;
  box-shadow: 0 0 0 1px rgba(217,169,86,.12), 0 40px 100px rgba(0,0,0,.7) !important;
  animation: cq-dialog-in .45s cubic-bezier(.2,.8,.2,1) both;
}
[data-testid="stDialog"] [role="dialog"]::before {
  content: ""; position: absolute; left: 12%; right: 12%; top: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--brass), transparent); opacity: .8;
}
@keyframes cq-dialog-in { from { opacity: 0; transform: translateY(18px) scale(.97); } to { opacity: 1; transform: none; } }
[data-testid="stPopoverBody"] {
  background: rgba(28,15,23,.92) !important; border: 1px solid var(--seam) !important; border-radius: 14px !important;
  -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px); box-shadow: 0 24px 60px rgba(0,0,0,.55) !important;
}

/* ---- expanders, toasts, empty states ---- */
[data-testid="stExpander"] details { border: 1px solid var(--seam) !important; border-radius: 10px !important;
  background: rgba(42,23,34,.45); transition: border-color .25s ease; }
[data-testid="stExpander"] details:hover { border-color: #6a4357 !important; }
[data-testid="stExpander"] details[open] { border-color: rgba(217,169,86,.45) !important; }
[data-testid="stToast"] { background: var(--curtain) !important; border: 1px solid var(--brass) !important; border-radius: 12px !important; }
.cq-empty { background: linear-gradient(180deg, rgba(42,23,34,.55), rgba(42,23,34,.15)); border-radius: 12px;
  animation: cq-rise-in .7s cubic-bezier(.2,.8,.2,1) both; }

/* ---- the reel lands with a flash of the marquee bulbs ---- */
.cq-reel-window { animation: cq-reel-glow 1.2s ease 3.3s both; }
@keyframes cq-reel-glow {
  0% { box-shadow: 0 0 0 6px #241320, 0 0 0 8px var(--seam), 0 0 30px rgba(217,169,86,.25); }
  30% { box-shadow: 0 0 0 6px #241320, 0 0 0 8px var(--brass), 0 0 90px rgba(246,213,142,.75); }
  100% { box-shadow: 0 0 0 6px #241320, 0 0 0 8px var(--seam), 0 0 36px rgba(217,169,86,.3); }
}

/* ---- the movie night bars fill in ---- */
.cq-fit .bar i { animation: cq-fill 1.1s cubic-bezier(.2,.8,.2,1) .2s both; transform-origin: left center; }
@keyframes cq-fill { from { transform: scaleX(0); } to { transform: scaleX(1); } }

@media (max-width: 640px) {
  .st-key-nav { top: .3rem; border-radius: 18px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .cq-ask, .cq-dtitle, .cq-feature-ask, .cq-feature-title, .cq-ask-sub, .cq-feature-label, .cq-feature-facts,
  .cq-feature-why, .cq-screen .cq-facts, .cq-screen .cq-chips, .cq-feature, .cq-screen, .cq-card, .cq-strip-item,
  .cq-match, .cq-score-pill, .cq-reasons li, .cq-empty, .cq-reel-window, .cq-fit .bar i, .cq-reel-result .t,
  [data-testid="stDialog"] [role="dialog"] { animation: none !important; }
  .cq-card, .cq-card::after, .cq-poster, a.cq-strip-item .cq-poster { transition: none !important; }
  a.cq-cardlink:hover .cq-card, a.cq-strip-item:hover .cq-poster { transform: none; }
}
</style>
"""


# =====================================================================
# Skeletons: the page's layout in placeholder shapes, shown in a st.empty()
# stage while picks are computed, then replaced in place by the real thing.
# A slow velvet shimmer, never gold. Posters fade in when they arrive.
# =====================================================================
SKELETON_CSS = """
<style>
.cq-sk { display: flex; flex-direction: column; gap: 1.4rem; }
.cq-sk-box {
  border-radius: 6px;
  background: linear-gradient(100deg, #2A1722 0%, #2A1722 35%, #3A2030 50%, #2A1722 65%, #2A1722 100%);
  background-size: 300% 100%; animation: cq-sk-shimmer 2.4s ease-in-out infinite;
}
@keyframes cq-sk-shimmer { from { background-position: 100% 0; } to { background-position: 0 0; } }
.cq-sk-bar { height: 1rem; border-radius: 4px; }

/* home: tonight's feature, then the actions, then film-strip rows */
.cq-sk-hero { position: relative; min-height: 520px; border-radius: 10px; border: 1px solid var(--seam); background: #221219;
  display: flex; flex-direction: column; justify-content: flex-end; gap: .8rem; padding: 2.4rem 3.4rem 2.6rem; }
.cq-sk-ask { height: 2.8rem; width: min(560px, 80%); }
.cq-sk-ask.b { width: min(300px, 50%); margin-bottom: 1rem; }
.cq-sk-label { width: 9rem; height: .9rem; }
.cq-sk-title { height: 2.4rem; width: min(380px, 65%); }
.cq-sk-fact { width: min(260px, 50%); }
.cq-sk-fact.b { width: min(200px, 40%); }
.cq-sk-btns, .cq-sk-pills { display: flex; gap: .6rem; flex-wrap: wrap; }
.cq-sk-btn { width: 9.5rem; height: 2.5rem; border-radius: 8px; }
.cq-sk-pill { width: 8.5rem; height: 2.3rem; border-radius: 999px; }
.cq-sk-strip-title { width: 15rem; height: 1.4rem; margin: .4rem 0 .5rem; }
.cq-sk-strip { display: flex; gap: .9rem; overflow: hidden; padding: 24px 16px 22px; border-radius: 6px;
  border: 1px solid #2a1620; background: #110910; }
.cq-sk-poster { flex: 0 0 148px; aspect-ratio: 2 / 3; }

/* grid: recommendation cards, poster then two lines */
.cq-sk-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1.6rem 1.4rem; }
.cq-sk-card { display: flex; flex-direction: column; gap: .55rem; }
.cq-sk-card .cq-sk-poster { flex: none; width: 100%; }
.cq-sk-card .cq-sk-bar.t { width: 70%; height: 1.1rem; margin-top: .3rem; }
.cq-sk-card .cq-sk-bar.m { width: 45%; height: .8rem; }
.cq-sk-card .cq-sk-bar.r { width: 85%; height: .8rem; }

/* real posters fade in instead of popping; until the image arrives the box keeps the skeleton tone */
img.cq-poster { background-color: #2A1722; animation: cq-poster-in .3s ease both; }
@keyframes cq-poster-in { from { opacity: 0; } to { opacity: 1; } }
.cq-reel-strip img.cq-poster { animation: none; }

@media (max-width: 640px) {
  .cq-sk-hero { min-height: 420px; padding: 1.6rem; }
  .cq-sk-poster { flex-basis: 118px; }
  .cq-sk-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cq-sk-btn { width: 7.5rem; }
}
@media (prefers-reduced-motion: reduce) {
  .cq-sk-box { animation: none; background: #2A1722; }
  img.cq-poster { animation: none; }
}
</style>
"""


def skeleton_html(layout: str) -> str:
    """Placeholder shapes for a page that is still loading. `layout`: "home" or "grid"."""
    box = 'class="cq-sk-box'
    posters = lambda n: "".join(f'<div {box} cq-sk-poster"></div>' for _ in range(n))  # noqa: E731
    if layout == "home":
        hero = ('<div class="cq-sk-hero">'
                f'<div {box} cq-sk-bar cq-sk-ask"></div><div {box} cq-sk-bar cq-sk-ask b"></div>'
                f'<div {box} cq-sk-bar cq-sk-label"></div><div {box} cq-sk-bar cq-sk-title"></div>'
                f'<div {box} cq-sk-bar cq-sk-fact"></div><div {box} cq-sk-bar cq-sk-fact b"></div>'
                '<div class="cq-sk-btns">'
                + "".join(f'<div {box} cq-sk-btn"></div>' for _ in range(3)) + '</div></div>')
        pills = '<div class="cq-sk-pills">' + "".join(f'<div {box} cq-sk-pill"></div>' for _ in range(5)) + '</div>'
        strips = "".join(f'<div><div {box} cq-sk-bar cq-sk-strip-title"></div>'
                         f'<div class="cq-sk-strip">{posters(9)}</div></div>' for _ in range(2))
        body = hero + pills + strips
    else:
        card = (f'<div class="cq-sk-card"><div {box} cq-sk-poster"></div><div {box} cq-sk-bar t"></div>'
                f'<div {box} cq-sk-bar m"></div><div {box} cq-sk-bar r"></div></div>')
        body = f'<div class="cq-sk-grid">{card * 8}</div>'
    return (f'<div class="cq-sk" role="status" aria-busy="true" aria-label="Loading your picks">'
            f'{body}</div>')


# =====================================================================
# Admitted: right after signing in, the ticket stub from the sign-in page
# gets a red rubber stamp, then the overlay fades away to reveal Home.
# CSS only (st.html strips scripts and <svg>); click-through throughout.
# =====================================================================
_INK_SVG_RAW = ("<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
                "<filter id='i'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' seed='7'/>"
                "<feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -2.6 0 0 0 2.25'/></filter>"
                "<rect width='100%' height='100%' filter='url(#i)'/></svg>")
# fully percent-encoded, like the grain: raw angle brackets in a <style> block get it stripped
INK_SVG = "data:image/svg+xml," + __import__("urllib.parse", fromlist=["quote"]).quote(_INK_SVG_RAW, safe="")

ADMIT_CSS = """
<style>
.cq-admit {
  position: fixed; inset: 0; z-index: 2147482000; display: grid; place-items: center;
  background: rgba(16,8,13,.86); pointer-events: none;
  animation: cq-admit-out .35s ease 1.85s forwards;
}
@keyframes cq-admit-out { to { opacity: 0; visibility: hidden; } }
.cq-admit-stub {
  position: relative; width: min(300px, 82vw); padding: 1.6rem 1.6rem 1.4rem 2rem; color: #2A1722;
  background: #F2E8DA; border-radius: 10px; box-shadow: 0 24px 60px rgba(0,0,0,.55);
  -webkit-mask: radial-gradient(circle 13px at 0 0, #0000 97%, #000) top / 100% 51% no-repeat,
                radial-gradient(circle 13px at 0 100%, #0000 97%, #000) bottom / 100% 51% no-repeat;
          mask: radial-gradient(circle 13px at 0 0, #0000 97%, #000) top / 100% 51% no-repeat,
                radial-gradient(circle 13px at 0 100%, #0000 97%, #000) bottom / 100% 51% no-repeat;
  animation: cq-arrive .35s cubic-bezier(.2,.8,.2,1) both;
}
.cq-admit-stub::before {            /* the torn, perforated edge */
  content: ""; position: absolute; left: .7rem; top: 1rem; bottom: 1rem; border-left: 2px dashed #B9A78F;
}
@keyframes cq-arrive { from { opacity: 0; transform: translateY(18px) rotate(-1.5deg); } }
.cq-admit-kicker { font-family: var(--sign); font-weight: 700; font-size: .72rem; letter-spacing: .32em; color: #8A5A12; }
.cq-admit-name { font-family: var(--sign); font-weight: 900; font-stretch: 75%; font-size: 3.2rem;
  line-height: .95; letter-spacing: .06em; color: #2A1722; margin: .35rem 0 .9rem; }
.cq-admit-facts { display: flex; gap: 1.6rem; border-top: 1px solid #D8C8B2; padding-top: .8rem; }
.cq-admit-facts span { display: block; font-family: var(--sign); font-size: .66rem; font-weight: 700;
  letter-spacing: .14em; color: #8A7480; }
.cq-admit-facts b { font-family: var(--sign); font-weight: 700; font-size: 1rem; color: #2A1722; white-space: nowrap; }
.cq-admit-stamp {
  position: absolute; left: 60%; top: 64%; padding: .22rem .6rem .18rem;
  font-family: var(--sign); font-weight: 900; font-stretch: 80%; font-size: 2rem; letter-spacing: .12em;
  color: #9E2A2B; border: 4px solid #9E2A2B; border-radius: 6px; mix-blend-mode: multiply;
  box-shadow: inset 0 0 0 2px #F2E8DA, inset 0 0 0 4px #9E2A2B;
  -webkit-mask-image: url("__INK__"); mask-image: url("__INK__");
  -webkit-mask-size: 160px 160px; mask-size: 160px 160px;
  transform: translate(-50%, -50%) rotate(-11deg);
  animation: cq-stamp .42s cubic-bezier(.3,1.5,.5,1) .25s both;
}
@keyframes cq-stamp {
  0% { opacity: 0; transform: translate(-50%, -50%) rotate(-11deg) scale(1.6); }
  55% { opacity: 1; transform: translate(-50%, -50%) rotate(-11deg) scale(.95); }
  100% { opacity: 1; transform: translate(-50%, -50%) rotate(-11deg) scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .cq-admit { animation: cq-admit-gone 2.2s steps(1, end) forwards; }
  .cq-admit-stub, .cq-admit-stamp { animation: none; }
}
@keyframes cq-admit-gone { to { visibility: hidden; opacity: 0; } }
</style>
""".replace("__INK__", INK_SVG)


def ticket_seat(day) -> str:
    """The seat printed on the ticket: changes daily, same all day."""
    n = day.toordinal()
    return f"{'DEFGHJK'[n % 7]}{n % 17 + 4}"


def admitted_html(date_label: str, seat: str) -> str:
    return (ADMIT_CSS
            + '<div class="cq-admit" aria-hidden="true"><div class="cq-admit-stub">'
            '<div class="cq-admit-kicker">ADMIT ONE</div><div class="cq-admit-name">CRITIQ</div>'
            '<div class="cq-admit-facts">'
            f'<div><span>DATE</span><b>{escape(date_label)}</b></div>'
            f'<div><span>SEAT</span><b>{escape(seat)}</b></div></div>'
            '<div class="cq-admit-stamp">ADMITTED</div></div></div>')


# =====================================================================
# Poster wall: slowly drifting columns of posters, tilted. Full strength
# behind the sign-in ticket; faint, blurred and fading out down the screen
# behind the signed-in pages (built from the user's own titles).
# =====================================================================
WALL_CSS = """
<style>
.cq-wall { position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none;
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 14px; padding: 0 14px;
  transform: rotate(-4deg) scale(1.15); }
.cq-wall-col { display: flex; flex-direction: column; gap: 14px; animation: cq-wall-drift 140s linear infinite; }
.cq-wall-col:nth-child(even) { animation-direction: reverse; margin-top: -90px; }
.cq-wall-col:nth-child(3n) { animation-duration: 170s; }
.cq-wall img { width: 100%; aspect-ratio: 2 / 3; object-fit: cover; border-radius: 6px; display: block;
  filter: saturate(.75); }
@keyframes cq-wall-drift { from { transform: translateY(0); } to { transform: translateY(-50%); } }

/* signed-in pages: the same wall, much fainter, softened, and gone by the bottom of the screen.
   The holder is fixed behind everything and takes no clicks; the fade is on the holder (not the
   tilted wall) so it runs straight down the screen. */
.cq-wall-app { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;
  opacity: .13; filter: blur(3px);
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 50%, transparent 100%);
          mask-image: linear-gradient(180deg, #000 0%, #000 50%, transparent 100%); }
.cq-wall-app .cq-wall { position: absolute; z-index: auto; }

@media (max-width: 640px) { .cq-wall { grid-template-columns: repeat(4, 1fr); } }
@media (prefers-reduced-motion: reduce) { .cq-wall-col { animation: none; } }
</style>
"""


def poster_wall_html(posters: list[str], cols: int = 7) -> str:
    """Columns of posters for the wall; each column repeats its set so the drift loops seamlessly."""
    if not posters:
        return ""
    col_html = []
    for c in range(cols):
        mine = posters[c::cols] or posters
        mine = (mine * 4)[:6]                       # same length per column
        imgs = "".join(f'<img src="{escape(u)}" alt="" loading="lazy">' for u in mine * 2)
        col_html.append(f'<div class="cq-wall-col">{imgs}</div>')
    return f'<div class="cq-wall" aria-hidden="true">{"".join(col_html)}</div>'


def app_wall_html(posters: list[str]) -> str:
    """The faint wall behind the signed-in pages, with the film grain on top as before."""
    small = [u.replace("/w342/", "/w185/") for u in posters]    # faint and blurred: small files do
    wall = poster_wall_html(small)
    holder = f'<div class="cq-wall-app" aria-hidden="true">{wall}</div>' if wall else ""
    return f'{holder}<div class="cq-grain" aria-hidden="true"></div>'


# =====================================================================
# Sign-in: a cinema ticket in front of a slowly drifting wall of this
# week's trending posters.
# =====================================================================
SIGNIN_CSS = """
<style>
.cq-wall-shade { position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 60% 55% at 50% 48%, rgba(28,15,23,.55) 0%, rgba(28,15,23,.82) 72%, #1C0F17 100%),
    rgba(28,15,23,.35); }

.cq-door { position: relative; z-index: 1; min-height: 78vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 1.4rem; padding: 2rem 0; }
.cq-ticket { --cut: 63%; display: flex; width: min(680px, 100%); color: #2A1722;
  background: #F2E8DA; border-radius: 10px; box-shadow: 0 24px 60px rgba(0,0,0,.55);
  -webkit-mask: radial-gradient(circle 13px at var(--cut) 0, #0000 97%, #000) top / 100% 51% no-repeat,
                radial-gradient(circle 13px at var(--cut) 100%, #0000 97%, #000) bottom / 100% 51% no-repeat;
          mask: radial-gradient(circle 13px at var(--cut) 0, #0000 97%, #000) top / 100% 51% no-repeat,
                radial-gradient(circle 13px at var(--cut) 100%, #0000 97%, #000) bottom / 100% 51% no-repeat;
  animation: cq-arrive .7s cubic-bezier(.2,.8,.2,1) both; }
@keyframes cq-arrive { from { opacity: 0; transform: translateY(18px) rotate(-1.5deg); } }
.cq-t-main { flex: 0 0 var(--cut); padding: 1.6rem 1.7rem 1.4rem; border-right: 2px dashed #B9A78F; }
.cq-t-admit { font-family: var(--sign); font-weight: 700; font-size: .72rem; letter-spacing: .32em;
  color: #8A5A12; }
.cq-t-name { font-family: var(--sign); font-weight: 900; font-stretch: 75%; font-size: 3.6rem;
  line-height: .95; letter-spacing: .06em; color: #2A1722; margin: .35rem 0 .4rem; }
.cq-t-line { font-style: italic; font-size: 1.05rem; color: #5A4250; margin: 0 0 1.2rem; }
.cq-t-facts { display: flex; flex-wrap: wrap; gap: .6rem 1.6rem; border-top: 1px solid #D8C8B2; padding-top: .8rem; }
.cq-t-fact span { display: block; font-family: var(--sign); font-size: .66rem; font-weight: 700;
  letter-spacing: .14em; color: #8A7480; }
.cq-t-fact b { font-family: var(--sign); font-weight: 700; font-size: 1rem; color: #2A1722; white-space: nowrap; }
.cq-t-stub { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: .7rem; padding: 1.2rem .9rem; text-align: center; min-width: 0; transition: transform .25s ease; transform-origin: left center; }
.cq-ticket:hover .cq-t-stub { transform: rotate(2.5deg) translateX(3px); }
.cq-t-tear { font-family: var(--sign); font-size: .66rem; font-weight: 700; letter-spacing: .14em; color: #8A7480; }
a.cq-google { display: inline-flex; align-items: center; gap: .55rem; background: #fff; color: #1f1f1f !important;
  text-decoration: none !important; font-family: Roboto, Arial, sans-serif; font-size: .92rem; font-weight: 500;
  padding: .55rem .85rem; border-radius: 999px; border: 1px solid #D8C8B2; white-space: nowrap;
  transition: box-shadow .2s ease, transform .2s ease; }
a.cq-google:hover { box-shadow: 0 4px 14px rgba(42,23,34,.25); transform: translateY(-1px); }
a.cq-google:focus-visible { outline: 3px solid #D9A956; outline-offset: 3px; }
.cq-google .cq-g { width: 18px; height: 18px; flex: none; }
.cq-t-note { font-size: .78rem; color: #8A7480; line-height: 1.35; max-width: 11rem; }
.cq-door-link { font-size: .95rem; }
.cq-door-link a { color: var(--usher) !important; }
.cq-door-link a:hover { color: var(--light) !important; }

@media (max-width: 640px) {
  .cq-ticket { --cut: 100%; flex-direction: column; -webkit-mask: none; mask: none; }
  .cq-t-main { border-right: 0; border-bottom: 2px dashed #B9A78F; }
  .cq-t-name { font-size: 2.8rem; }
  .cq-t-facts { gap: .6rem 1.2rem; }
  .cq-ticket:hover .cq-t-stub { transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .cq-ticket { animation: none; }
  .cq-t-stub, a.cq-google { transition: none; }
}
</style>
"""

_G_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
            '<path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.6 5.4 2.6 13.3l7.9 6.1C12.4 13.7 17.7 9.5 24 9.5z"/>'
            '<path fill="#4285F4" d="M46.1 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.4c-.5 2.9-2.2 5.3-4.6 6.9l7.4 5.7c4.3-4 6.9-9.9 6.9-17.1z"/>'
            '<path fill="#FBBC05" d="M10.5 28.6c-.5-1.4-.8-3-.8-4.6s.3-3.2.8-4.6l-7.9-6.1C1 16.6 0 20.2 0 24s1 7.4 2.6 10.7l7.9-6.1z"/>'
            '<path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.8-5.8l-7.4-5.7c-2.1 1.4-4.8 2.3-8.4 2.3-6.3 0-11.6-4.2-13.5-10l-7.9 6.1C6.6 42.6 14.6 48 24 48z"/></svg>')
# st.html strips inline <svg>, so the Google "G" goes in as an image
GOOGLE_G = ('<img class="cq-g" alt="" src="data:image/svg+xml,'
            + __import__("urllib.parse", fromlist=["quote"]).quote(_G_SVG, safe="") + '">')


def signin_html(posters: list[str], date_label: str, seat: str, href: str,
                invited: bool = False) -> str:
    """The logged-out page. `posters` are image URLs for the wall (may be empty)."""
    wall = poster_wall_html(posters)
    show = "Movie night for two" if invited else "Your next watch"
    line = ("You've been invited. Sign in and Critiq finds something you'll both enjoy."
            if invited else "Write it down. We'll take it from there.")
    return (
        f'{wall}<div class="cq-wall-shade"></div>'
        '<div class="cq-door"><div class="cq-ticket" role="group" aria-label="Critiq admission ticket">'
        '<div class="cq-t-main"><div class="cq-t-admit">ADMIT ONE</div>'
        '<div class="cq-t-name">CRITIQ</div>'
        f'<p class="cq-t-line">{escape(line)}</p>'
        '<div class="cq-t-facts">'
        f'<div class="cq-t-fact"><span>DATE</span><b>{escape(date_label)}</b></div>'
        f'<div class="cq-t-fact"><span>SHOWING</span><b>{escape(show)}</b></div>'
        f'<div class="cq-t-fact"><span>SEAT</span><b>{escape(seat)}</b></div>'
        '</div></div>'
        '<div class="cq-t-stub"><div class="cq-t-tear">TEAR HERE</div>'
        f'<a class="cq-google" href="{escape(href)}" target="_self">{GOOGLE_G}Sign in with Google</a>'
        '<div class="cq-t-note">Your ratings stay with your Google account, on every device.</div>'
        '</div></div>'
        '<div class="cq-door-link"><a href="https://rayanasad109.github.io/Critiq/" target="_blank" '
        'rel="noopener">New here? See what Critiq does</a></div></div>'
    )
