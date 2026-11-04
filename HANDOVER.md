# Yes Bro: GitHub Actions + Gemini Flash handover

## What this is
Yes Bro (yesbrohq.com) used to be written by Grok Bot routines. Those routines stay paused.
This package runs the paper every morning on GitHub Actions, with Gemini Flash writing the
headlines and summaries. YouTube talks are dropped completely.

Publishes from: **GitHub repo Earth5R/yesbro**, branch **main**, GitHub Pages at the repo root
(custom domain yesbrohq.com). Never delete or edit the `CNAME` file.

## What runs each day
1. Gather RSS / Google News for Daily and all field papers.
2. Gemini picks stories per section (one call per paper).
3. Fetch article text.
4. Gemini writes headlines and 30 to 50 word deadpan summaries (batched).
5. Template memes (no AI by default, saves quota). Columns are off by default.
6. Jobs, events, research, student opps (best effort). **Talks are not run.**
7. Build newsprint HTML, publish into the Pages paths, refresh landing + sitemap.
8. Commit and push with `GITHUB_TOKEN` (`contents: write`).

Schedule: `0 0 * * *` UTC = about 5:30 IST. Also supports **workflow_dispatch** for a manual run.

## One-time setup
1. Get a free Gemini API key at https://aistudio.google.com/apikey
2. In the Earth5R/yesbro repo: Settings → Secrets and variables → Actions → New repository secret
   - Name: `GEMINI_API_KEY`
   - Value: the key
   Or from a machine with `gh` auth: `gh secret set GEMINI_API_KEY --repo Earth5R/yesbro`
3. Push this package into the repo (the `pipeline/` folder and `.github/workflows/daily.yml`).
   The workflow expects builder code at `pipeline/yesbro/` and writes HTML to the repo root.
4. Enable Actions on the repo if they are not already on.
5. Run once by hand: Actions → Yes Bro daily → Run workflow.

## Daily cost
Expected: **free**, on Gemini Flash Lite free tier (`gemini-3.1-flash-lite` by default).
The pipeline batches hard (about 1 pick call + a few copy calls per paper, template memes).
If free-tier daily request caps are hit, remaining papers fall back to teaser-based copy so the
site still updates. Paid Gemini is optional if you want higher volume or `gemini-3.5-flash`.

GitHub Actions minutes: public repo unlimited, private repo free allowance is enough for one
daily job.

## How to change papers or prompts
- Paper list / sections: `pipeline/yesbro/editions/config/<key>.json` and the feed modules under
  `pipeline/yesbro/editions*/`.
- Voice and writing rules: `pipeline/prompts/VOICE.md` plus `picks.txt`, `copy.txt`, `meme.txt`,
  `column.txt`.
- Enable AI memes: set repo variable / env `YESBRO_AI_MEMES=1`.
- Enable AI columns: `YESBRO_AI_COLUMNS=1`.
- Limit papers for a test run: workflow input `eds` (for example `daily,ux,ai`) or env `YESBRO_EDS`.
- Dry run without Gemini: workflow input `dry_run=1` or env `YESBRO_DRY_RUN=1`.
- Model override: env `YESBRO_GEMINI_MODEL` (default `gemini-3.1-flash-lite`).

## Local run (this box)
```bash
export YESBRO_ROOT=/workspace/yesbro
export YESBRO_SITE=/workspace/yesbro-site
export PATH="/workspace/yesbro/.venv/bin:$PATH"
export PYTHONPATH=/workspace/yesbro_actions/pipeline:/workspace/yesbro
export YESBRO_GEMINI_MODEL=gemini-3.1-flash-lite
# optional: YESBRO_DRY_RUN=1
python /workspace/yesbro_actions/pipeline/run_daily.py --date YYYY-MM-DD --per-section 8
```

## What was dropped
- `talks.py` and all yt-dlp / YouTube talk gathering.
- Talk sections no longer appear (builder only shows Talks when a talks JSON is passed; the
  pipeline never passes one).
- Grok Bot routines are not resumed and are not called from Actions.

## Risks to know
- Some publishers block datacenter / GitHub IPs. Fetches then fall back to RSS teasers.
- Gemini free-tier daily request caps vary by model. Flash (non-lite) can be as low as ~20
  requests/day. Prefer Flash Lite. If caps trip, copy falls back automatically.
- Nobody reviews each day's page before it goes live. House rules are baked into the prompts
  and `blocklist.py` still strips Begin Group and trade-fair free coverage.
- Image fetching can be slow or flaky on Actions. A run still publishes text-only stories.
