import json,re,sys,itertools
from collections import defaultdict
it=json.load(open("items_new.json"))
ed=sys.argv[1]; cap=int(sys.argv[2]) if len(sys.argv)>2 else 200
X=[i for i in it if i["ed"]==ed]
def toks(t): return set(w for w in re.findall(r"[a-z0-9]+",t.lower().split(" - ")[0]) if len(w)>3)
JUNK=re.compile(r"live updates|horoscope|quiz|photos:|watch:|video|stock to buy|stocks to buy|share price today|top gainers|top losers|check details|result 2026 live|admit card|answer key",re.I)
byfeed=defaultdict(list)
for i in X:
    if JUNK.search(i["title"]): continue
    byfeed[i["feed"]].append(i)
order=[x for x in itertools.chain.from_iterable(itertools.zip_longest(*byfeed.values())) if x]
keep=[];ts=[]
for i in order:
    t=toks(i["title"])
    if any(len(t&u)/max(1,len(t|u))>0.45 for u in ts): continue
    keep.append(i);ts.append(t)
    if len(keep)>=cap: break
for i in keep:
    s=i["src"] or re.sub(r"^https?://(www\.)?([^/]+).*",r"\2",i["feed"])
    print(f'{i["id"]}|{s[:18]}|{i["title"][:105]}')
