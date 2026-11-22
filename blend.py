"""Movie night: find titles two people will both enjoy.

Each person's taste is scored against the same candidate pool with the normal
recommender. Scores are put on the same 0-1 scale (divided by that person's
best), then combined with a "least misery" rule: a title is only as good as
the person who'd like it least, plus a little credit for the average.

    blended = 0.6 * min(you, friend) + 0.4 * mean(you, friend)

So a title one of you would love and the other would hate can't win just by
being great for one person.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from recommender import Recommendation

MIN_WEIGHT = 0.6


@dataclass
class Pick:
    title: dict
    score: float
    you: int                     # 0-100, how well it fits you
    friend: int                  # 0-100, how well it fits your friend
    reasons_you: list[str] = field(default_factory=list)
    reasons_friend: list[str] = field(default_factory=list)


def _scaled(recs: list[Recommendation]) -> dict[str, tuple[float, Recommendation]]:
    best = max((r.score for r in recs), default=0) or 1
    return {r.title["key"]: (max(0.0, r.score) / best, r) for r in recs}


def blend(recs_you: list[Recommendation], recs_friend: list[Recommendation],
          top_n: int = 12) -> list[Pick]:
    you, friend = _scaled(recs_you), _scaled(recs_friend)
    picks = []
    for key in you.keys() & friend.keys():
        a, ra = you[key]
        b, rb = friend[key]
        score = MIN_WEIGHT * min(a, b) + (1 - MIN_WEIGHT) * (a + b) / 2
        picks.append(Pick(ra.title, score, round(100 * a), round(100 * b),
                          ra.reasons, rb.reasons))
    picks.sort(key=lambda p: -p.score)
    return picks[:top_n]
