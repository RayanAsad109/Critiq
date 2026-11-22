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
# Showtime effects: lights down while loading, curtains open on results,
# and the slot-machine reel.
# =====================================================================
EFFECTS_CSS = """
<style>
.cq-lights, .cq-reveal { position: fixed; inset: 0; z-index: 999990; }
.cq-lights { display: grid; place-items: center; animation: cq-dim .6s ease forwards; }
@keyframes cq-dim { from { background: rgba(8,4,7,0); } to { background: rgba(8,4,7,.9); } }
.cq-curtain {
  position: fixed; top: 0; bottom: 0; width: 51%;
  background:
    linear-gradient(180deg, rgba(0,0,0,.35), rgba(0,0,0,0) 18%, rgba(0,0,0,0) 80%, rgba(0,0,0,.55)),
    repeating-linear-gradient(90deg, #4c0f26 0 22px, #66173a 22px 34px, #3a0a1c 34px 52px);
  box-shadow: 0 0 40px rgba(0,0,0,.6);
}
.cq-curtain.l { left: 0; }  .cq-curtain.r { right: 0; }
.cq-lights .cq-curtain.l { transform: translateX(-101%); animation: cq-close-l 1s cubic-bezier(.6,.05,.3,1) .15s forwards; }
.cq-lights .cq-curtain.r { transform: translateX(101%);  animation: cq-close-r 1s cubic-bezier(.6,.05,.3,1) .15s forwards; }
@keyframes cq-close-l { to { transform: translateX(0); } }
@keyframes cq-close-r { to { transform: translateX(0); } }

/* old film-leader countdown */
.cq-leader {
  position: relative; z-index: 2; width: 230px; height: 230px; border-radius: 50%;
  border: 3px solid var(--light); opacity: 0; animation: cq-fade .3s ease .9s forwards;
  background:
    linear-gradient(var(--light), var(--light)) center / 2px 100% no-repeat,
    linear-gradient(var(--light), var(--light)) center / 100% 2px no-repeat,
    radial-gradient(circle, transparent 62%, var(--light) 62.5%, var(--light) 63.5%, transparent 64%),
    #1a1016;
}
.cq-leader-sweep {
  position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(rgba(242,232,218,.32) 0deg, rgba(242,232,218,0) 1deg 360deg);
  animation: cq-sweep 1s linear .9s infinite;
}
@keyframes cq-sweep { from { transform: rotate(0); } to { transform: rotate(360deg); } }
.cq-leader-num span {
  position: absolute; inset: 0; display: grid; place-items: center; opacity: 0;
  font-family: var(--sign); font-weight: 900; font-size: 6.5rem; color: var(--light);
  animation: cq-count 3s steps(1) infinite;
}
.cq-leader-num span:nth-child(1) { animation-delay: .9s; }
.cq-leader-num span:nth-child(2) { animation-delay: 1.9s; }
.cq-leader-num span:nth-child(3) { animation-delay: 2.9s; }
@keyframes cq-count { 0% { opacity: 1; } 33.3% { opacity: 0; } 100% { opacity: 0; } }
.cq-leader-cap {
  position: absolute; z-index: 2; top: calc(50% + 140px); left: 0; right: 0; text-align: center;
  color: var(--usher); font-style: italic; font-size: 1.1rem; opacity: 0; animation: cq-fade .3s ease 1s forwards;
}
@keyframes cq-fade { to { opacity: 1; } }

/* curtains part to reveal the results */
.cq-reveal { pointer-events: none; animation: cq-gone 0s linear 1.5s forwards; }
.cq-reveal .cq-curtain.l { animation: cq-open-l 1.2s cubic-bezier(.6,.05,.3,1) .15s forwards; }
.cq-reveal .cq-curtain.r { animation: cq-open-r 1.2s cubic-bezier(.6,.05,.3,1) .15s forwards; }
@keyframes cq-open-l { to { transform: translateX(-101%); } }
@keyframes cq-open-r { to { transform: translateX(101%); } }
@keyframes cq-gone { to { visibility: hidden; } }

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
  .cq-curtain, .cq-leader-sweep, .cq-leader-num span { animation: none !important; }
  .cq-lights .cq-curtain { transform: none; }
  .cq-leader-num span:nth-child(1) { opacity: 1; }
  .cq-reveal { display: none; }
  .cq-reel-strip { animation-duration: .01s !important; }
}
</style>
"""


def lights_down_html(caption: str = "Finding your next watch") -> str:
    return ('<div class="cq-lights" role="status" aria-label="Loading recommendations">'
            '<div class="cq-curtain l"></div><div class="cq-curtain r"></div>'
            '<div class="cq-leader"><div class="cq-leader-sweep"></div>'
            '<div class="cq-leader-num"><span>3</span><span>2</span><span>1</span></div></div>'
            f'<div class="cq-leader-cap">{escape(caption)}</div></div>')


def curtain_reveal_html() -> str:
    return '<div class="cq-reveal"><div class="cq-curtain l"></div><div class="cq-curtain r"></div></div>'


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
