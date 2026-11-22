"""Content-based recommender.

Each title is turned into two vectors:
  * a "tag" vector  - genres, keywords, cast and directors (TF-IDF over tokens)
  * a "text" vector - plot overview + tagline + keywords (TF-IDF over words)

Your taste profile is a weighted sum of the titles you rated: a 5/5 pulls the
profile toward that title, a 0.5/5 pushes it away (weights run from -1 to +1,
with 2.5 as neutral). Your written reviews are vectorized with the same text
vocabulary and added in the direction of their rating. Opinion words ("loved",
"amazing", "boring") are stripped first: the rating already says how you felt,
so only words about *what the film is* ("twist", "alien", "language") count.
Favourite actors/directors and an optional "in the mood for" line add on top,
and genre / release-year / TMDB-score filters narrow the pool.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.preprocessing import normalize as l2

TAG_WEIGHT = 0.65
TEXT_WEIGHT = 0.35
REVIEW_WEIGHT = 1.5      # how strongly a review counts vs. the title's own text
VIBE_WEIGHT = 2.0        # the "in the mood for" box
ACTOR_BOOST = 0.12
DIRECTOR_BOOST = 0.18
QUALITY_BOOST = 0.08
MIN_REVIEW_OVERLAP = 0.004   # below this a shared word is coincidence, not a reason

# Words that say how you felt, not what the film is about. The star rating
# already carries the sentiment, so these would only add noise.
OPINION_WORDS = {
    # feelings / verdicts
    "love", "loved", "loving", "loves", "like", "liked", "likes", "enjoy", "enjoyed", "enjoyable",
    "hate", "hated", "hates", "dislike", "disliked", "adore", "adored", "appreciate", "appreciated",
    "amazing", "awesome", "great", "good", "best", "better", "bad", "worse", "worst", "terrible",
    "awful", "horrible", "brilliant", "incredible", "fantastic", "excellent", "perfect", "perfectly",
    "masterpiece", "solid", "decent", "okay", "fine", "nice", "cool", "fun", "boring", "bored",
    "overrated", "underrated", "mid", "trash", "garbage", "beautiful", "beautifully", "stunning",
    "wonderful", "favorite", "favourite", "favorites", "favourites", "recommend", "recommended",
    "impressive", "impressed", "disappointing", "disappointed", "masterful", "peak", "goated",
    "insane", "crazy", "wow", "lol", "omg", "honestly", "literally", "absolutely", "totally",
    "really", "pretty", "super", "kinda", "sorta", "quite", "truly", "simply", "definitely",
    # the medium itself / viewing
    "movie", "movies", "film", "films", "show", "shows", "series", "season", "seasons", "episode",
    "episodes", "watch", "watched", "watching", "rewatch", "rewatched", "seen", "saw", "viewing",
    # generic filler verbs / nouns
    "felt", "feel", "feels", "feeling", "think", "thought", "thinks", "way", "ways", "thing",
    "things", "lot", "lots", "bit", "overall", "fully", "completely", "changes", "changed",
    "change", "makes", "making", "made", "make", "gets", "got", "getting", "goes", "went",
    "kind", "sort", "actually", "basically", "especially", "maybe", "probably", "end",
    "time", "times", "part", "story", "stories", "plot", "character", "characters", "acting",
    "acted", "performance", "performances", "scene", "scenes", "writing", "written", "script", "parts", "point", "start", "started", "towards", "toward",
}
# sklearn drops stop words *before* building phrases, so "time" has to stay in
# the vocabulary for "time travel" to exist. On its own it is never shown as a reason.
KEEP_WORDS = {"time"}
STOP_WORDS = sorted((ENGLISH_STOP_WORDS | OPINION_WORDS) - KEEP_WORDS)
TOKEN_PATTERN = r"(?u)\b[a-zA-Z][a-zA-Z'-]{2,}\b"   # words of 3+ letters, no numbers

# TMDB names some genres differently for TV.
TV_GENRE_ALIASES = {
    "Action": "Action & Adventure", "Adventure": "Action & Adventure",
    "Science Fiction": "Sci-Fi & Fantasy", "Fantasy": "Sci-Fi & Fantasy",
    "War": "War & Politics",
}
FILTER_GENRES = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama",
                 "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance",
                 "Science Fiction", "Thriller", "War", "Western"]


def rating_weight(rating: float) -> float:
    """0..5 (step .25) -> -1..+1, with 2.5 as neutral."""
    return (float(rating) - 2.5) / 2.5


def tag_tokens(t: dict) -> list[str]:
    toks = [f"genre:{g.lower()}" for g in t.get("genres", [])]
    toks += [f"kw:{k.lower()}" for k in t.get("keywords", [])]
    toks += [f"cast:{c.lower()}" for c in t.get("cast", [])[:6]]
    toks += [f"dir:{d.lower()}" for d in t.get("directors", [])]
    return toks


def text_blob(t: dict) -> str:
    return " ".join([t.get("overview", ""), t.get("tagline", ""), " ".join(t.get("keywords", []))])


def passes_filters(t: dict, prefs: dict) -> bool:
    """Genre (any of), release-year range, your streaming services and minimum TMDB score."""
    wanted = prefs.get("genres") or []
    if wanted:
        have = set(t.get("genres", []))
        if not any(g in have or TV_GENRE_ALIASES.get(g) in have for g in wanted):
            return False
    lo, hi = prefs.get("year_min"), prefs.get("year_max")
    if lo or hi:
        year = int(t["year"]) if str(t.get("year", "")).isdigit() else None
        if year is None or (lo and year < lo) or (hi and year > hi):
            return False
    services = prefs.get("services") or []
    if services and not set(services) & set(t.get("stream_on", [])):
        return False
    min_score = prefs.get("min_score") or 0
    if min_score and t.get("vote_average", 0) < min_score:
        return False
    return True


@dataclass
class Recommendation:
    title: dict
    score: float
    reasons: list[str] = field(default_factory=list)


def build_candidate_keys(watched: list[dict], extra_keys: list[tuple[str, int]],
                         discover_keys: list[tuple[str, int]] | None = None,
                         limit: int = 80) -> list[tuple[str, int]]:
    """Pick which titles to fetch full details for.

    Titles recommended by several things you rated highly float to the top;
    titles only "related" to things you disliked are ignored. extra_keys come
    from favourite people; discover_keys from TMDB's filter-based discovery.
    """
    watched_keys = {(w["title"]["media_type"], w["title"]["id"]) for w in watched}
    votes: Counter = Counter()
    for w in watched:
        weight = rating_weight(w["rating"])
        if weight <= 0:
            continue
        for rank, k in enumerate(w["title"].get("related", [])):
            votes[tuple(k)] += weight * (1.0 - rank / 60)  # earlier = more relevant
    for k in extra_keys:
        votes[tuple(k)] += 0.8
    for rank, k in enumerate(discover_keys or []):
        votes[tuple(k)] += 0.6 * (1.0 - rank / 120)
    ranked = [k for k, _ in votes.most_common() if k not in watched_keys]
    return ranked[:limit]


def recommend(watched: list[dict], candidates: list[dict], prefs: dict | None = None,
              media_filter: str = "both", top_n: int = 12,
              allowed_keys: set[str] | None = None) -> list[Recommendation]:
    """
    watched:    [{"title": Title, "rating": float, "review": str}, ...]
    candidates: [Title, ...]  (anything already watched is skipped)
    prefs:      {"actors", "directors", "vibe", "genres", "year_min", "year_max", "min_score"}
    allowed_keys: if given (actor/director filters), only these titles are eligible
    """
    prefs = prefs or {}
    watched_keys = {w["title"]["key"] for w in watched}
    seen, pool = set(), []
    for c in candidates:
        if c["key"] in watched_keys or c["key"] in seen:
            continue
        if media_filter != "both" and c["media_type"] != media_filter:
            continue
        if not passes_filters(c, prefs):
            continue
        if allowed_keys is not None and c["key"] not in allowed_keys:
            continue
        seen.add(c["key"])
        pool.append(c)
    if not pool:
        return []

    w_titles = [w["title"] for w in watched]
    weights = np.array([rating_weight(w["rating"]) for w in watched])
    reviews = [w.get("review", "").strip() for w in watched]
    vibe = prefs.get("vibe", "").strip()

    # ---- vectorize everything in one shared vocabulary -------------------
    all_titles = w_titles + pool
    tag_vec = TfidfVectorizer(analyzer=lambda toks: toks, min_df=1)
    tag_vec.fit([tag_tokens(t) for t in all_titles] + [[]])
    text_vec = TfidfVectorizer(stop_words=STOP_WORDS, token_pattern=TOKEN_PATTERN,
                               ngram_range=(1, 2), sublinear_tf=True, min_df=1)
    text_vec.fit([text_blob(t) for t in all_titles] + reviews + [vibe, "placeholder"])

    C_tag = l2(tag_vec.transform([tag_tokens(t) for t in pool]))
    C_text = l2(text_vec.transform([text_blob(t) for t in pool]))
    text_terms = text_vec.get_feature_names_out()

    # ---- build the taste profile -----------------------------------------
    p_tag = np.zeros(len(tag_vec.vocabulary_))
    p_text = np.zeros(len(text_vec.vocabulary_))
    review_profile = np.zeros(len(text_vec.vocabulary_))
    if watched:
        W_tag = l2(tag_vec.transform([tag_tokens(t) for t in w_titles]))
        W_text = l2(text_vec.transform([text_blob(t) for t in w_titles]))
        p_tag = np.asarray(W_tag.T @ weights).ravel()
        p_text = np.asarray(W_text.T @ weights).ravel()
        for review, wt in zip(reviews, weights):
            if review:
                r = l2(text_vec.transform([review])).toarray().ravel()
                review_profile += wt * r
        p_text = p_text + REVIEW_WEIGHT * review_profile
    else:
        W_tag = W_text = None
    if vibe:
        p_text = p_text + VIBE_WEIGHT * l2(text_vec.transform([vibe])).toarray().ravel()

    def unit(v):
        n = np.linalg.norm(v)
        return v / n if n else v

    tag_sim = C_tag @ unit(p_tag)
    text_sim = C_text @ unit(p_text)
    scores = TAG_WEIGHT * np.asarray(tag_sim).ravel() + TEXT_WEIGHT * np.asarray(text_sim).ravel()

    # ---- favourite people + a small quality prior -------------------------
    fav_actors = {a.lower() for a in prefs.get("actors", []) if a}
    fav_dirs = {d.lower() for d in prefs.get("directors", []) if d}
    reasons: list[list[str]] = [[] for _ in pool]
    for i, c in enumerate(pool):
        cast = {x.lower(): x for x in c.get("cast", [])}
        dirs = {x.lower(): x for x in c.get("directors", [])}
        hit_a = [cast[a] for a in fav_actors if a in cast][:2]
        hit_d = [dirs[d] for d in fav_dirs if d in dirs]
        scores[i] += ACTOR_BOOST * len(hit_a) + DIRECTOR_BOOST * len(hit_d)
        if hit_d:
            reasons[i].append("Directed by " + ", ".join(hit_d))
        if hit_a:
            reasons[i].append("Stars " + ", ".join(hit_a))
        confidence = min(1.0, c.get("vote_count", 0) / 500)
        scores[i] += QUALITY_BOOST * (c.get("vote_average", 0) / 10) * confidence

    # ---- explanations ------------------------------------------------------
    pos_review = np.clip(review_profile, 0, None)
    liked_reviews = _norm(" | ".join(rv for rv, wt in zip(reviews, weights) if rv and wt > 0))
    if W_tag is not None:
        sim_to_watched = (C_tag @ W_tag.T).toarray() * 0.65 + (C_text @ W_text.T).toarray() * 0.35
    for i, c in enumerate(pool):
        if W_tag is not None and (weights > 0).any():
            contrib = sim_to_watched[i] * np.where(weights > 0, weights, 0)
            j = int(contrib.argmax())
            if contrib[j] > 0.05:
                src = w_titles[j]
                shared = [g for g in c.get("genres", []) if g in src.get("genres", [])][:2]
                line = f"Because you rated {src['title']} {watched[j]['rating']:g}/5"
                if shared:
                    line += f" ({' / '.join(shared)})"
                reasons[i].append(line)
        if pos_review.any():
            reasons[i].extend(review_reason(C_text[i].toarray().ravel(), pos_review, text_terms,
                                            c, liked_reviews))

    order = np.argsort(-scores)[:top_n]
    return [Recommendation(pool[i], float(scores[i]), reasons[i]) for i in order]


def _norm(text: str) -> str:
    return " " + " ".join(re.sub(r"[^a-z0-9' ]+", " ", text.lower()).split()) + " "


def review_reason(cand_vec: np.ndarray, review_vec: np.ndarray, terms,
                  title: dict | None = None, reviews_norm: str = "") -> list[str]:
    """Up to two content words/phrases a title shares with your positive reviews.

    Removing stop words can glue neighbours into fake phrases ("time travel and the
    twist" -> "travel twist"), so a phrase only counts if it really appears, word for
    word, in your review and in the title's keywords or description."""
    overlap = cand_vec * review_vec
    # Phrases ("time travel") are more telling than single words.
    bonus = np.array([1.5 if " " in t else 1.0 for t in terms])
    ranked = [k for k in (overlap * bonus).argsort()[::-1][:12] if overlap[k] >= MIN_REVIEW_OVERLAP]
    hits = [terms[k] for k in ranked]
    # Prefer phrases, then single words they don't already cover ("twist ending" beats "twist").
    title_norm = _norm(text_blob(title)) if title else ""
    keywords = {k.lower() for k in (title or {}).get("keywords", [])}

    def real(phrase: str) -> bool:
        if not title:
            return True
        in_title = phrase in keywords or f" {phrase} " in title_norm
        return in_title and f" {phrase} " in reviews_norm

    phrases = [t for t in hits if " " in t and real(t)]
    words = [t for t in hits if " " not in t and t not in KEEP_WORDS
             and not any(t in p.split() for p in phrases)]
    top: list[str] = []
    for t in phrases + words:
        if len(top) == 2:
            break
        if not any(set(t.split()) & set(x.split()) for x in top):
            top.append(t)
    if not top:
        return []
    return ["You wrote about " + " and ".join(f"“{t}”" for t in top)]
