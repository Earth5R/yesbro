# Yes Bro news voice: the TechCrunch deadpan (from 26 Oct 2026)

Owner direction, 26 Oct 2026: "It's savage and I love it. We need this deadpan humour in everything."

## Reference example (TechCrunch on Ask Proxy)

> Ask Proxy's biggest differentiator is that it "thinks like a woman," meaning it aims to anticipate your needs before you even ask, the company explains on its website.
> It works like a chatbot you can text like a friend, whether you need gift ideas, help planning an event, or recommendations for things to do that weekend. You can ask it to add important dates to your calendar, set reminders, or help with everyday decisions. You can also send it photos, like an empty table, to figure out how to decorate the table for a dinner party.
> Unlike a typical chatbot, Ask Proxy also takes a proactive approach. It can reach out when it notices something you might forget or when it comes across a new activity, restaurant, or experience you might enjoy.

Why it works: the writer adds no opinion and no adjectives. The company's own grand claim is quoted straight, then the plain facts sit next to it and do the damage. Savage by implication, never by insult.

## The rule

- **Summaries (30 to 50 words)** get the deadpan. Accurate and sourced, but dry and knowing: quote the company's own grand claims straight, set them beside the plain facts, and where it helps, end on one short dry observation.
- **The humour comes from framing and selection only.** Never invent facts, numbers, names, quotes or claims that are not in the source. The closing observation may be a wry aside ("Nobody told the A100.") but must not state a new fact or attribute anything to anyone.
- **Headlines** stay factual and clear. They may be wry but must never mislead.
- **Never mock** victims, tragedies, deaths, illness, disasters, ethnic or religious groups, or anyone's private life. Leave those summaries plain.
- **Politics** stays neutral: dry about process at most, never partisan. When in doubt, write it straight.
- **Healing** stays kind and evidence-minded (no cure claims, keep the caveats). **Schools** stays gentle (readers are teens). Jokes there are about the situation, never the students.
- **House rules still apply:** no em or en dashes, no semicolons, no tricolons in our own asides, no "not X but Y", no counting our own things, never "intern" or "internship", no "lol", no emoji, never explain the joke.
- Not every story needs a punchline. A straight summary that selects the right two facts is often the driest thing on the page.

## Before and after (26 Oct 2026, verbatim)

1. **GPU rental prices are rising, even for older chips** (AI)
   - Before: Rental prices for Nvidia's H200 GPUs have risen 160 percent this year and B200 prices 120 percent, according to data from a16z. Rates for older H100 and A100 chips have also gone up, against the usual pattern of hardware getting cheaper with age.
   - After: Rental prices for Nvidia's H200 GPUs have risen 160 percent this year and B200 prices 120 percent, according to a16z data. Rates for older H100 and A100 chips have gone up too. Hardware is supposed to get cheaper with age, and nobody told the A100.
2. **Google changes its Workspace privacy promise on ads** (Daily)
   - Before: Google long pledged that Gmail, Drive and Photos content never personalises ads. Since 16 October that promise lapses if users let other ad-showing Google services use the content, such as through the opt-in Personal Intelligence tool.
   - After: Google long promised that Gmail, Drive and Photos content would never personalise ads. Since 16 October, that promise lapses if users let other ad-showing Google services use the content, such as through the opt-in Personal Intelligence tool. Never now comes with settings.
3. **Blue Planet III keeps its rough edges to prove it is real** (UX)
   - Before: The BBC's Blue Planet III is leaving in imperfect shots that would normally be cut, to prove its footage is real. Executive producer Elizabeth White spoke to The Guardian about the approach, since footage that looks too polished and seamless is now a giveaway of AI.
   - After: The BBC's Blue Planet III is leaving in imperfect shots that would normally be cut, to prove its footage is real. Executive producer Elizabeth White told The Guardian that footage which looks too polished is now a giveaway of AI. The ocean has been asked to look slightly worse.
4. **Shein to pay $100 million to settle a US FTC probe** (Startups)
   - Before: The fast-fashion retailer will pay $100 million, equal to 44% of its second-quarter profit, to settle an FTC investigation into delivery delays and other complaints, Reuters reported. Consumers filed more than 12,000 complaints.
   - After: Shein will pay $100 million, equal to 44% of its second-quarter profit, to settle an FTC investigation into delivery delays and other complaints, Reuters reported. Consumers filed more than 12,000 complaints. The settlement, unlike some orders, arrived.
5. **Nintex launches a process tool to tie AI to workflows** (AI, juxtaposition with no added line)
   - Before: Nintex has introduced Nintex Processes, a process management product inside its platform. The company says organisations want to coordinate work across people, systems and AI with governance in place, and recent customers include large firms in manufacturing, the public sector and finance.
   - After: Nintex has introduced Nintex Processes, a process management product for managing processes. The company says organisations want to coordinate work across people, systems and AI with governance in place. Recent customers include large firms in manufacturing, the public sector and finance.
6. **Companies get more time to file annual accounts and returns** (Daily)
   - Before: The corporate affairs ministry extended the deadline for filing 2025-26 financial statements to 31 December and annual returns to 31 January 2027. Companies had complained of problems filing through the MCA21 portal.
   - After: The corporate affairs ministry extended the deadline for filing 2025-26 financial statements to 31 December and annual returns to 31 January 2027. Companies had complained of problems filing through the MCA21 portal. The portal has not commented.

## Checking a rewrite

`run26/voice/apply.py <ed>` checks a set of rewritten summaries (`run26/voice/<ed>.py`, `R={index: summary}`) for word count, banned characters, "lol" and emoji, "not X but Y", double quotes and any number that was not in the original summary or headline, and lists capitalised names that are new. `--write` patches the stories json, .html.json, .out.json and the copy source in place, keeping images. For new copy written from scratch, `make_run.py` (field papers) and `gather26/assemble.py` (Daily) still apply.
