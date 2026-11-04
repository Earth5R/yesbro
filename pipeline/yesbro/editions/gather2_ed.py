import feedparser, requests, json, re, html, calendar, sys
from concurrent.futures import ThreadPoolExecutor
from feeds2 import FEEDS
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
CUT=calendar.timegm((2026,10,17,18,30,0))  # last ~7 days
def get(args):
    ed,u=args
    try:
        r=requests.get(u,headers=UA,timeout=20); f=feedparser.parse(r.content)
    except Exception as e: return ed,u,str(e)[:40],[]
    out=[]
    for e in f.entries:
        t=e.get("published_parsed") or e.get("updated_parsed")
        ts=calendar.timegm(t) if t else None
        if not ts or ts<CUT or ts>calendar.timegm((2026,10,26,0,0,0)): continue
        d=re.sub(r"<[^>]+>"," ",html.unescape(e.get("summary","") or ""));d=re.sub(r"\s+"," ",d).strip()[:450]
        src=(e.get("source") or {}).get("title","")
        out.append({"ed":ed,"feed":u,"title":html.unescape(e.get("title","")).strip(),"url":e.get("link",""),"ts":ts,"desc":d,"src":src})
    return ed,u,r.status_code,out
jobs=[(s,u) for s,us in FEEDS.items() for u in us]
allit=[]
with ThreadPoolExecutor(24) as ex:
    for ed,u,st,items in ex.map(get,jobs):
        print(ed,st,len(items),u); allit+=items
seen=set();res=[]
for i in allit:
    k=(i["ed"],i["url"])
    if k in seen or not i["url"]: continue
    seen.add(k);res.append(i)
res.sort(key=lambda i:-i["ts"])
for n,i in enumerate(res): i["id"]=n
json.dump(res,open("items2.json","w"),indent=0)
print(len(res))
