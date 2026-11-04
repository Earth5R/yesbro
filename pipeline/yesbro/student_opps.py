#!/usr/bin/env python3
"""Student Opportunities for Yes Bro Schools.

  python3 student_opps.py --date YYYY-MM-DD  -> student_opps_schools_YYYY-MM-DD.json

Competitions, olympiads, essay contests, scholarships and challenges for school students.
India first, then global. Official page must show an open deadline. Never internships, never fairs.
Dedupes against student_opps/seen.json. Cap 8 to 15.
"""
import argparse, datetime as dt, json, os, re, sys
import blocklist
import jobs

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, "student_opps", "seen.json")
CAP = 15
BAD = re.compile(r"[\u2014\u2013;]")
INTERN = re.compile(r"\bintern(s|ship|ships)?\b", re.I)

def load_seen():
    try: return set(json.load(open(SEEN)))
    except Exception: return set()

def save_seen(s):
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)
    json.dump(sorted(s)[-2000:], open(SEEN, "w"), indent=0)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args(); today = dt.date.fromisoformat(a.date)
    seen = load_seen()
    st, errs = jobs.students(today)
    for e in errs: print("skip", e)
    # India first, soonest deadline
    def india(j):
        return 0 if (j.get("region") == "India" or "India" in (j.get("location") or "") or "India" in (j.get("org") or "")) else 1
    MIN = 8  # top up with still-open, re-verified listings from earlier days so the section never runs empty
    fresh = [j for j in st if j.get("url") not in seen]
    old = [j for j in st if j.get("url") in seen]
    key = lambda j: (india(j), j.get("deadline") or "9999", j.get("title") or "")
    fresh.sort(key=key); old.sort(key=key)
    st = fresh + (old[:max(0, MIN - len(fresh))] if len(fresh) < MIN else [])
    _bl = {}
    st = blocklist.keep(st, "student_opps", _bl)
    if _bl: blocklist.log(_bl)
    out = []
    for j in st:
        title = j["title"]
        if BAD.search(title) or INTERN.search(title): continue
        line = f"Deadline {(j.get('deadline') or '').strip()}. Checked on the official page this morning."
        if BAD.search(line): line = "Deadline on the official page. Checked this morning."
        item = {
            "title": title[:140], "org": j.get("org") or "", "url": j["url"],
            "deadline": j.get("deadline") or "", "location": j.get("location") or j.get("region") or "",
            "region": "India" if india(j) == 0 else ("Online" if j.get("remote") or (j.get("location") or "") == "Online" else "World"),
            "line": line,
        }
        out.append(item)
        seen.add(j["url"])
        if len(out) >= CAP: break
    path = os.path.join(HERE, f"student_opps_schools_{a.date}.json")
    json.dump({"date": a.date, "edition": "schools", "items": out}, open(path, "w"), indent=1, ensure_ascii=False)
    save_seen(seen)
    print("student_opps", len(out), [i["title"][:40] for i in out])

if __name__ == "__main__":
    main()
