# Yes Bro Newspaper: daily build

There are two outputs from the same stories file:
1. **Newsprint HTML**, the main reading copy: `yesbro_YYYY-MM-DD.html`. It has cream paper, a blackletter masthead,
   Playfair Display headlines, Libre Caslon body text, ink-brown text (never pure black), double rules and ruled columns.
2. **Grok canvas page** (canvas_id bdfdced6-929c-4d2d-b842-8e6ea5b68fe2). It uses the app theme only, because the canvas
   compiler rejects literal colours. It cannot have the newsprint look.

Drive: My Drive / "Yes Bro Newspaper" (folder id 1ZkCjVjcLqX-JV6CeemNlTH1QzlURA6a4), private.

## House voice rule (all papers and the landing page, from 25 Oct 2026)
- **Fun, not funny.** Yes Bro is the cool, post Gen Z alternative to traditional media and it makes reading fun. The wit is dry, smart and understated, a smirk and not a punchline. No slapstick, no meme speak, no trying too hard, no cringe.
- Deadpan, serious faced humour runs full on in everything we write around the news: absurd things said straight, grand language for trivial things, dry understatement, one line twists. Never explain the joke. No "lol" and no emoji punchlines.
- This covers section intros, the Jobs, Events, Tenders and Funding blurbs, empty state lines, menu microcopy, landing card mottos, footers, the FIELDWORK ads (still professional, no intern words) and the "Tell us" button.
- **News voice (from 26 Oct 2026, replaces the old strictly factual rule):** summaries get the TechCrunch deadpan. Accurate and sourced, but dry and knowing: quote the company's own grand claims straight, set them beside the plain facts, end where useful on one short dry observation. Humour comes from framing and selection only, never from invented facts, made up quotes or claims not in the source. Headlines stay factual and clear (wry is fine, misleading is not). Never mock victims, tragedies, deaths, illness, disasters, ethnic or religious groups or private lives, and leave those summaries plain. Politics stays neutral, dry about process at most. Healing stays kind and evidence-minded, Schools stays gentle. Full guide with the Ask Proxy reference passage and before and after examples: `VOICE.md`.
- Yes Bro Explains columns may carry a dry deadpan touch, but every fact stays accurate.
- The copy rules still apply: no em dashes, en dashes or semicolons in visible copy, never invent facts, Earth5R is never an NGO.
- **No counting in house copy (from 25 Oct 2026, owner feedback).** Copy that counts things reads as machine written. In mottos, ears, card blurbs, section intros, footers, ads, menus, buttons, the home screen note and column decks, never count our own things: no "thirteen papers", no "30 jobs", no "85 events", no "all 13 papers", no "seven sections". No section, menu or card counters either. Avoid the other obvious tells too: "X things, one Y, no Z" lines, tricolons and three item lists, "not X, but Y" constructions and overly neat parallel lines. Write the way a sharp human editor would, dry and deadpan. Real numbers inside news summaries, prices, dates, deadlines and the data in columns are fine. `build_html.py` and `build_landing.py` print a "HOUSE VOICE WARNING" line for any count they find in house copy. Fix it before publishing.

## Daily workflow
1. Write `stories_YYYY-MM-DD.json`: a list of `{ "section", "headline", "summary", "url" }`.
   The section is one of: India Politics, India Overall, India Startups, India ESG and Environment,
   Global Overall, Global AI and Technology, Global ESG and Environment, Health, Space and Science, Humour.
   Health covers physical health, mental health and nutrition or fitness without naming those subtopics in the heading,
   stays evidence-minded and never presents a remedy as a cure. Space and Science leads with ISRO then NASA, ESA and discoveries.
   Humour is real offbeat and quirky news only: never political, religious, communal, about victims, deaths, illness, disasters,
   or jokes about named groups or private people. Gather sources live in gather29/feeds.py keys HE, SS and HU
   (The Hindu Science and Health, ScienceDaily, Phys.org, NASA, STAT, India Today Trending, Indian Express Trending,
   Hindustan Times Trending, Guinness and odd-news Google News queries).
   Summaries should be 30-50 words, with no em dashes or semicolons.
   Add any new site's display name to `sources.py`.
2. Fetch the images (both modes are cached in `cache/`):
   ```
   python3 fetch_images.py stories_D.json stories_D.html.json --mode html     # original og:image URLs
   python3 fetch_images.py stories_D.json stories_D.out.json                  # small thumbnails (canvas + fallback)
   ```
   - HTML mode keeps the original og:image URL whenever the image host serves it without the publisher's
     Referer. When the host blocks hotlinking, it embeds a 640px WebP (q60) instead.
   - Site-wide logos and placeholders are skipped, and those stories render text only.
3. Build the HTML:
   ```
   python3 build_html.py stories_D.html.json "Sunday 25 October 2026" yesbro_D.html --fallback stories_D.out.json --config editions/config/daily.json
   ```
   `editions/config/daily.json` sets the title "Yes Bro Daily" and the home screen tags (`manifest.json`, `../icon-512.png`).
   `--fallback` adds the small thumbnail as an onerror backup, in case a remote image fails in the browser.
4. Preview (optional): render `yesbro_D.html` with headless Chrome or Playwright
   (`executable_path="/usr/bin/google-chrome"`) and screenshot it to `preview_D.png`.
5. Upload with the Google Drive connector `create_file`:
   - `contentMimeType` "text/html"
   - `disableConversionToGoogleType` true (otherwise it becomes a Google Doc)
   - `parentId` the folder above
   - Never share the file.
6. Canvas (optional):
   `python3 build_canvas.py stories_D.out.json "Sunday 25 October 2026" > canvas_D.tsx`, then WriteCanvas on the canvas_id.

## Section menu (all papers, built in automatically)
- `build_html.py` adds a fixed "Sections" button (three-line icon) at the top left of every paper, main and editions. It stays visible while scrolling.
- Tapping it slides open a left panel with a blackletter "Yes Bro" header, then every section in order with its story count.
  When a paper has Jobs (`--jobs`), a highlighted "Jobs" item sits at the top. When the paper has the FIELDWORK house ad, a "Fieldwork" item
  links to it (`id="fieldwork"` is added to the `<aside class="housead">` automatically). The last item goes back to the top.
- Each link smooth scrolls to its section and closes the panel. The panel also closes with its X button, a tap outside it, or Esc.
- Anchors are stable: each section is `id="<slug of section name>"` (for example `#india-politics`), Jobs is `#jobs`, FIELDWORK is `#fieldwork`, top is `#top`.
- Plain HTML, CSS and about 15 lines of vanilla JS, no libraries. The top section nav under the dateline is unchanged.
- It is always on, so builds are no longer byte for byte identical to the pre-menu builds (the old builder is at `/tmp/build_html.orig.py` for this session only).
- Check it with `python3 menushot.py <url> <out.png> <1 if the paper has jobs else 0>`: 390x844 iPhone viewport, opens the menu, checks every link target,
  tests Esc, outside tap, X and a jump, and writes `<out.png>` (menu open) plus `<out>_jumped.png`.
- The menu ends with "Top of this paper" (#top) and "Back to the front page", which links to the landing page https://yesbrohq.com/ (`HOME_URL` in `build_html.py`). The masthead title in every paper also links to the landing page.

## Notes
- The HTML loads Google Fonts and the publisher images over the network. Offline it falls back to Georgia or Times,
  plus the embedded thumbnails.
- The layout is a lead story in a double-width column with two ruled columns beside it. Below 1050px wide
  it switches to two columns, and below 640px to one column.
- Google Drive does not render HTML. Its preview shows the source text, so download the file and open it in a browser.

## Site layout and publishing (since 25 Oct 2026)
Repo `/workspace/yesbro-site` (Earth5R/yesbro, GitHub Pages, custom domain yesbrohq.com). Never delete or edit `CNAME`. Always `git pull --rebase` before committing.

| URL | What | Written by |
|---|---|---|
| https://yesbrohq.com/ | Landing page (front door): pick your paper | `build_landing.py` |
| https://yesbrohq.com/daily/ | Yes Bro Daily, the main Daily paper | main paper routine |
| https://yesbrohq.com/daily/archive/YYYY-MM-DD.html | Daily back issues | main paper routine |
| https://yesbrohq.com/ux/, /architecture/, /schools/ | Field editions | field editions routine (see editions.md) |

Old root `archive/2026-10-25.html` is a redirect stub to `/daily/archive/2026-10-25.html`. Do not add new files to root `archive/`.

### Main paper publish steps
```
cd /workspace/yesbro-site && git pull --rebase
cd /workspace/yesbro && python3 publish.py daily yesbro_D.html D   # writes daily/index.html and daily/archive/D.html (paths, canonical and og:url fixed), then sitemap
python3 build_landing.py          # refreshes root index.html + manifest.json with today's top headlines, then sitemap.xml and robots.txt
cd /workspace/yesbro-site && git add daily index.html manifest.json sitemap.xml robots.txt && git commit -m "Daily: <date>" && git push
```
`publish.py <key> <built.html> <YYYY-MM-DD>` works for every paper (keys: daily ux arch schools sustainability startups highered consulting health marketing finance aviation). The old manual `cp` plus `sed` steps are replaced by it.

### Landing page (`build_landing.py`)
- `python3 build_landing.py [--site /workspace/yesbro-site] [--stories-dir /workspace/yesbro]` writes only root `index.html` and `manifest.json` (name "Yes Bro", start_url "/").
- Cards come from the `EDITIONS` list at the top of the script (key, name, path, stories prefix, config JSON, one line blurb, card photo). A new paper is one line.
- Card photos live in the site repo at `img/landing/<key>.webp`: free licence stock (Unsplash or Pexels), grayscale, 16:9, 800x450, WebP q58, under 80KB. Sources are listed in `img/landing/CREDITS.md`. A missing photo file prints a warning and the card shows without a photo.
- Each card shows the price line and motto from the edition config, and the first headline of the newest `stories_<prefix>DATE.json`. A missing file just leaves the card without a headline.
- Includes the FIELDWORK house ad (https://earth5r.org/fieldwork/, never call Earth5R an NGO) and a "Your field isn't here yet? Tell us" mailto button to ontheworldroad@gmail.com.
- Remember my pick: clicking a card stores `yesbro.pick` in localStorage. Next visit shows a slim "Continue to Yes Bro X" bar with "Show all papers" and "Forget my pick". It never redirects on its own.
- The script refuses to write if visible copy contains an em dash, en dash or semicolon.
- Run it after any paper publishes (cheap, idempotent). Check it with `python3 landingshot.py <url> preview_landing.png` (390x844 phone, writes full page, `_top` and `_continue` shots, and tests the bar).

## Yes Bro Explains: our own columns (since 25 Oct 2026)
About 10% of each paper is original analysis that can rank on Google. Each paper has one column series.
- **Write:** `columns/<key>/YYYY-MM-DD-<slug>.md` with front matter between `---` lines: `title`, `slug` (SEO slug, lowercase with hyphens), `date` (YYYY-MM-DD), `dek` (one or two sentences), optional `description` (meta description, about 155 characters). Body is light markdown: paragraphs, `## ` subheads, `- ` lists, `**bold**`, `*italic*`, `[text](url)`.
- **No-intern rule (permanent, from 25 Oct 2026):** never write intern, interns, internship or internships in our own copy (columns, configs, section names, jobs intros, menu labels, ad copy, landing, meta and SEO tags). Readers are professionals. Earth5R's offer is the FIELDWORK fellowship: hands-on fieldwork with real people, real conversations, real users and real research. Link https://earth5r.org/fieldwork/ (or another verified earth5r.org page that is not an internship page), never an earth5r.org internship URL. Internship listings are never shown (see below). Our labels say "Jobs" or "Jobs and student opportunities". Earth5R is never an NGO. Enforced by `columns.py check` and `columns.py publish`, `build_landing.py` and the config check in `build_html.py` (all fail on a hit).
- **Rules:** 500 to 800 words. Plain, smart, lightly witty newspaper voice. Every fact, number, name and quote comes from a source opened that run and is cited with an inline link. Never invent anything. No em dashes, en dashes or semicolons. Earth5R is never an NGO. Link 1 or 2 verified earth5r.org pages only where natural. Byline is always "Yes Bro Desk".
- **Check:** `python3 columns.py check [keys]` (word count, banned characters, slug, at least 3 links, every link loads; a 403 from a bot blocking site is reported but allowed). `--no-net` skips the link test.
- **Publish:** `python3 columns.py publish [keys] [--site /workspace/yesbro-site]` writes `/<folder>/explains/<slug>/index.html` for every column, `/<folder>/explains/index.html` (all columns, newest first), then the sitemap. Daily lives at `/daily/explains/`.
- **Featured box:** `build_html.py` calls `columns.box_html(key, date)` and puts a "Yes Bro Explains" box after the first section (id `explains`, with a menu item). It shows the newest column dated on or before the paper date, for 7 days (`KEEP_DAYS`). After that the box disappears until a new column is written. A broken column file never stops the paper build.
- Column pages: newsprint look, masthead, kicker, H1, dek, byline with date and read time, auto "Sources and links in this column" list, "More Yes Bro <field>" link, Earth5R footer credit, and NewsArticle JSON-LD.

## SEO (since 25 Oct 2026)
- Each `editions/config/<key>.json` has `key`, `url` (https://yesbrohq.com/<folder>/), `seo_title` and `seo_desc`. `build_html.py` uses them for the `<title>`, meta description, canonical, robots, Open Graph and Twitter card tags (share image `img/landing/<key>.webp`) and CollectionPage plus ItemList JSON-LD (top 3 stories per section). Publisher is Yes Bro with parentOrganization Earth5R.
- No JobPosting schema for third party listings. Ever.
- Landing page: keyword title and description, canonical https://yesbrohq.com/, OG and Twitter tags, WebSite plus Organization plus CollectionPage JSON-LD.
- Archive pages stay indexable. `publish.py` rewrites their canonical and og:url to the archive URL itself.
- Footer credit on every paper, column page and the landing page: "A product of Earth5R" linking https://earth5r.org/ (one modest link).
- **Sitemap:** `sitemap.py` (`python3 sitemap.py [--site ...]`) writes `sitemap.xml` (landing, all papers, explains indexes, columns, archives, lastmod from the archive date or JSON-LD) and `robots.txt` pointing to it. It runs automatically at the end of `publish.py`, `columns.py publish` and `build_landing.py`, so every publish refreshes it. Commit `sitemap.xml` and `robots.txt` with each push.
- Live sitemap: https://yesbrohq.com/sitemap.xml

## House copy rules
- **No internship listings ever, conflict of interest with FIELDWORK (final, 25 Oct 2026):** no internship listings anywhere on Yes Bro, Higher Ed and Schools included. Jobs sections list real jobs only: full-time, part-time, contract, graduate and entry-level jobs, education-sector roles and airline cadet programmes. `jobs.py` enforces it with a hard filter (`NO_INTERN`, `is_internship`) on title, employment type (Lever commitment, Ashby and Himalayas employmentType, SmartRecruiters typeOfEmployment), org, note and URL, applied to every source and every seed in main(), with an assert before the file is written. Never add internship seeds or internship-focused sources or queries. FIELDWORK is how readers get job-ready and stand out.
- **No-intern rule (permanent, from 25 Oct 2026):** never write intern, interns, internship or internships in our own copy (columns, configs, section names, jobs intros, menu labels, ad copy, landing, meta and SEO tags). Readers are professionals. Earth5R's offer is the FIELDWORK fellowship: hands-on fieldwork with real people, real conversations, real users and real research. Link https://earth5r.org/fieldwork/ (or another verified earth5r.org page that is not an internship page), never an earth5r.org internship URL. Internship listings are never shown (see below). Our labels say "Jobs" or "Jobs and student opportunities". Earth5R is never an NGO. Enforced by `columns.py check` and `columns.py publish`, `build_landing.py` and the config check in `build_html.py` (all fail on a hit).
- No em dashes, en dashes or semicolons in visible copy. Never invent facts.

## Since 25 Oct 2026: Business, events, tenders, pills and home screen
- 13 papers: Daily plus UX, Architecture, Schools, Sustainability, Startups, Higher Ed, Consulting, Health, Marketing, Finance, Aviation and Business (https://yesbrohq.com/business/). The landing page has 13 cards, Business second. Business opens with Indian Business news, and tenders sit further down the page, never at the top of the page or the menu.
- Daily routine order: news pipeline per paper, then `jobs.py <key>` one paper at a time, then `events.py --date D` (all papers at once), then `opps.py --date D` (Business), then `bash rebuild_today.sh D "<Day date>"`, then pull with rebase, commit (never CNAME), push and curl every paper with `-m` timeouts.
- `build_html.py` flags: `--events events_<key>_D.json` for every paper, `--opps opps_business_D.json` for Business. Both are skipped quietly when the file is missing.
- Every paper has the All Yes Bro papers pills (top and bottom) and the collapsible "Add Yes Bro to your home screen" note. `pwa.py` writes the per folder manifests. See editions.md for details.

## Yes Bro Healing (since 26 Oct 2026)
- **Yes Bro Healing** (`healing`, folder `healing/`, config `editions/config/healing.json`, https://yesbrohq.com/healing/, "Price: Free, unlike the retreat"). Personal wellbeing news, kept separate from the Health paper (Health covers medicine, public health and health tech). Sections: Mental Health, Mindfulness and Meditation, Sleep and Balance, Body and Movement, Food and Nutrition, Longevity, Alternative Therapies, then Jobs and Events.
- **Evidence rule for Healing:** summaries report what the source says, including its caveats (small sample, mice, observational, preprint, low certainty). Never present an alternative therapy, supplement or diet as a proven cure. Skip promotional pieces, cure claims, press-release mills (openPR, TradingView, Dr Axe style sites) and social posts.
- **Sources:** `editions4/feeds_healing.py` (merged into `run26/feeds_all.py`): Mindful.org, Greater Good, ScienceDaily (mind and brain, nutrition, fitness, sleep, healthy ageing, alternative medicine), NYT Well, Guardian wellbeing and mental health, BBC Health, The Hindu, Indian Express, HT and TOI health, WHO, NPR, plus Google News `when:3d` queries (Harvard Health and NCCIH via site: queries, mental health India, meditation, yoga, ayurveda, acupuncture and shiatsu, breathwork, sleep, nutrition, gut health, longevity, loneliness and burnout).
- **Jobs:** `python3 jobs.py healing` (Greenhouse Talkspace, Calm, Oura, Lever Lyra Health, Himalayas wellness, therapist, counselor, yoga, nutritionist, health coach and meditation queries). `HEAL_RE` keeps wellbeing roles and `HEAL_NO` drops finance, sales, engineering and talent pool posts.
- **Events:** `events/seeds.json` entries with `"eds": ["healing"]` (mental health conferences, Ayurveda, yoga and wellness festivals, each checked on its official page), plus Luma matched by the `healing` keyword regex in `events.py`.
- **NO FIELDWORK OR EARTH5R ON HEALING (permanent, owner, 26 Oct 2026):** Healing carries no FIELDWORK ad, no FIELDWORK jobs box, no Earth5R credit and no Earth5R JSON-LD parent, in the paper, its menu, its footer and its Yes Bro Explains columns. Its house ad and promotion are for the owner's own site, Mindful Wholeness (https://mindfulwholeness.org/). Config keys: `ad_html` (boxed classic ad, `ad_id` "mindfulwholeness", menu label from `ad_menu` and `ad_menu_note`), `ad2_html` and `ad2_after` (smaller second ad), and `no_earth5r: true`, which drops the footer credit and JSON-LD parent and makes `build_html.py` fail if the output mentions FIELDWORK or Earth5R. `columns.py` skips the Earth5R credit for keys in `NO_E5R`. Never add `jobs_ad_html` or a FIELDWORK ad to Healing, in builds or columns. Mindful Wholeness ad copy uses only what mindfulwholeness.org states (Shiatsu, reflexology, organic facials and mindfulness-based counselling with Sunil, home visits in Mumbai, counselling online, fees on enquiry, WhatsApp messages only, complementary therapies that are not a substitute for medical or emergency care). No health claims or cures in the ad.
- **Columns:** proposed Sunday and Thursday for Healing (Thursday becomes the only morning with a fifth column). Columns for Healing never mention FIELDWORK or Earth5R.


## Yes Bro AI (since 26 Oct 2026)
- **Yes Bro AI** (`ai`, folder `ai/`, config `editions/config/ai.json`, https://yesbrohq.com/ai/, "Price: Free, unlike the compute"). The 15th paper. Artificial intelligence news in eight sections: Models and Labs, AI Products and Tools, AI in India, AI Startups and Funding, Research and Papers, Chips and Compute, AI at Work, Safety and Policy. Safety and Policy stays factual and neutral: no election, voter data, defence, weapons or bloc politics stories. Avoid repeating the Daily paper's Global AI stories, or go deeper on them. Landing card blurb "For anyone keeping up with artificial intelligence, minus the launch livestream", image `img/landing/ai.webp` (Wikimedia, CC BY 2.0, see CREDITS.md). BRAND_W 'AI' = 1.09 in build_landing.py and columns.py.
- **Sources:** `editions4/feeds_ai.py` (merged into `run26/feeds_all.py`): TechCrunch AI, The Verge AI, VentureBeat, MIT Technology Review, Ars Technica, The Decoder, MarkTechPost, OpenAI, Google DeepMind, Google AI, Hugging Face, The Register, AIM, Inc42, YourStory, Medianama, ET AI, Mint AI, Tom's Hardware, Wired AI, ScienceDaily AI, MIT News, plus Google News queries. `run26/gather_ed_append.py ai` appends the ai bucket to items_all.json when the paper is gathered on its own.
- **Jobs:** `python3 jobs.py ai` (Greenhouse Anthropic, Scale AI, Databricks, Google DeepMind, Glean and the India boards, Lever Mistral and the India boards, Ashby OpenAI, Sarvam AI, Cohere, Perplexity, Himalayas machine learning engineer, AI engineer, data scientist, LLM, applied scientist and MLOps queries). `AI_RE` keeps machine learning, AI research and AI engineering roles. `AI_NO` drops interns, sales, recruiting, legal and admin roles.
- **Events:** `events/seeds.json` entries with `"ai"` in `eds` (AI conferences and summits, each checked on its official page, plus Bengaluru Tech Summit, Web Summit and the Elets BFSI AI Summit shared with other papers), plus Luma matched by the `ai` keyword regex in `events.py`.
- **Ad:** the FIELDWORK house ad and jobs box as on the other professional papers, pitched as hands-on fieldwork. Never say intern or internship.
- **Meme:** hand-written `memes/ai_<date>.json` from a non-political story outside Safety and Policy (SKIP_SECTIONS skips it anyway). Persona "Me, waiting for my GPU quota to reset".
- **Columns:** proposed Wednesday and Sunday for AI (Wednesday becomes a five column morning). The Columns routine is unchanged until the owner updates it. The Yes Bro Explains box appears on its own once `columns/ai/` has a column.
## Yes Bro Packaging (since 27 Oct 2026)
- **Yes Bro Packaging** (`packaging`, folder `packaging/`, config `editions/config/packaging.json`, https://yesbrohq.com/packaging/, "Price: Free, the wrapping costs extra"). The 16th paper. Packaging industry news, plastic first, India first then global, in eight sections: Plastic Packaging, Polymers and Resin Prices, Recycling and Recycled Content, EPR and Plastic Waste Rules, Paper and Sustainable Packaging, Machinery and Converting, FMCG and E-commerce Packaging, Deals and Funding. Aim for 60 or more stories. Landing card blurb "For anyone who makes, buys or recycles packaging, plastic first", image `img/landing/packaging.webp` (Wikimedia, CC BY-SA 4.0, see CREDITS.md). BRAND_W 'Packaging' = 4.93 (measured in Chrome) in build_html.py, build_landing.py and columns.py.
- **Expos are never free coverage.** Trade fairs, expos, trade shows and roadshows (Plastindia, IPLEX, PackEx, interpack, K Show, PACK EXPO, Chinaplas, Labelexpo, drupa, Loupe India and others) are caught by `_TRADE` and the trade-word pattern in `blocklist.py` FAIR_PATTERNS plus their domains in FAIR_DOMAINS, so the builder drops them and prints `BLOCKED: fairs`. They appear only as paid listings via `sponsors.json`, after Saurabh confirms. The config carries a second ad slot (`ad2_html`, after section 6): "Your expo here. Ask Saurabh." with a mailto to ontheworldroad@gmail.com.
- **Sources:** `editions4/feeds_packaging.py` (merged into `run27/feeds_all.py`): Packaging South Asia, Packaging Dive, Plastics Today, Packaging World, Packaging News UK, Recycling Today, Circular Online, plus about 30 Google News queries, India first. `run27/gather_ed_append.py packaging` appends the bucket to items_all.json. Picks in `run27/picks_packaging.py`, copy in `run27/copy/copy_packaging.py`.
- **Jobs:** `python3 jobs.py packaging` (Workday Amcor, Huhtamaki and Dow, Himalayas packaging engineer, packaging technologist, plastics engineer, polymer, flexible packaging and recycling queries). `PKG_RE` keeps packaging, plastics, converting, recycling and plant roles. `PKG_NO` drops interns, software, semiconductor "package engineer" roles, card plastics, fuel recycling and legal roles. These boards had no India postings on 27 Oct, so India jobs need a new source. `tidy_loc`/`INDIA` no longer read "IN, USA" (Indiana) as India.
- **Events:** `events/seeds.json` entries with `"packaging"` in `eds` (conferences and summits only, each checked on its official page: PACK.Nxt Mumbai, World Circular Plastics and Waste-to-Value Summit Vienna, Circle Responsible End Markets summit), plus Luma matched by the `packaging` keyword regex in `events.py`. Never seed an expo.
- **Ads:** main slot is the Earth5R Corporate Sustainability Training house ad (https://earth5r.org/corporate-sustainability-training/), jobs box is the FIELDWORK pitch. Never say intern or internship. Earth5R is never an NGO.
- **Meme:** hand-written `memes/packaging_<date>.json` from a non-political story outside EPR and Plastic Waste Rules. Persona "Me, a packaging buyer refreshing the resin price sheet".
- **Also:** share line in `share.py` TEXT, a 14-line pool in `interludes.py` POOLS, a maker credit line in `maker.py` LINES ("Handle with care. He wrapped this one himself.", chosen by the owner), and `packaging` in rebuild_today.sh, run27/build_fields.sh, run27/watch_imgs.sh, columns.py EDS, events.py EDS, memes.py KEYS and the landing EDITIONS list. No column days are set for Packaging until the owner decides.

- **Yes Bro Fashion** (`fashion`, folder `fashion/`, config `editions/config/fashion.json`, https://yesbrohq.com/fashion/, "Price: Free, unlike the designer label"). The 17th paper. Fashion, jewellery and accessories news, India first then global, in nine sections: Fashion News India, Global Fashion, Jewellery, Accessories, Textiles and Craft, Sustainable and Circular Fashion, Fashion Industry, Fashion Tech and Retail, Opportunities, plus Research and Development, Talks, Events and Conferences, and Jobs. Jewellery covers gems, gold, diamonds, lab-grown and the Indian jewellery industry (GJEPC, Titan/Tanishq). Opportunities are real verified open calls, grants, design competitions and scholarships for fashion or jewellery design, never internships. Never give a jewellery or fashion trade fair free coverage (IIJS, Vicenzaoro, JCK, Premiere Vision and the like). Fashion weeks and runway shows are fine. Landing card blurb "For anyone who follows fashion, jewellery and accessories, India first", image `img/landing/fashion.webp` (Pexels, see CREDITS.md). BRAND_W 'Fashion' = 3.80 in build_html.py, build_landing.py and columns.py.
- **House rules for Fashion:** FIELDWORK ad only, never call it an internship. No intern or internship in our copy. Jobs are real currently open roles, India first then Global then Remote. Events are official pages within 90 days, online allowed, no trade fairs or expos.
- **Sources:** `editions4/feeds_fashion.py` (merged into `run29/feeds_all.py`): Vogue Business, BoF, WWD, Fibre2Fashion, Apparel Resources, Economic Times Retail, Rapaport, JCK, Solitaire, GJEPC, Fashion United, Livemint lifestyle and Google News queries. `run29/gather_ed_append.py fashion` appends the bucket to items_all.json. Picks in `run29/picks_fashion.py`, copy in `run29/copy/copy_fashion.py`.


- **Yes Bro Real Estate** (`realestate`, folder `realestate/`, config `editions/config/realestate.json`, https://yesbrohq.com/realestate/, "Price: Free, no brokerage"). The 18th paper. Indian real estate trade paper, India first then global, with sustainability as one section among many. Sections: India Real Estate, Residential and Housing, Commercial, Offices and Retail, Industrial, Warehousing and Data Centres, Land, Infrastructure and Smart Cities, Policy, RERA and Regulation, Finance, REITs, Deals and Funding, PropTech, Construction and Materials, Green Buildings and Sustainability, Global Real Estate, plus Research and Development, Talks, Events and Conferences, Jobs, Meme of the day and a FIELDWORK ad for the built environment. Aim for 60 or more stories. Conferences and research are a day-one edge (CREDAI, NAREDCO, RICS, ULI, IGBC, MIPIM and PropTech summits, plus JLL, Knight Frank, CBRE, Anarock-style reports and academic notes). Property expos and housing fairs are paid listings only. Landing card blurb "For developers, brokers and anyone who has argued about carpet area", image `img/landing/realestate.webp` (Pexels, see CREDITS.md). BRAND_W 'Real Estate' = 5.50 in build_html.py, build_landing.py and columns.py.
- **Sources:** `editions4/feeds_realestate.py` (merged into `run31/feeds_all.py`): Moneycontrol, Livemint, Hindustan Times real estate, Economic Times property, Housing.com where the feed answers, plus Google News queries for India residential, commercial, industrial, RERA, REITs, PropTech, cement and green buildings, then global. `run31/gather_ed_append.py realestate` appends the bucket. Picks in `run31/picks_realestate.py`, copy in `run31/copy/copy_realestate.py`.
- **Jobs:** `python3 jobs.py realestate` (Greenhouse/Lever/Ashby boards for CBRE, JLL, Cushman, Colliers, Housing.com, PropTiger, Redfin, Zillow, Compass where they answer, plus Himalayas queries for property manager, facility manager, valuation, PropTech, leasing and quantity surveyor). `RE_RE` keeps real estate, property, housing, brokerage, facility management, valuation and PropTech roles. `RE_NO` drops interns and software "developer" false positives. India postings were thin on day one, so Remote filled the list.
- **Events:** `events/seeds.json` entries with `"realestate"` in `eds` (RICS India Built Environment Summit Mumbai, Realty and Beyond Bengaluru, Green Building Congress, CoreNet Choosing India, MIPIM Asia Hong Kong, plus GRIHA Summit tagged through), each checked on its official page within 90 days. Never seed a property expo or housing fair.
- **Also:** share line in `share.py`, interludes pool in `interludes.py`, maker credit in `maker.py`, `realestate` in rebuild_today.sh, columns.py EDS, events.py EDS, memes.py KEYS, research.py, talks.py and the landing EDITIONS list.


- **Yes Bro Auto** (`auto`, folder `auto/`, config `editions/config/auto.json`, https://yesbrohq.com/auto/, "Price: Free, no on-road charges"). The 19th paper. Indian auto trade paper, India first then global, with sustainability as one section among many. Sections: India Auto, Cars and SUVs, Two-Wheelers and Three-Wheelers, Electric Vehicles and Charging, Commercial Vehicles, Tractors and Off-Highway, Components, Tyres and Supply Chain, Sales, Dealers and Retail, Finance, Insurance and Deals, Auto Tech, Software and Autonomy, Policy and Regulation, Motorsport, Sustainability and Clean Mobility, Global Auto, plus Research and Development, Talks, Events and Conferences, Jobs, Meme of the day and a FIELDWORK ad for mobility. Aim for 60 or more stories. Conferences and research are a day-one edge (SIAM, ACMA, FADA, SAE India, ET Auto, EV summits, plus SIAM/FADA/ACMA/ICRA/CRISIL/ARAI/ICCT/IEA-style reports). Auto Expo, motor shows and trade fairs are paid listings only. Landing card blurb "For anyone who still negotiates the on-road price", image `img/landing/auto.webp` (Pexels, see CREDITS.md). BRAND_W 'Auto' = 2.20 in build_html.py, build_landing.py and columns.py.
- **Sources:** `editions4/feeds_auto.py` (merged into `run31/feeds_all.py`): ET Auto, Autocar India, CarWale, CarDekho, Moneycontrol auto, Economic Times auto, plus Google News queries for India cars, two-wheelers, EVs, CVs, components, dealers, finance, ADAS, policy, motorsport and clean mobility, then global. `run31/gather_ed_append.py auto` appends the bucket. Picks in `run31/picks_auto.py`, copy in `run31/copy/copy_auto.py`.
- **Jobs:** `python3 jobs.py auto` (Tesla, Rivian and other OEM boards where they answer, Workday India queries for automotive and EV, Himalayas queries for OEMs, components, dealers, battery and charging). `AUTO_RE` keeps automotive, EV, dealer, powertrain and mobility roles. Never internships. India first.
- **Events:** `events/seeds.json` entries with `"auto"` in `eds` (SAEINDIA APAC 23, ETAuto EV Conclave, Auto EV TechVision Summit, EV charging careers webinar), each checked on its official page within 90 days. Never seed Auto Expo, motor shows or trade fairs.
- **Also:** share line in `share.py`, interludes pool in `interludes.py`, maker credit in `maker.py`, `auto` in rebuild_today.sh, columns.py EDS, events.py EDS, memes.py KEYS, research.py, talks.py, blocklist auto-expo rules, and the landing EDITIONS list.

## Yes Bro Architecture: climate zones and Jobs vs Certifications (since 27 Oct 2026)

- New news section "Building for India's Climate Zones" in editions/config/arch.json, after Materials and Building Tech. Feeds: editions4/feeds_arch_climate.py (Google News, India, last 3 days), loaded by run27/feeds_all.py.
- Copy tuples may carry a 4th element, a kicker such as "Hot-dry zone, Bhuj". make_run.py writes it as "kicker" and build_html.py prints it above the headline (KICKER_CSS).
- "evergreen_days" in the config lets one section use older explainers (30 days for the climate section). Every other section keeps the usual date rule.
- "Jobs vs Certifications" (skills.py, config "skills_block") reads every posting in that day's jobs_arch file (Workday through its job API, other sites as page text, cached in skills_cache/), matches certifications, software and skills, and shows them with a share bar and links to the postings. No counts are printed. Postings with intern words in the title are skipped. It sits just before the FIELDWORK pitch and Jobs, is pinned in the menu, and changes daily with the jobs. If fewer than 4 postings can be read it is left out and the build carries on.

## Meme of the day (all papers, since 26 Oct 2026)
- Every paper (config `"meme": true`, set in all of `editions/config/*.json`, Daily included) carries a **Meme of the day** box after its second news section, built by `memes.py` and called from `build_html.py`. The landing page shows a small one from Yes Bro Daily after the paper cards (`build_landing.py`, `landing_meme`). Real text in HTML and CSS, in the newsprint style. No images, no hotlinks, no famous meme templates or photos.
- Formats: `nobody` (Nobody: / Absolutely nobody: / Someone: line, optional reaction), `expect` (Expectation and Reality panels), `chart` (a joke bar chart of two bars), `classic` (top and bottom caption on a dark halftone panel). Each meme references a real story in that day's edition and links to it ("From today's paper").
## Share button (all papers and the landing page, since 27 Oct 2026)
`share.py` is imported by `build_html.py` and `build_landing.py`, so every build includes it. Nothing to run by hand.
- Placement: a Share button and a WhatsApp button under the dateline, a smaller pair near the foot of the page, and on papers a "Share this paper" line in the slide-out menu.
- Share opens the phone's own share sheet (`navigator.share`, title plus share text plus URL). Browsers without it get a small panel with WhatsApp, X, LinkedIn, Telegram, Email and Copy link (the button reads "Copied" for a moment).
- The shared URL is always the stable paper URL from the config `url` (for example https://yesbrohq.com/ux/), also on archive pages. The landing page shares https://yesbrohq.com/.
- Share text: `TEXT` in `share.py`, one deadpan line per paper key, shown as "<paper title>. <line>". House copy rules apply, and `share.py` refuses dashes, semicolons and intern words at import. Keep Healing kind and free of FIELDWORK and Earth5R. The Healing guard in `build_html.py` still checks the whole page. A new paper needs a line in `TEXT`, otherwise it gets a generic fallback.
- Open Graph and Twitter card tags were already present. `og:image` now uses `img/landing/<key>.webp` only when that file exists (otherwise `icon-512.png`), and `og:image:alt` was added.
- The landing page body no longer carries `filter:grayscale(0)`. A filter on body breaks fixed positioning, which pushed the share panel to the bottom of the page.

## Maker credit (all papers and the landing page, since 27 Oct 2026)
`maker.py` is imported by `build_html.py` and `build_landing.py`. Inside every footer, under "A product of Earth5R" (which Healing does not show), it adds "Created by Saurabh Gupta". It also adds "Say hello at ontheworldroad@gmail.com", a mailto link with the paper name as the subject, followed by the paper's deadpan line from `LINES`.
- The lines in `LINES` were approved by the owner on 27 Oct 2026. Use them exactly and change them only with his approval. `GENERAL` holds spare lines for a new paper.
- `ENABLED = True` switches the credit on. Set it to False to remove it from every page on the next build.
- `maker.py` refuses dashes, semicolons, intern words, FIELDWORK and Earth5R at import, and the Healing guard still checks the whole page.

## Interludes

`interludes.py` drops a standalone deadpan strip (large dark brown Playfair italic, centred, thin rules above and below, no label) between news sections. `build_html.build()` calls it on every paper, so the morning runs include it with no extra step.

- Pools: `POOLS[key]` holds each paper's lines. They rotate by date, and each paper shows `len(pool) // 7` strips a day, so no line repeats within a week. To show more strips a day, add lines (21 lines gives 3 a day).
- Override for one day: put a JSON list of strings in `interludes/<key>_<YYYY-MM-DD>.json` (for example `interludes/ux_2026-10-27.json`). Those lines go first and pass the same checks.
- Placement: only after a news section, spread evenly down the page. A slot is skipped when the section above or below is political or policy (`POLITICAL`), when the end of the section above or the featured top of the section below mentions tragedy, death, illness, disaster or victims (`SENSITIVE`), and where the meme, the Explains box or a house ad already sits. A paper can get no strips on a heavy news day. That is intended.
- Copy rules: `validate()` runs on every pool line at import and on override lines. It rejects dashes, semicolons, "not X but Y", intern words, lol or emoji, counts of our own things and any FIELDWORK or Earth5R, and the build stops if a line fails. Humans check for tricolons and truth. Never punch down, never political. Healing and Schools stay gentle. Health never jokes about illness.
- The build log prints `interludes: N placed of M (S safe slots)` for each paper.

## Blocklist: no Begin Group coverage (since 27 Oct 2026)

`blocklist.py` is a hard blocklist. Saurabh is negotiating with Begin Group and offering them coverage, so no Yes Bro edition or the landing page may give them any coverage. **This stays until Saurabh confirms a partnership. Only he can lift it.**

- Blocked, case insensitive: any URL whose domain contains `begingroup` or `begin-expo`, Begin Group, Begin Expo, Begin India, Begin fair, Begin school visits, the International Education Fair by Begin (Mumbai Nehru Centre 25 Nov, Bangalore 20 Nov, Delhi 26 Nov), and Nehru Centre when it sits next to an education fair. The ordinary word begin ("exams begin in February") is never blocked.
- Where it runs: `build_html.py` drops matching stories, jobs, events and opps before building and logs `BLOCKED: Begin <n> (...)` in every build log. `events.py`, `jobs.py` and `opps.py` drop matches before writing their JSON. `columns.py` skips any column that mentions Begin. `memes.py` never picks a Begin story or accepts a Begin meme file. `interludes.py` rejects Begin lines. `build_landing.py` skips Begin stories for card headlines.
- Final guard: `blocklist.guard_html()` checks the finished HTML in `build_html.py`, `publish.py`, `columns.py publish` and `build_landing.py`. If anything slipped through (config copy, hand written copy, meme, column), that paper fails and is not published. `rebuild_today.sh` now carries on with the other papers, prints `FAILED: <paper>`, and exits 1 at the end.
- `events/seeds.json` still holds a Begin fair seed. The blocklist drops it on every run.

## Blocklist: no free fair or expo coverage (since 27 Oct 2026)

Fair coverage is a paid product now. No Yes Bro paper gives a fair organiser free coverage: Begin, educationfair.net (International Education Fairs India), Education Worldwide India, IDP fairs, QS tours, university fairs, study abroad expos, admission fairs and the like. A fair appears only with a confirmed paid deal.

- Rule (`blocklist.FAIR_RE`, `FAIR_DOMAINS`): an item is dropped when its main subject is an education, study abroad, university or admissions fair, expo or roadshow. Main subject means its title (headline, name, title) or its URL (domain or path). A passing mention in a summary is fine. Conferences, summits, webinars, hackathons, competitions, science fairs, book fairs, campus tours and the ordinary word fair ("fair pricing") are never blocked.
- Applies to stories, events, jobs, opps, memes, columns and interludes, the same paths as the Begin block. Build logs show `BLOCKED: Begin <n>` and `BLOCKED: fairs <n>`.
- Publish guard: any page that links a known fair organiser domain (`FAIR_DOMAINS`) fails and is not published.
- Paid partners: add them to `sponsors.json` as `{"fairs": [{"name": "Exact fair name", "domains": ["organiser.com"]}]}`. An allowlisted fair passes the fair rule and the domain guard. It is empty for now. Only Saurabh adds entries, once a paid deal is confirmed. Begin stays hard blocked in `blocklist.py` whatever sponsors.json says.
- The Higher Ed and Schools event intros no longer mention fairs.
