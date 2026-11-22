# Getting Critiq live

Do these in order. Steps 1 to 4 are one-time setup, and each takes about 5 minutes.

## 1. Run it on your laptop first

```bash
cd critiq
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests          # should say 12 passed
streamlit run app.py
```

It opens at http://localhost:8501. With no secrets file it runs in **local mode**: you paste your TMDB key in the sidebar, there's no login, and ratings are saved to `data/critiq.db` on your machine.

**OMDb key (for IMDb and Rotten Tomatoes scores):** Go to omdbapi.com/apikey.aspx, choose FREE, enter your email, and click the activation link they send you. Add it to `.streamlit/secrets.toml` as `OMDB_API_KEY = "..."`.

**TMDB key:** Sign up at themoviedb.org, then go to Settings → API → request a key (choose "Developer"). Copy the "API Key" (v3).

## 2. Create the database (Neon, free Postgres)

1. Sign up at neon.tech and create a project (any name or region).
2. Click **Connect** and copy the connection string. It looks like
   `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`.

Critiq creates its own tables the first time it connects, so you don't need to write any SQL.

## 3. Set up "Sign in with Google"

1. Go to console.cloud.google.com and create a project called "Critiq".
2. Go to **APIs & Services → OAuth consent screen**. Choose External, set the app name to Critiq, and add your email. Under **Audience**, add yourself as a test user, or publish the app later so anyone can sign in.
3. Go to **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized redirect URIs: add both
     - `http://localhost:8501/oauth2callback`
     - `https://<your-app-name>.streamlit.app/oauth2callback` (add this one once you know the URL from step 5)
4. Copy the **Client ID** and **Client secret**.

## 4. Fill in your secrets locally

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Paste in the TMDB key, the Neon URL and the Google values. For `cookie_secret`, use any long random string, for example the output of `python -c "import secrets; print(secrets.token_hex(32))"`.

Run `streamlit run app.py` again. You should now see a Google sign-in page, and your ratings are stored in Neon.
`secrets.toml` is git-ignored, so **never commit it**.

## 5. Push to GitHub

```bash
git init
git add .
git commit -m "Critiq: movie & show recommender"
git branch -M main
git remote add origin https://github.com/<you>/critiq.git
git push -u origin main
```

## 6. Deploy on Streamlit Community Cloud

1. Go to share.streamlit.io and sign in with GitHub. Click **Create app**, pick the `critiq` repo, branch `main`, file `app.py`, and choose a URL like `critiq`.
2. Under **Advanced settings → Secrets**, paste your whole `secrets.toml`, **but change `redirect_uri`** to `https://<your-app-name>.streamlit.app/oauth2callback`.
3. Click Deploy. Make sure the same redirect URI is in your Google OAuth client (step 3).

Every `git push` to `main` redeploys the app automatically.

## Troubleshooting
- **"redirect_uri_mismatch" from Google:** The URI in your secrets and in Google Cloud must match exactly.
- **"Access blocked" on sign-in:** Your Google account isn't listed as a test user yet, or the app hasn't been published.
- **App "sleeping":** Free Streamlit apps sleep after a period with no visitors. Click wake up. Your data is safe in Neon.
