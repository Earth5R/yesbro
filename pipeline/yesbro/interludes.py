"""Interludes: standalone deadpan punchline strips between news sections (imported by build_html.py).

How it works
- POOLS holds the lines for each paper key. Lines rotate by date: each day takes the next block of lines,
  and a paper shows len(pool) // 7 strips a day (at least 1), so no line repeats within a week.
  Add lines to a pool to show more strips a day without repeats.
- Optional hand written override for one day: interludes/<key>_<YYYY-MM-DD>.json, a JSON list of strings.
  Override lines are validated with the same rules and used before the pool.
- Placement: only after a news section, spread evenly down the page. A slot is skipped when the section
  before or after it is political or policy, when the stories next to it (end of the section above,
  featured top of the section below) touch tragedy, death, illness, disaster or victims, and where the meme,
  the Explains box or a house ad already sits.
- Copy rules (validate()): no dashes, no semicolons, no "not X but Y", no intern words, no lol or emoji,
  no counting our own things, and no FIELDWORK or Earth5R anywhere (Healing guard). Tricolons and
  truthfulness are checked by a human when lines are added. Healing and Schools stay gentle, Health
  never jokes about illness.
"""
import datetime, html, json, os, re

DARK = "#4a2a12"

POOLS = {
"daily": [
    "If this news felt familiar, that is because it happened last week too.",
    "Everyone in this section has a press team. You have this paper.",
    "Somewhere, an expert is being quoted as saying it is too early to say.",
    "Officials are monitoring the situation. The situation is monitoring them back.",
    "A committee has been formed to look into the committee.",
    "This breaking news will be replaced by next week's breaking news.",
    "Sources familiar with the matter remain very familiar with it.",
    "Read the headline twice. You will feel twice as informed.",
    "Somewhere, a group chat has already reached a verdict on this.",
    "The press release called it historic. Most press releases do.",
    "Experts agree, eventually, after the event.",
    "The world kept turning overnight. Nobody asked it to pause.",
    "The forecast said sunny. The forecast has said many things.",
    "Everything in this section was announced with great confidence.",
],
"business": [
    "Record profits were announced. Your salary has been informed.",
    "The CEO called it a challenging quarter from a very comfortable chair.",
    "Synergies have been identified. Nobody has seen them yet.",
    "Guidance was maintained. So was the bonus.",
    "The company is optimistic about the second half. It usually is.",
    "Analysts were surprised. Analysts are surprised every quarter.",
    "The merger will create value, according to the people paid to merge it.",
    "Cost discipline has been announced. The offsite is still on.",
    "The board has full confidence. The board said so itself.",
    "Shareholders were rewarded. Everyone else was thanked.",
    "The stock reacted. The fundamentals are still thinking about it.",
    "A strategic review is underway. Nobody has been told what it is reviewing.",
    "The quarter ended. The jargon did not.",
    "Every annual report now has a photo of a smiling plant.",
],
"ux": [
    "Somewhere, a dark pattern is winning an award.",
    "The cookie banner has been redesigned. It is still lying to you.",
    "The redesign tested well with the people who designed it.",
    "Every app now has an AI button. Few of them know why.",
    "Onboarding has been simplified into a carousel of tips you will skip.",
    "Accessibility was added to the roadmap. The roadmap is very long.",
    "Users said they loved it. Users also said they read the terms.",
    "Dark mode has shipped. The problems are now harder to see.",
    "The unsubscribe link is still there, behind a feeling of guilt.",
    "The design system has a component for everything except agreement.",
    "A new font was chosen after a long and emotional meeting.",
    "Rounded corners are back. They never left.",
    "The button says Continue. It means Pay.",
    "Every redesign moves the settings somewhere new, which is consistency of a kind.",
],
"arch": [
    "Another glass tower has been called sustainable by the people selling it.",
    "The render had trees. The building has a car park.",
    "The facade is iconic. The lift queue will become iconic too.",
    "Natural light was promised. The brochure got most of it.",
    "The architect calls it a dialogue with the context. The neighbours call it big.",
    "A pavilion was built for one season and will be photographed forever.",
    "Concrete remains popular with everyone except the atmosphere.",
    "Mixed use means the coffee shop opens before the offices fill.",
    "Every masterplan has a green spine. Few of them have shade.",
    "The adaptive reuse was so successful the rent adapted too.",
    "The award jury loved it. The jury does not live there.",
    "Biophilic design means one plant, carefully lit.",
    "Somewhere, a client has asked for something like Bilbao, only cheaper.",
    "The model was beautiful. Models usually are.",
],
"schools": [
    "The syllabus has changed again. Your textbook has not heard.",
    "Exams are coming. So is tea, if anyone is asking.",
    "Your homework is safe here. This paper will not eat it.",
    "Teachers read the news too, usually between corrections.",
    "The timetable has a free period. It will be found and filled.",
    "Study abroad brochures always show sunshine. Pack a jumper anyway.",
    "Revision notes work best when written before the night before.",
    "The deadline is closer than it appears.",
    "Somewhere, a teacher is still waiting for the class to settle.",
    "Group projects remain excellent training for adult life.",
    "The school bell has never once been on your side.",
    "Scholarships reward effort. Forms reward patience.",
    "Remember to drink water. The exam board will not remind you.",
    "Every great essay began as a blank page and mild panic.",
],
"sustainability": [
    "Another net zero pledge has been made, conveniently far away.",
    "The report was printed on recycled paper. The targets were recycled too.",
    "Carbon neutral, after offsets, after footnotes.",
    "The ESG rating went up. Nobody is sure what was measured.",
    "A tree was planted for the press photo. It is doing its best.",
    "Green bonds are booming. The planet would like to see the receipts.",
    "The transition plan is ambitious, mostly in the later years.",
    "Every company now has a sustainability officer. The thermostat has not been told.",
    "Scope 3 emissions remain someone else's problem, by definition.",
    "The packaging is now compostable, in a facility near nobody.",
    "The disclosure is complete. The emissions are also complete.",
    "Greenwashing has been made harder. Marketing has been informed.",
    "Sustainability week has ended. The air conditioning resumes.",
    "The climate summit ended with an agreement to meet again.",
],
"startups": [
    "Another founder has quit a cushy job to disrupt the industry that hired him.",
    "Profitability remains on the roadmap, right after the next round.",
    "The startup is pivoting. Last month it was pivoting the other way.",
    "The valuation doubled. So did the burn.",
    "Stealth mode ended with a press release.",
    "The pitch deck had a slide for everything except revenue.",
    "The company is building the Uber of something that did not need an Uber.",
    "Founder mode has been activated. HR has been deactivated.",
    "Every startup is AI first now. Revenue remains second.",
    "The investors are long term. Their patience is quarterly.",
    "Unicorn status achieved. Unit economics still pending.",
    "The team is a family, until the next restructuring.",
    "Hustle culture works, according to people who sell courses on it.",
    "Another newsletter has declared the end of the funding winter.",
],
"highered": [
    "Every university is world class, according to its own website.",
    "Rankings were released. Every university won something.",
    "The campus tour featured the one renovated building.",
    "The acceptance rate fell. The application fee did not.",
    "Office hours exist. Students who use them are rare and powerful.",
    "The prospectus has never once shown a queue.",
    "A new AI degree has launched. The old syllabus has a new cover.",
    "The scholarship is generous. The form is a quest.",
    "Study abroad means learning a new language, mostly the word deposit.",
    "The professor is on sabbatical. The reading list is not.",
    "The thesis will be finished next month, as it has been since spring.",
    "The library is open late. The coffee machine has other plans.",
    "Tuition went up. The brochure got glossier to match.",
    "The portal opens at midnight. So does everyone's anxiety about the portal.",
],
"consulting": [
    "Somewhere, a deck with 140 slides is being presented to someone who will read slide one.",
    "The framework is a two by two matrix, as all serious thinking is.",
    "The recommendation was to restructure. The fee was not restructured.",
    "Transformation is underway. Nobody remembers the before photo.",
    "The report found what the client hoped it would find.",
    "Alignment was achieved in a workshop with sticky notes.",
    "Best practice was shared. It was someone else's practice.",
    "The partner flew in for a meeting that could have been an email.",
    "The engagement was extended. Engagements usually are.",
    "Low hanging fruit has been identified again.",
    "The slides were final. Then came final final.",
    "Utilisation is high. Sleep is not a billable metric.",
    "The consultant asked to circle back. The circle is now very large.",
    "Every problem is a framework problem if the invoice is big enough.",
],
"health": [
    "The study found an association. A headline found a miracle.",
    "Correlation remains unmoved by the press release.",
    "Ask your doctor. Your doctor would also like a lunch break.",
    "The sample size was small. The confidence was large.",
    "Results in mice are encouraging, especially for the mice.",
    "Wellness trends move faster than peer review.",
    "The supplement aisle has more claims than evidence.",
    "Health tech now tracks everything except whether you looked at it.",
    "Your step count is judging you quietly.",
    "More research is needed. More research is always needed.",
    "The app reminded you to rest. Then it kept reminding you.",
    "Peer review is slow because it reads to the end.",
    "The headline said breakthrough. The paper said modest.",
    "Drink water, they said, again, correctly.",
],
"marketing": [
    "This brand has a purpose now. It is still mostly selling things.",
    "The campaign went viral. The product did not.",
    "The influencer loved the product, as per the contract.",
    "The rebrand cost a fortune. The logo is now lowercase.",
    "Engagement is up. Sales would like to be engaged.",
    "Authenticity was added in post production.",
    "The agency called the idea disruptive. The client asked for a bigger logo.",
    "Every brand wants to be your friend. Your friends do not send push notifications.",
    "The ad was skippable after five seconds. Most people needed two.",
    "Storytelling is back. It is still a coupon.",
    "The brand joined the conversation. Nobody had invited it.",
    "The tagline went through many rounds and came out as a single word.",
    "Award season has begun. Some of the work was made for the jury.",
    "Personalisation means it knows your name and spells it wrong.",
],
"finance": [
    "Your financial advisor also read this paper this morning.",
    "The market will recover. Whether you will is a separate question.",
    "Analysts expect volatility. Analysts always expect volatility.",
    "Past performance is a story people tell at parties.",
    "The rate decision was priced in. The pain was not.",
    "Diversification means losing money in several places at once.",
    "Your SIP continues quietly. It is braver than you.",
    "Gold is up. Your grandmother would like a word.",
    "The fund beat its benchmark, which it chose itself.",
    "Cash is king, says the bank paying you very little for it.",
    "The market reacted to the news. The news is still processing.",
    "Every crash is called unprecedented, which is a lot of precedent.",
    "Compounding is magic, especially in the brochure.",
    "The bull case is ready. So is the bear case. Pick a mood.",
],
"aviation": [
    "Legroom is still being researched.",
    "Boarding by groups continues, with everyone in group one.",
    "The flight was on time. Please hold your applause for the baggage belt.",
    "New routes were announced. The middle seat remains the main route.",
    "The airline has improved the meal. The portion has been informed.",
    "Your bag is on a separate journey of self discovery.",
    "Wifi is available on board, in principle.",
    "Please remain seated until the person in front stands up anyway.",
    "The window seat was booked for a fine view of the wing.",
    "Cabin crew have seen everything, including you reclining.",
    "Airport coffee costs more than the flight, spiritually.",
    "The terminal is world class. The walk to the gate is a pilgrimage.",
    "The aircraft order is historic. The delivery date will also be historic.",
    "The armrest in the middle belongs to whoever wants it more.",
],
"healing": [
    "Your inbox can wait. It always has.",
    "Rest is productive. Your manager has not been told.",
    "This is a good moment to unclench your jaw.",
    "A glass of water is a modest and reliable hero.",
    "Sleep is free and still underrated.",
    "You are allowed to read this slowly.",
    "The research says walk more. Your shoes agree.",
    "Breathing remains available at no extra cost.",
    "Shoulders down. They drifted up while you were reading.",
    "Small habits are boring. That is part of their charm.",
    "You may skip one thing on today's list. Choose kindly.",
    "The phone will still be there after a stretch.",
    "Kindness to yourself counts as maintenance.",
    "Go outside for a minute. The sky has been waiting.",
],
"ai": [
    "The AI is very confident. That is the problem.",
    "Every company is now an AI company, including the ones that make socks.",
    "A new model has launched. The previous one is now described as old.",
    "The chatbot apologised. It will do it again.",
    "AGI has been promised for next year, as it was last year.",
    "The demo worked perfectly. Demos usually do.",
    "The agent can book your flights. Nobody has asked it to yet.",
    "Compute is the new oil. The electricity bill agrees.",
    "The model has been aligned with the values of its marketing team.",
    "Your job is safe, says the company selling the tool that does it.",
    "The context window grew. Attention spans did not.",
    "Somewhere, a GPU is working harder than anyone in this section.",
    "The benchmark was beaten. The benchmark has been replaced.",
    "The model hallucinated. It called it creativity.",
],
"packaging": [
    "The pouch is recyclable, according to the pouch.",
    "Somewhere, a small box is arriving inside a much larger box.",
    "The label says eco-friendly. The label wrote that itself.",
    "Every pack now has a QR code. Nobody has scanned one on purpose.",
    "A brand has gone plastic-free, apart from the lid.",
    "Nobody in history has popped just one bubble.",
    "Easy open, says the packet. Scissors, says experience.",
    "The recycling symbol is a suggestion with arrows.",
    "Resin prices went up. The film got thinner in sympathy.",
    "Your parcel is out for delivery, in a box sized for a fridge.",
    "Corrugated board has carried the economy for years and never asked for credit.",
    "Mono-material means fewer layers to argue about.",
    "The tamper-evident seal worked. It is still on the jar.",
    "Shrink film prices moved. The shrink film declined to comment.",
],

"auto": [
    "Ex-showroom is the number before the real conversation starts.",
    "The waiting period is still measured in months, not kilometres.",
    "On-road price includes things the brochure forgot to mention.",
    "The test drive route never includes the speed breaker outside the gate.",
    "FADA numbers land. Dealer WhatsApp groups interpret them first.",
    "The EV range is laboratory. The traffic is not.",
    "Service appointment slots fill faster than the service bay empties.",
    "Tyre size is a lifestyle choice until the first pothole.",
    "ADAS beeps more than the salesperson talks.",
    "The accessory pack costs as much as a scooter in another life.",
    "BS VI stickers faded. The PUC queue did not.",
    "Motorsport weekends still start with a traffic jam to the circuit.",
    "Clean mobility slides look cleaner than the charging queue.",
    "The fleet manager counts uptime. The driver counts tea breaks.",
],

"realestate": [
    "Carpet area and built-up area remain on speaking terms.",
    "The brochure said lake view. The lake is being discussed.",
    "Possession next quarter has been next quarter for a while.",
    "RERA registration is framed in the sales office, next to the flowers.",
    "The site visit starts with shoes covers and ends with chai.",
    "Someone has measured the balcony twice and got two answers.",
    "Grade A office is still Grade A after the plants arrive.",
    "The REIT yield is public. The parking charge is a surprise.",
    "PropTech has an app for that. The broker still has a WhatsApp group.",
    "Affordable housing is defined carefully in the footnote.",
    "The warehouse is full of nothing that looks like a warehouse from the road.",
    "Green building certification arrives after the marble does.",
    "The floor plan is to scale, said the caption under the artist impression.",
    "EMI calculators never ask how you feel about the traffic.",
],

}

# Sections we never place a strip next to (politics and policy).
POLITICAL = re.compile(r"politic|election|policy|government|geopolit|defen[cs]e|visa|regulation", re.I)
# Stories we never place a strip next to (tragedy, death, illness, disaster, victims).
SENSITIVE = re.compile(r"\b(dead|death|deaths|died|dies|dying|kill\w*|fatal\w*|crash\w*|suicid\w*|murder\w*|rape\w*|abuse\w*|assault\w*|victim\w*|"
                       r"traged\w*|disaster\w*|flood\w*|earthquake\w*|cyclone\w*|wildfire\w*|fire|blaze|explosion\w*|bomb(?:s|ed|ing|ings|er|ers)?|missile\w*|attack\w*|war|"
                       r"terror\w*|shooting\w*|injur\w*|hospitali[sz]ed|cancer\w*|tumou?r\w*|outbreak\w*|ebola|virus\w*|infection\w*|disease\w*|illness\w*|"
                       r"ill|patients?|mortality|dementia|alzheimer\w*|stroke|depress\w*|anxiety|disorder\w*|autism|grief|mourn\w*|funeral\w*|refugee\w*|"
                       r"famine|collapse\w*|drown\w*|layoffs?|evacuat\w*|hostage\w*|missing)\b", re.I)

BANNED = [("\u2014", "em dash"), ("\u2013", "en dash"), (";", "semicolon")]

def validate(line, key=""):
    """Return a list of problems with one interlude line (empty list means it passes)."""
    p = [name for ch, name in BANNED if ch in line]
    if re.search(r"(?i)\bintern(ship)?s?\b", line): p.append("intern word")
    if re.search(r"(?i)\bnot\b[^.]*\bbut\b", line): p.append("not X but Y")
    if re.search(r"(?i)\blol\b|[\U0001F300-\U0001FAFF\u2600-\u27BF]", line): p.append("lol or emoji")
    if re.search(r"(?i)fieldwork|earth5r", line): p.append("FIELDWORK or Earth5R")
    import blocklist
    if blocklist.blocked(line): p.append("BLOCKED: Begin or fair")
    if " - " in line or line.strip() != line or not line.endswith((".", "?", "!")): p.append("format")
    try:
        from build_html import COUNT_RE
        if COUNT_RE.search(line): p.append("counts our own things")
    except Exception:
        pass
    return p

def _check_pools():
    bad = {f"{k}: {l}": validate(l, k) for k, ls in POOLS.items() for l in ls if validate(l, k)}
    dup = [k for k, ls in POOLS.items() if len(set(ls)) != len(ls)]
    if bad or dup:
        raise SystemExit(f"interlude pool breaks house rules: {bad} duplicates in {dup}")
_check_pools()

def per_day(key):
    return max(1, len(POOLS.get(key, [])) // 7)

def lines_for(key, iso, here=os.path.dirname(os.path.abspath(__file__))):
    """Lines for this paper and date: the override file first, then the next block of the pool."""
    pool = POOLS.get(key, [])
    n = per_day(key) if pool else 0
    out, own = [], 0
    f = os.path.join(here, "interludes", f"{key}_{iso}.json")
    if os.path.exists(f):
        for l in json.load(open(f)):
            pr = validate(l, key)
            if pr:
                raise SystemExit(f"interlude override {f} breaks house rules: {l!r} {pr}")
            out.append(l)
        own = len(out)
    if pool:
        day = datetime.date.fromisoformat(iso).toordinal()
        start = (day * n) % len(pool)
        out += [pool[(start + i) % len(pool)] for i in range(n)]
    seen, uniq = set(), []
    for l in out:
        if l not in seen:
            seen.add(l); uniq.append(l)
    return uniq[:max(n, own)]

def _txt(s):
    return f'{s.get("headline", "")} {s.get("summary", "")}'

def safe_slot(prev_name, prev_stories, next_name, next_stories):
    """True when a strip may sit between these two sections."""
    if POLITICAL.search(prev_name or "") or (next_name and POLITICAL.search(next_name)):
        return False
    near = list(prev_stories[-4:]) + list(next_stories[:6])  # end of the section above, the featured top of the one below
    return not any(SENSITIVE.search(_txt(s)) for s in near)

def choose(candidates, n):
    """Spread n strips evenly over the candidate slots (list of slot ids in page order)."""
    if n <= 0 or not candidates:
        return []
    if n >= len(candidates):
        return list(candidates)
    return [candidates[int((i + 0.5) * len(candidates) / n)] for i in range(n)]

def html_strip(line):
    return f'<aside class="interlude" role="note"><p>{html.escape(line)}</p></aside>'

CSS = r"""
.interlude{max-width:820px;margin:34px auto 38px;padding:22px 12px 24px;text-align:center;position:relative;
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.interlude::before,.interlude::after{content:"";position:absolute;left:0;right:0;height:1px;background:var(--rule-soft)}
.interlude::before{top:3px}.interlude::after{bottom:3px}
.interlude p{margin:0 auto;max-width:30ch;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;
  font-size:clamp(23px,6vw,34px);line-height:1.22;letter-spacing:-.005em;color:""" + DARK + r""";text-wrap:balance}
@media (max-width:640px){.interlude{margin:26px 0 30px;padding:18px 4px 20px}}
"""
