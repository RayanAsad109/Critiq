# 🎬 Critiq

Rate the movies and shows you've watched (0–5 in quarter-star steps), say *why* in a sentence, list your favourite actors and directors, and get personalised recommendations, each with an explanation.

## How it works

1. **Data**: Titles, genres, keywords, cast, directors/creators and plot summaries come from the [TMDB API](https://developer.themoviedb.org/).
2. **Candidates**: Titles TMDB lists as related to the things you rated highly, the best-known work of your favourite people, and (when filters are set) TMDB Discover results for your genres, years and minimum score.
3. **Vectors**: Each title becomes two TF-IDF vectors (scikit-learn):
   - **tags**: genres, keywords, cast, directors
   - **text**: overview, tagline and keywords as words and bigrams
4. **Taste profile**: A weighted sum of the titles you rated. Ratings map linearly to weights from −1 to +1, with 2.5 as neutral, so titles you disliked push the profile *away* from similar things.
5. **Reviews**: Your written reviews are vectorised in the same vocabulary and added in the direction of their rating. Opinion words ("loved", "amazing", "boring") are stripped first, because the star rating already carries the sentiment. That way only words about the content, like "twist ending" or "alien language", count.
6. **Score**: `0.65·cos(tags) + 0.35·cos(text)`, plus boosts for favourite actors and directors and a small quality prior from TMDB's vote average.
7. **Filters**: Genres, a release-year range and a minimum TMDB score narrow the pool before scoring. TV genre names are mapped to their movie equivalents, so "Science Fiction" also matches "Sci-Fi & Fantasy".
8. **Explanations**: Each recommendation names the rated title that contributed most to its score ("Because you rated Inception 5/5"), the favourite people it features, and the words from your reviews it matched.

## Ratings from IMDb and Rotten Tomatoes

TMDB supplies each title's IMDb id, and [OMDb](https://www.omdbapi.com/) turns that into IMDb and Rotten Tomatoes scores. These scores are cached for a week. When minimum-score filters are set, Critiq looks up scores lazily, walking down the ranked list in batches until it has 12 titles that pass, so it stays well inside OMDb's free tier of 1,000 lookups a day.

## Movie night, watchlist and other features

- **Movie night**: blend your ratings with a friend's to find titles you'll *both* like. Each of you is scored against the same candidate pool, scores are scaled to 0–1, and they're combined with a "least misery" rule, $0.6\min(a,b) + 0.4\,\text{mean}(a,b)$, so a title one of you would hate can't win. Invite a friend with a private link (when deployed with sign-in) or by swapping backup files.
- **Watchlist**: "Save for later" on any title. Saved titles appear on Home and in Library, and drop off automatically once you rate them.
- **My streaming services**: only recommend what's included with your subscriptions in your region (TMDB / JustWatch data).
- **Spin the reel**: a slot-machine pick from your recommendations, weighted by match score.
- **Lights down**: while candidates load, the house dims, the curtains close and a 3-2-1 film leader counts down. Then the curtains part on your picks.
- **Letterboxd import**: upload your Letterboxd export `.zip`. Ratings, reviews and watchlist are matched to TMDB in parallel and imported.

## Home

- **Tonight's feature**: your single best pick, shown big on its own backdrop with the reason Critiq chose it, a trailer link, Save for later, and *Not tonight* to see the next pick. Picks are recomputed only when your ratings or streaming services change. New users see what's trending instead.
- **Film-strip rows** you can scroll sideways: your watchlist, "Because you loved ___", "New on" your streaming services, trending this week, and your last Discover results.
- **One-tap moods** that jump to Discover with matching filters, plus a stats line: how many you've rated, your average, and how much harsher or kinder you are than IMDb.

## Details pages

Click any poster to open a page with the backdrop, cast with character names, key crew, release details, genres and themes, a trailer link, where to stream, rent or buy it in your region (JustWatch data via TMDB, set with `REGION`, default `CA`), your rating, why Critiq recommended it, and more titles like it. Pages have their own URLs, so refresh and the back button work.

## Accounts & storage

- **Sign in with Google** uses Streamlit's built-in OIDC login, and each user only sees their own ratings.
- **Database:** SQLAlchemy over Postgres (Neon) in production, or a local SQLite file in development. One `ratings` table is keyed by user and title, and a `prefs` table holds favourite people and the mood text.
- **Backup / restore:** You can export your ratings as JSON and import them again.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

With no secrets file it runs in single-user local mode. See **[DEPLOY.md](DEPLOY.md)** for the database, Google login and Streamlit Cloud setup.

## Project layout

| File | What it does |
|---|---|
| `app.py` | Streamlit app: login, Home / Rate / Library / Discover sections, details pages, rating dialog |
| `ui.py` | Visual layer: global CSS, poster cards, marquee header |
| `.streamlit/config.toml` | Theme: colours, Newsreader serif (text) and Archivo (signage), radii |
| `recommender.py` | TF-IDF taste profile, scoring and explanations (pure Python, no I/O) |
| `tmdb.py` | TMDB API client with disk caching and parallel fetches |
| `blend.py` | Movie night: combines two people's scores (least-misery blend) |
| `letterboxd.py` | Parses a Letterboxd data export (ratings, reviews, watchlist) |
| `omdb.py` | OMDb client for IMDb / Rotten Tomatoes scores, plus lazy min-score filtering |
| `storage.py` | Database layer (SQLAlchemy) |
| `tests/` | pytest suite for the recommender and storage |

## Tests

```bash
python -m pytest tests
```

The tests run offline. The recommender tests use hand-made titles and check that disliked titles rank last, that reviews change the scores, the actor boost, the movie/show filter, cold start from the mood box alone, and candidate selection. The storage tests check that ratings persist after reopening, that users stay separate, and that backups round-trip.
