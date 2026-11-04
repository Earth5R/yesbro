# Yes Bro specialist editions

These are personalised spin offs of the Yes Bro Newspaper. They use the same newsprint builder and look, and their own sections, mastheads and price lines. The first run was Sunday 25 October 2026, covering roughly the previous 7 days of news. There is no politics in any edition.

## House voice rule (all papers and the landing page, from 25 Oct 2026)
- **Fun, not funny.** Yes Bro is the cool, post Gen Z alternative to traditional media and it makes reading fun. The wit is dry, smart and understated, a smirk and not a punchline. No slapstick, no meme speak, no trying too hard, no cringe.
- Deadpan, serious faced humour runs full on in everything we write around the news: absurd things said straight, grand language for trivial things, dry understatement, one line twists. Never explain the joke. No "lol" and no emoji punchlines.
- This covers section intros, the Jobs, Events, Tenders and Funding blurbs, empty state lines, menu microcopy, landing card mottos, footers, the FIELDWORK ads (still professional, no intern words) and the "Tell us" button.
- **News voice (from 26 Oct 2026, replaces the old strictly factual rule):** summaries get the TechCrunch deadpan. Accurate and sourced, but dry and knowing: quote the company's own grand claims straight, set them beside the plain facts, end where useful on one short dry observation. Humour comes from framing and selection only, never from invented facts, made up quotes or claims not in the source. Headlines stay factual and clear (wry is fine, misleading is not). Never mock victims, tragedies, deaths, illness, disasters, ethnic or religious groups or private lives, and leave those summaries plain. Politics stays neutral, dry about process at most. Healing stays kind and evidence-minded, Schools stays gentle. Full guide with the Ask Proxy reference passage and before and after examples: `VOICE.md`.
- Yes Bro Explains columns may carry a dry deadpan touch, but every fact stays accurate.
- The copy rules still apply: no em dashes, en dashes or semicolons in visible copy, never invent facts, Earth5R is never an NGO.
- **No counting in house copy (from 25 Oct 2026, owner feedback).** Copy that counts things reads as machine written. In mottos, ears, card blurbs, section intros, footers, ads, menus, buttons, the home screen note and column decks, never count our own things: no "thirteen papers", no "30 jobs", no "85 events", no "all 13 papers", no "seven sections". No section, menu or card counters either. Avoid the other obvious tells too: "X things, one Y, no Z" lines, tricolons and three item lists, "not X, but Y" constructions and overly neat parallel lines. Write the way a sharp human editor would, dry and deadpan. Real numbers inside news summaries, prices, dates, deadlines and the data in columns are fine. `build_html.py` and `build_landing.py` print a "HOUSE VOICE WARNING" line for any count they find in house copy. Fix it before publishing.

## Editions

| Edition | Masthead / apple title | Price line | Live URL |
|---|---|---|---|
| UX | Yes Bro UX / Yes Bro UX | Price: Free, no dark patterns | https://yesbrohq.com/ux/ |
| Architecture | Yes Bro Architecture / Yes Bro Arch | Price: Free, unlike your consultant's fee | https://yesbrohq.com/architecture/ |
| Schools (grades 9 to 12, IB, Cambridge, international boards) | Yes Bro Schools / Yes Bro Schools | Price: Free, unlike tuition | https://yesbrohq.com/schools/ |
| Sustainability | Yes Bro Sustainability | Price: Free, unlike a carbon offset | https://yesbrohq.com/sustainability/ |
| Startups | Yes Bro Startups | Price: Free, no term sheet required | https://yesbrohq.com/startups/ |
| Higher Ed | Yes Bro Higher Ed | Price: Free, unlike the application fee | https://yesbrohq.com/highered/ |
| Consulting | Yes Bro Consulting | Price: Free, not billed by the hour | https://yesbrohq.com/consulting/ |
| Health | Yes Bro Health | Price: Free, no prescription needed | https://yesbrohq.com/health/ |
| Marketing | Yes Bro Marketing | Price: Free, no influencer fee | https://yesbrohq.com/marketing/ |
| Finance | Yes Bro Finance | Price: Free, zero expense ratio | https://yesbrohq.com/finance/ |
| Aviation | Yes Bro Aviation | Price: Free, no baggage fee | https://yesbrohq.com/aviation/ |
| Business (from 25 Oct 2026) | Yes Bro Business | Price: Free, unlike your CA | https://yesbrohq.com/business/ |
| Healing (from 26 Oct 2026) | Yes Bro Healing | Price: Free, unlike the retreat | https://yesbrohq.com/healing/ |
| AI (from 26 Oct 2026) | Yes Bro AI | Price: Free, unlike the compute | https://yesbrohq.com/ai/ |

With the main paper (https://yesbrohq.com/daily/, "Price: Free, unlike your opinions") that makes 11 papers. The daily editions run covers all 10 field editions above (UX, Architecture, Schools and the 8 added on 25 Oct 2026). Story files use these keys: ux, arch, schools, sustainability, startups, highered, consulting, health, marketing, finance, aviation. Folders are the same except arch publishes to `architecture/`.

Every masthead carries a small "Yes Bro Newspaper" family line above it.

### Sections (in order)
- **UX:** UX and Product Design, UI and Visual Design, AI and Design, Design Tools and Platforms, Design in India, Design Startups and Funding, Careers and Ideas.
- **Architecture:** Sustainable and Green Architecture, Architecture India, Global Architecture and Design, Materials and Building Tech, Urbanism and Climate, Architecture Startups and Innovation, Education and Ideas.
- **Schools:** IB and Cambridge Board News, University Admissions, Scholarships and Opportunities, Study Abroad and Visas, Teaching and Pedagogy, Education India, Ideas and Careers.
- **Sustainability:** ESG and Disclosure, Carbon Markets and Climate Finance, Climate Policy, Circular Economy and Waste, Corporate Sustainability and Energy Transition.
- **Startups:** India Funding, Global Funding, VC and Investors, IPOs, Exits and Results, Founders and Ideas.
- **Higher Ed:** Admissions and Entrance Exams, Study Abroad and Visas, Scholarships and Opportunities, Universities and Rankings, Policy and Campus Life.
- **Consulting:** The Big Firms, Research and Insights, Deals and Moves, India Policy and Business, Careers and Campus.
- **Health:** Medicine and Research, Public Health India, Global Public Health, Health Tech, Wellness and Mental Health.
- **Marketing:** Brands and Campaigns, Advertising and Agencies, Social Media and Creators, Platforms and Ad Tech, Martech and AI.
- **Finance:** Indian Markets, Global Markets, Banking and Regulation, Fintech and Payments, Personal Money.
- **Aviation:** India Airlines and Airports, Global Airlines, Aircraft Orders and Industry, Safety and Regulation, Pilots and Training. Jobs list airline cadet programmes first (tag "Cadet"), then other roles.

Daily news window for the 8 newer editions is the last 2 to 3 days. On thin days a section may run 5 to 9 stories rather than pad. Paywalled pages (FT, WSJ, FlightGlobal) may be used only from their public standfirst or RSS teaser, and the summary says so when the full piece is for subscribers.

## Story rules
- Aim for 10 to 20 stories per section. Go lower only when news is thin, and never pad.
- Each story has a headline, our own 30 to 50 word summary in the house news voice (VOICE.md), and the original article URL. Decode Google News links before using them.
- Check that every URL loads this run. A 403 bot block is acceptable if the RSS teaser carries enough facts.
- Never invent facts. Write each summary only from the fetched article text or the RSS teaser.
- No duplicates within an edition. The same story may appear in two editions (for example, Mach9 ran in both UX and Arch).
- No em dashes, en dashes or semicolons in visible copy.
- Put the strongest stories first, because the first 5 in each section get photos and full cards.
- Drop anything whose published date is older than about 10 days. This run dropped items with pub dates in March, June and September, plus a 2024 Elets article.

## Sources that worked
- **UX:**
  - nngroup.com, uxdesign.cc (UX Collective) and uxplanet.org. The last two block bots with 403, but their RSS teasers are usable.
  - smashingmagazine.com, ixdf.org, figma.com/blog, creativebloq.com, creativeboom.com, itsnicethat.com, designweek.co.uk, abduzeedo.com.
  - fastcompany.com, 9to5mac.com, macrumors.com, techcrunch.com, stirworld.com, monocle.com, campaignindia.in, saastr.com, inc42.com, posthog.
- **Architecture:**
  - archdaily.com, dezeen.com, designboom.com, parametric-architecture.com, archinect.com, archpaper.com, architecturetoday.co.uk, architecturaldigest.in, architecture.live, architectureau.com.
  - metropolismag.com, woodcentral.com.au, aecmag.com, greenbuildingadvisor.com, globalconstructionreview.com, projectscot.com.
  - constructiondive.com and smartcitiesdive.com (both 403, teaser only).
  - newindianexpress.com, deccanherald.com, tribune.com.pk, dawn, iol.co.za.
- **Schools:**
  - thepienews.com, monitor.icef.com, timeshighereducation.com, insidehighered.com, edsurge.com, edweek.org, educationnext.org, thejournal.com, k12dive.com (403, teaser only), theconversation.com.
  - thehindu.com/education, indianexpress.com/education, edexlive.com, dtnext.in, ndtv education, bweducation.com, irishtimes.com.
- **Newer editions (25 Oct 2026):** the shared gather in `editions2/` (`feeds_new.py`, `gather_new.py`, fetch cache `fetched_new.json`) used trade press plus Google News RSS with `when:3d`. Copy lives in `editions2/copy/copy_<ed>.py`, validated and written by `editions2/make_stories2.py` to `stories_<ed>_YYYY-MM-DD.json`.
- Google News RSS search with `when:7d` (in `editions/feeds_ed.py` and `feeds2.py`) filled the gaps left by dead feeds.

## Files (in /workspace/yesbro)
- **Gathering:** `editions/feeds_ed.py`, `gather_ed.py`, `feeds2.py` and `gather2_ed.py` produce `items*.json`, which are merged into `all.json`.
- **Picks:** `editions/picks.py`, then `fetch_picks.py` (decodes Google News links and fetches the pages), then `fetched.json`. `extract.py` adds trafilatura text.
- **Copy:** `editions/copy_ux.py`, `copy_arch.py` and `copy_schools.py` hold (id, headline, summary) per section. `editions/make_stories.py` validates word counts, banned characters, duplicates, Google News URLs and stale pub dates, then writes `stories_{ux,arch,schools}_2026-10-25.json`.
- **Images:**
  - `python3 fetch_images.py stories_X.json stories_X.html.json --mode html --width 560 --quality 50`
  - plus the canvas thumbnail fallback: `python3 fetch_images.py stories_X.json stories_X.out.json`
- **Configs:** `editions/config/{ux,arch,schools}.json` set the sections, title, masthead, family line, motto, ears, edition label, price, footer, head_extra (home screen tags) and ad_html/ad_after.
- **Jobs (every day, before the build):** `python3 jobs.py X --date YYYY-MM-DD` for X = ux, arch, schools. It writes `jobs_X_YYYY-MM-DD.json` (see the Jobs section below).
- **Build:** `python3 build_html.py stories_X.html.json "Sunday 25 October 2026" yesbro_X_2026-10-25.html --fallback stories_X.out.json --config editions/config/X.json --jobs jobs_X_2026-10-25.json`
  - `--jobs` adds the Jobs section as the last section and a "Jobs" link at the end of the section nav. Without `--jobs` the build is byte for byte unchanged (verified with cmp on 25 Oct 2026).
  - The `--config` flag is optional.
  - Every build now includes the slide-out section menu (see README.md, "Section menu"). In the editions, Jobs is pinned and highlighted at the top of the menu, and the FIELDWORK house ad gets `id="fieldwork"` and a menu item. The byte for byte comparisons above predate the menu.
- **Source names:** `sources.py` NAMES now covers all the new hosts. A backup is at `sources.py.bak`.

## Publish (repo /workspace/yesbro-site, Earth5R/yesbro, GitHub Pages)
1. Run `python3 publish.py <key> yesbro_<key>_YYYY-MM-DD.html YYYY-MM-DD` for each edition. It writes `<folder>/index.html` and `<folder>/archive/YYYY-MM-DD.html` (head paths rewritten to `../manifest.json` and `../../icon-512.png`, canonical and og:url pointed at the archive URL) and refreshes `sitemap.xml` and `robots.txt`. Add `sitemap.xml robots.txt` to the commit.
2. Each edition has its own `manifest.json`: name, short_name, `start_url "./"`, and icon `../icon-512.png`.
3. Home screen tags go in through `head_extra`: apple-mobile-web-app-capable, apple-mobile-web-app-title, theme-color #f3ead6, manifest, and apple-touch-icon / icon pointing at `../icon-512.png`.
4. Folders for the newer editions: `sustainability/`, `startups/`, `highered/`, `consulting/`, `health/`, `marketing/`, `finance/`, `aviation/`, each with `index.html`, `manifest.json` and `archive/`.
5. Edition publishes never touch the root `index.html`, root `archive/`, `daily/` or `CNAME`. Do not run `build_landing.py` from the editions routine. The 8 am main paper run refreshes the landing page, and it picks up the newest edition stories files from the 6:30 run. The main paper lives at `daily/` (see README.md). Menu "Back to the front page" and the masthead link to https://yesbrohq.com/. (Exception on 25 Oct 2026: all four papers were rebuilt together to add the section menu.)
6. Commit once for all editions, push to main, then curl each live URL for 200 and the day's date line.
7. The landing page (`build_landing.py`, EDITIONS list) has 12 cards in this order: Daily, UX, Architecture, Schools, Sustainability, Startups, Higher Ed, Consulting, Health, Marketing, Finance, Aviation. Three columns from 1100px, two from 700px, one on phones with a shorter photo. Photos and credits are in `img/landing/` and `img/landing/CREDITS.md`.

## Screenshots
Menu check: `python3 menushot.py https://earth5r.github.io/yesbro/ux/ preview_menu_ux.png 1` (writes the open-menu shot and a `_jumped` shot after tapping Jobs).
Run `/tmp/shot.py` (Playwright, `/usr/bin/google-chrome`, 390x844 mobile, iPhone UA). It writes `preview_ux.png`, `preview_arch.png` and `preview_schools.png`.
For the Jobs section run `python3 /tmp/shotjobs.py https://earth5r.github.io/yesbro /workspace/yesbro`. It writes `preview_jobs_ux.png`, `preview_jobs_arch.png` and `preview_jobs_schools.png`.

## FIELDWORK house ad
- **Format:** one boxed, classic newspaper ad per edition (`<aside class="housead">`). It goes in through `ad_html` in the config and is placed after section 3 (`ad_after: 3`). It reads "Advertisement", then the blackletter "Fieldwork", a headline, one or two lines of copy, and a "Learn more at earth5r.org" button linking to https://earth5r.org/fieldwork/.
- **Facts used, all verified on earth5r.org on 25 Oct 2026:**
  - FIELDWORK takes students out of the classroom into their own neighbourhoods. They study real problems and work alongside the community, and every piece of their work is verified.
  - It is a mentored fellowship open to school and university students. A mentor guides each step and checks the work.
  - Fellows work on a live Earth5R project, online with field work near where they live, and join research conversations with professors at MIT, Oxford, Cambridge, LSE and others.
  - Earth5R runs climate programmes with communities in more than 150 Indian cities, including river clean ups, waste and circular economy work.
- **Rules:** never call Earth5R an NGO, never invent facts, and no em dashes or semicolons.
- **No-intern rule (permanent, from 25 Oct 2026):** never write intern, interns, internship or internships in our own copy (columns, configs, section names, jobs intros, menu labels, ad copy, landing, meta and SEO tags). Readers are professionals. Earth5R's offer is the FIELDWORK fellowship: hands-on fieldwork with real people, real conversations, real users and real research. Link https://earth5r.org/fieldwork/ (or another verified earth5r.org page that is not an internship page), never an earth5r.org internship URL. Internship listings are never shown (see below). Our labels say "Jobs" or "Jobs and student opportunities". Earth5R is never an NGO. Enforced by `columns.py check` and `columns.py publish`, `build_landing.py` and the config check in `build_html.py` (all fail on a hit).
- **Ad copy by edition:**
  - **UX:** "Your next user interview is down the street." The copy is about real-world research with communities, and meeting people first, then designing.
  - **Arch:** "See how people really use the city." The copy covers on-ground work on waste, water and climate with communities, and studying the street before you draw it.
  - **Schools:** "A real project for your university application." The copy covers the mentored fellowship, a live project near home, research conversations, and a verified record of work.
- **Main paper:** the ad was not added. Adding it would mean rebuilding the main daily file and its published copy, which the brief said not to touch, so it was not trivial. To add it later, pass a config with only `ad_html` and `ad_after` to the main build.

## Jobs section (daily, all ten field editions)
- **No internship listings ever, conflict of interest with FIELDWORK (final, 25 Oct 2026):** no internship listings anywhere on Yes Bro, Higher Ed and Schools included. Jobs sections list real jobs only: full-time, part-time, contract, graduate and entry-level jobs, education-sector roles and airline cadet programmes. `jobs.py` enforces it with a hard filter (`NO_INTERN`, `is_internship`) on title, employment type (Lever commitment, Ashby and Himalayas employmentType, SmartRecruiters typeOfEmployment), org, note and URL, applied to every source and every seed in main(), with an assert before the file is written. Never add internship seeds or internship-focused sources or queries. FIELDWORK is how readers get job-ready and stand out.
- **No-intern rule (permanent, from 25 Oct 2026):** never write intern, interns, internship or internships in our own copy (columns, configs, section names, jobs intros, menu labels, ad copy, landing, meta and SEO tags). Readers are professionals. Earth5R's offer is the FIELDWORK fellowship: hands-on fieldwork with real people, real conversations, real users and real research. Link https://earth5r.org/fieldwork/ (or another verified earth5r.org page that is not an internship page), never an earth5r.org internship URL. Internship listings are never shown (see below). Our labels say "Jobs" or "Jobs and student opportunities". Earth5R is never an NGO. Enforced by `columns.py check` and `columns.py publish`, `build_landing.py` and the config check in `build_html.py` (all fail on a hit).
- **Daily routine:** after the stories are ready, run `python3 jobs.py X --date YYYY-MM-DD` for every edition key (ux, arch, schools, sustainability, startups, highered, consulting, health, marketing, finance, aviation). They can run in parallel because the same day ATS responses are cached on disk in `jobs/cache/YYYY-MM-DD/`. Then build each edition with `--jobs jobs_X_YYYY-MM-DD.json` and publish as usual. Jobs are part of every edition every day.
- **What it lists:** real, open roles only, India first, then Global, then Remote (Schools calls the last group "Remote and Online"). Up to 30 per edition (caps: India 14, Global 8, Remote 8, with spare room spread to groups that have more). At most 3 per organisation per group. Each listing shows title, organisation, location, posting date or closing date when known, a Teacher or Student tag in Schools, an Apply link to the original posting, and the source.
- **Rules in the script:** postings older than 30 days or past their closing date are dropped. Every link is checked (status under 400) and dead ones are dropped. Em dashes, en dashes and semicolons are replaced in all copy.
- **Repeats:** `jobs/jobs_seen.json` records the first day each posting was seen. Still-open postings stay listed. A small "New" marker appears only on postings first seen that day, and is hidden when every listing is new (first run).
- **Sources (public APIs and feeds only, no LinkedIn, Naukri, Indeed, Glassdoor or logins):**
  - **UX:** Greenhouse, Lever, Ashby and SmartRecruiters public job APIs for product companies (Razorpay, PhonePe, Swiggy, Bosch, ServiceNow, Mindtickle, Toast, Figma, Airbnb, OpenAI and others), Workday public job search (Adobe, Autodesk, Salesforce, PayPal, Mastercard, Cisco), We Work Remotely RSS, Himalayas API, Dribbble jobs RSS, Remotive and Working Nomads.
  - **Arch:** Archinect jobs feed and remote pages, Workday (AtkinsRealis, Surbana Jurong, JLL), RINA career site, AECOM and Stantec careers RSS, Colliers SmartRecruiters, Himalayas.
  - **Schools:** ISP schools Workday, Nord Anglia career site search (Oakridge and others), Woodstock School HireHive API, Kodaikanal International School and American School of Bombay career pages, and official student programme pages (Earth Prize, Non-Trivial, Technovation, Conrad Challenge, Yale Young Global Scholars, Aspirnaut and more). A student programme is listed only when its own page shows a deadline in the next 150 days.
- **Seeds:** `jobs/seeds_{ux,arch,schools}.json` hold direct posting URLs found with web search (fields: title, org, location, url, optional tag, note, posted, deadline, source). The script re-checks each one every run and drops it if the page fails, says closed, or has no closing date ahead and no posting date within 30 days. Refresh the seeds every few days with a web search for new India roles (green building, IGBC, GRIHA, architecture faculty, IB and Cambridge teachers). Do not seed pages that copy LinkedIn listings.
- **Known gaps (25 Oct 2026):** Himalayas job pages show a Cloudflare check to scripts, so Himalayas links are kept on the strength of the API's expiry date and ranked below verified sources. Failed or skipped: Dezeen Jobs and Behance (403), Authentic Jobs (no job feed), TES (no feed), ibo.org jobs (403), TeachAway (loads by script), GEMS (no feed), Nord Anglia RSS (403, search page works), Gensler feed (old listings), Jacobs careers (empty to scripts), Workday for AECOM, Jacobs, Arcadis, WSP, Mott MacDonald, Cognita (site names not found), PROMYS India (SSL error), and several programme pages with no deadline showing yet.
- **FIELDWORK jobs box:** a small boxed line above the Jobs section (`jobs_ad_html` in each config), tailored per edition, linking to https://earth5r.org/fieldwork/. UX: research on your portfolio that hiring managers can check. Arch: a live Earth5R project near home on waste, water and climate for students between offers. Schools: for students, and for teachers to share. Same facts and rules as the house ad above.

### Jobs changes on 25 Oct 2026
- Seeds may set `"allow_blocked": true`. The seed is then kept on a 401 or 403 if its deadline is today or later. Used for the IndiGo cadet page on garudaaviation.in, which returns 403 to scripts but was checked by hand.
- The closed check strips `<script>` blocks first, so Next.js pages that embed a 404 template (Skystudy cadet pages) are no longer flagged as closed.
- Seeds tagged "Cadet" sort first within their region, so cadet programmes lead the Aviation jobs.
- Closed at the time of the first run: IndiGo cadet batch 7 (closed 20 Oct), Air India cadet (closed 15 Sep), Akasa first intake (closed 24 Jun). Recheck the seeds for new batches every few days.

## FIELDWORK ad copy for the newer editions
- **Sustainability:** "Your ESG report needs ground truth."
- **Startups:** "Find the problem before the pitch deck."
- **Higher Ed:** "Your application needs more than marks." Covers the mentored fellowship, a live Earth5R project online and in the field near home, research conversations with professors at MIT, Oxford, Cambridge, LSE and others, and a verified record of work for university applications.
- **Consulting:** "Real fieldwork beats another framework."
- **Health:** "Public health starts on your street."
- **Marketing:** "Know your audience. Literally."
- **Finance:** "Some returns do not show up in a portfolio."
- **Aviation:** "Ground school for the real world."
Same facts and rules as above. Never call Earth5R an NGO.

## Efficiency notes for the daily 11 paper run
1. Gather once. One shared RSS and Google News pass for all field editions, written to a single items file, then split by edition. This avoids fetching the same wire stories eight times.
2. Share the fetch cache. Reuse `fetched_new.json` (decoded Google News URL, status, text) across editions and across the day, so a story used in two editions is fetched once.
3. Run jobs in parallel. `jobs.py` for all ten keys at once. The ATS disk cache in `jobs/cache/YYYY-MM-DD/` means shared employers are called once.
4. Run `fetch_images.py` in parallel, one background process per edition (html mode and the .out fallback), and wait on done markers.
5. Build and publish in one loop over all keys, lint visible copy (em dash, en dash, semicolon, NGO) in the same loop, then one commit and one push. The Pages build then runs once.
6. Keep the copy files small: pick the strongest 10 to 14 per section first, write summaries, and validate with `make_stories2.py` before the image step, so images are only fetched for stories that ship.
7. On thin days write fewer stories rather than widen the window past 3 days.

## Yes Bro Explains columns and SEO (since 25 Oct 2026)
- Every edition build now shows the "Yes Bro Explains" box after section 1 when `columns/<key>/` has a column from the last 7 days. Nothing extra to do in the editions routine, the box appears on its own. See README.md, "Yes Bro Explains".
- Columns are written by the separate "Yes Bro Columns" routine at 4:30 IST, before the 5:30 field editions run and the 8:00 daily run, so both builds pick up the new column.
- Schedule (twice a week per paper, 3 or 4 days apart, at most 4 columns a morning):
  - Mon: Daily, Finance, Startups, Aviation
  - Tue: UX, Schools, Higher Ed, Business
  - Wed: Architecture, Sustainability, Consulting, Health, AI (proposed)
  - Thu: Daily, Finance, Startups, Marketing, Healing (proposed)
  - Fri: UX, Schools, Higher Ed, Aviation
  - Sat: Architecture, Sustainability, Consulting, Business
  - Sun: Health, Marketing, Healing, AI (proposed)
  The 7 day box window means every paper always shows a column under 4 days old.
- SEO keys live in each config (`key`, `url`, `seo_title`, `seo_desc`). Keep titles keyword led and unique, descriptions 150 to 175 characters with no banned characters.
- The editions routine still never runs `build_landing.py`, but `publish.py` refreshes `sitemap.xml` and `robots.txt`, so commit those two files with the editions.

## Business paper, Events, Tenders and Funding, pills and home screen (since 25 Oct 2026)
- **Yes Bro Business** (`business`, folder `business/`, config `editions/config/business.json`). Page order (owner, 25 Oct 2026, business news must lead, tenders never lead): Indian Business (lead story and photo), Stock Market, Deals and M&A, Business Basics, Funding, Government Tenders and Releases, Events, Jobs. Set by `sections` and `top_blocks` in the config. The slide-out menu pins Jobs, Events, Funding, Tenders in that order through `menu_pins`. Story files are sorted in section order so the landing card's top story is Indian Business news. News copy lives in `editions3/copy/copy_business.py` and is validated against `editions3/fetched_biz.json` like the other papers (30 to 50 words, no banned characters, no duplicates, no Google News URLs). Columns: Tuesday and Saturday.
- **opps.py** (Business only): `python3 opps.py --date YYYY-MM-DD` writes `opps_business_YYYY-MM-DD.json` with tenders (Google News `when:3d`, decoded and link checked), government releases (PIB English RSS, "Posted On" within 3 days) and funding calls (`opps/funding.json`, kept only while the official page loads, shows its check strings and the deadline date, and the deadline is ahead). GeM and CPPP are not reachable from the box, so tenders come from news plus PIB. Never invent tenders, amounts or dates.
- **events.py** (all 15 papers): `python3 events.py --date YYYY-MM-DD` writes `events_<key>_YYYY-MM-DD.json`. Seeds in `events/seeds.json` are kept only when the official page loads and shows the start date, the event is ahead and within 90 days. Luma public feeds (Bengaluru, Mumbai, New Delhi, tech, ai, climate, arts) add up to 6 meetups per paper by name keywords. confs.tech adds UX conferences. Each event has a region (India, World, Online). Build with `--events events_<key>_D.json`. The section is "Events and Conferences" (id `events`), pinned in the menu after Jobs.
- **Jobs:** `python3 jobs.py business --date D` (Workday PwC, Accenture, Unilever, Mastercard, Citi, S&P Global, Gartner plus the India Greenhouse and Lever boards, EY India and Himalayas). Run jobs.py papers one at a time, they share `jobs_seen.json`.
- **All Yes Bro papers pills:** every paper shows a pill at the top right and a larger pill at the bottom ("Other papers. Equally free."), both linking https://yesbrohq.com/. Config keys `pill_top` and `pill_bottom` override the labels.
- **Add Yes Bro to your home screen:** a collapsible note (id `homescreen`) on every paper and the landing page, with iPhone (Safari, Share, Add to Home Screen) and Android (Chrome, three-dot menu, Add to Home screen or Install app) steps and an Install button that appears only when the browser fires `beforeinstallprompt`. `build_html.py` writes the standard home screen head tags for any config with a `url`. `pwa.py` writes `<folder>/manifest.json` for all papers (name "Yes Bro <Field>", id, start_url and scope `/<folder>/`, standalone, `/icon-512.png`). `rebuild_today.sh` runs it last.
- **Full rebuild:** `bash rebuild_today.sh YYYY-MM-DD "Sunday 25 October 2026"` builds all 15 papers (Daily, the field papers, Healing and AI) with jobs, events and (Business) opps, publishes them, publishes columns, the landing page and the manifests. Never touch CNAME or the root archive folder. Pull with rebase before committing.

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
## Meme of the day (all papers, since 26 Oct 2026)
- Every paper (config `"meme": true`, set in all of `editions/config/*.json`, Daily included) carries a **Meme of the day** box after its second news section, built by `memes.py` and called from `build_html.py`. The landing page shows a small one from Yes Bro Daily after the paper cards (`build_landing.py`, `landing_meme`). Real text in HTML and CSS, in the newsprint style. No images, no hotlinks, no famous meme templates or photos.
- Formats: `nobody` (Nobody: / Absolutely nobody: / Someone: line, optional reaction), `expect` (Expectation and Reality panels), `chart` (a joke bar chart of two bars), `classic` (top and bottom caption on a dark halftone panel). Each meme references a real story in that day's edition and links to it ("From today's paper").
- **Daily worker step (5:30 am Field Editions and 8 am Daily):** after the copy is final, write `memes/<key>_<YYYY-MM-DD>.json` for each paper (key `daily` for Daily) by hand, then build. Format: `{"url": "<exact story url from stories_<key>_D.html.json>", "format": "nobody|expect|chart|classic", ...}` with `lines` and `after`, or `expect` and `reality`, or `title` and `bars` ([label, percent] pairs), or `top` and `bottom`. Vary formats across papers and from yesterday. Voice is "Fun, not funny": deadpan, dry, grand language for small things. Joke about the reader, the desk or the situation, never about the people in the story.
- **Never:** politics, politicians, parties, elections, governments' political actions, religion or festivals, communal or geopolitical conflict, named communities or ethnic groups, death, illness, disasters, accidents, crime or victims, layoffs or closures, real private individuals. Healing memes stay kind, never touch mental health struggles and never suggest a therapy, supplement or diet cures anything.
- **Validator and fallback (memes.py):** a hand file is used only if its story is in today's edition, passes the story filters (POLITICAL, SENSITIVE and COMMUNITY keyword lists plus SKIP_SECTIONS for politics, policy, regulation, safety, public health, mental health and alternative therapy sections) and its own words pass `validate()` (no em or en dashes or semicolons, no intern words, Earth5R never an NGO, no FIELDWORK or Earth5R on Healing, no "not X but Y", no tricolons, no counting, no political, sensitive or unkind words). Otherwise a template caption is built on a safe story picked from the top of the sections, with the format rotating by paper and by day. If no story is safe, a house meme about reading the paper. A meme can never fail a build or ship an empty box. The rejected file and reason are printed in `/tmp/b_<key>.log` as `meme: ... rejected`.

## Yes Bro Fashion (29 Oct 2026)

- **Yes Bro Fashion** (`fashion`, folder `fashion/`, config `editions/config/fashion.json`, https://yesbrohq.com/fashion/, "Price: Free, unlike the designer label"). The 17th paper. Sections: Fashion News India, Global Fashion, Jewellery, Accessories, Textiles and Craft, Sustainable and Circular Fashion, Fashion Industry, Fashion Tech and Retail, Opportunities, plus Research and Development, Talks, Events and Conferences, and Jobs. India first then global. Jewellery covers gems, gold, diamonds, lab-grown and Indian industry (GJEPC, Titan/Tanishq). Opportunities: real open calls, grants, design competitions and scholarships only, never internships. Trade fairs (IIJS, Vicenzaoro, JCK, Premiere Vision and the like) are paid listings only. Fashion weeks and runway shows are fine.
- **Sources:** `editions4/feeds_fashion.py` into `run29/feeds_all.py`. Gather with `run29/gather_ed_append.py fashion`. Picks `run29/picks_fashion.py`, copy `run29/copy/copy_fashion.py`. Jobs via `jobs.py fashion`, events/research/talks via the shared scripts with key fashion. Meme `memes/fashion_D.json`. Landing image `img/landing/fashion.webp`. BRAND_W Fashion = 3.80. Rebuild_today.sh includes fashion.

## Yes Bro Real Estate (31 Oct 2026)

- **Yes Bro Real Estate** (`realestate`, folder `realestate/`, config `editions/config/realestate.json`, https://yesbrohq.com/realestate/, "Price: Free, no brokerage"). The 18th paper. Sections: India Real Estate, Residential and Housing, Commercial, Offices and Retail, Industrial, Warehousing and Data Centres, Land, Infrastructure and Smart Cities, Policy, RERA and Regulation, Finance, REITs, Deals and Funding, PropTech, Construction and Materials, Green Buildings and Sustainability, Global Real Estate, plus Research and Development, Talks, Events and Conferences, and Jobs. India first then global. Sustainability is one section among many. Conferences, events and research are a day-one edge. Property expos and housing fairs are paid listings only. Never internships.
- **Sources:** `editions4/feeds_realestate.py` into `run31/feeds_all.py`. Gather with `run31/gather_ed_append.py realestate`. Picks `run31/picks_realestate.py`, copy `run31/copy/copy_realestate.py`. Jobs via `jobs.py realestate`, events/research/talks via the shared scripts with key realestate. Meme `memes/realestate_D.json`. Landing image `img/landing/realestate.webp`. BRAND_W Real Estate = 5.50. Rebuild_today.sh includes realestate.

## Yes Bro Auto (31 Oct 2026)

- **Yes Bro Auto** (`auto`, folder `auto/`, config `editions/config/auto.json`, https://yesbrohq.com/auto/, "Price: Free, no on-road charges"). The 19th paper. Sections: India Auto, Cars and SUVs, Two-Wheelers and Three-Wheelers, Electric Vehicles and Charging, Commercial Vehicles, Tractors and Off-Highway, Components, Tyres and Supply Chain, Sales, Dealers and Retail, Finance, Insurance and Deals, Auto Tech, Software and Autonomy, Policy and Regulation, Motorsport, Sustainability and Clean Mobility, Global Auto, plus Research and Development, Talks, Events and Conferences, and Jobs. India first then global. Sustainability is one section among many. Conferences, events and research are a day-one edge. Auto Expo, motor shows and trade fairs are paid listings only. Never internships.
- **Sources:** `editions4/feeds_auto.py` into `run31/feeds_all.py`. Gather with `run31/gather_ed_append.py auto`. Picks `run31/picks_auto.py`, copy `run31/copy/copy_auto.py`. Jobs via `jobs.py auto`, events/research/talks with key auto. Meme `memes/auto_D.json`. Landing image `img/landing/auto.webp`. BRAND_W Auto = 2.20. Rebuild_today.sh includes auto.
