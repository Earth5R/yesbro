import feedparser, requests, json, re, html, calendar, sys, time
from concurrent.futures import ThreadPoolExecutor
from feeds_biz import FEEDS
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
CUT=calendar.timegm((2026,10,22,18,30,0))  # since 23 Oct 2026 00:00 IST
NOW=time.time()+3600
def get(args):
    ed,u=args
    try:
        r=requests.get(u,headers=UA,timeout=20); f=feedparser.parse(r.content); st=r.status_code
    except Exception as e: return ed,u,str(e)[:40],[]
    out=[]
    for e in f.entries:
        t=e.get("published_parsed") or e.get("updated_parsed")
        ts=calendar.timegm(t) if t else None
        if not ts or ts<CUT or ts>NOW: continue
        d=re.sub(r"<[^>]+>"," ",html.unescape(e.get("summary","") or ""));d=re.sub(r"\s+"," ",d).strip()[:450]
        src=(e.get("source") or {}).get("title","")
        out.append({"ed":ed,"feed":u,"title":html.unescape(e.get("title","")).strip(),"url":e.get("link",""),"ts":ts,"desc":d,"src":src})
    return ed,u,st,out
jobs=[(s,u) for s,us in FEEDS.items() for u in us]
allit=[]
with ThreadPoolExecutor(32) as ex:
    for ed,u,st,items in ex.map(get,jobs):
        print(ed,st,len(items),u[:110]); allit+=items
seen=set();res=[]
for i in allit:
    k=(i["ed"],i["url"]); kt=(i["ed"],i["title"].lower()[:70])
    if k in seen or kt in seen or not i["url"]: continue
    seen.add(k);seen.add(kt);res.append(i)
res.sort(key=lambda i:-i["ts"])
for n,i in enumerate(res): i["id"]=n
json.dump(res,open("items_biz.json","w"),indent=0)
from collections import Counter
print(len(res),Counter(i["ed"] for i in res))
