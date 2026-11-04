import json,re,html,requests,time,trafilatura
from concurrent.futures import ThreadPoolExecutor
from googlenewsdecoder import gnewsdecoder
from picks_new import P
items={i["id"]:i for i in json.load(open("items_new.json"))}
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36","Accept-Language":"en"}
try: cache=json.load(open("fetched_new.json"))
except: cache={}
def resolve(u):
    if "news.google.com" not in u: return u
    for k in range(3):
        try:
            r=gnewsdecoder(u,interval=1)
            if r.get("status") or r.get("success"): return r["decoded_url"]
        except Exception: pass
        time.sleep(2)
    return None
def meta(page,prop):
    m=re.search(r'<meta[^>]+(?:property|name|itemprop)=["\']%s["\'][^>]*content=["\']([^"\']*)'%prop,page,re.I) or re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name|itemprop)=["\']%s["\']'%prop,page,re.I)
    return html.unescape(m.group(1)).strip() if m else ""
def strip(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()
def work(i):
    k=str(i)
    if k in cache and cache[k].get("status")==200: return k,cache[k]
    it=items[i]; u=resolve(it["url"])
    out={"id":i,"title":it["title"],"rss_desc":strip(it["desc"])[:300],"url":u,"status":None,"final":"","ogt":"","ogd":"","tx":"","ts":it["ts"],"pub":""}
    if not u: out["status"]="unresolved"; return k,out
    try:
        r=requests.get(u,headers=UA,timeout=25,allow_redirects=True); out["status"]=r.status_code; out["final"]=r.url
        p=r.text
        out["ogt"]=meta(p,"og:title"); out["ogd"]=meta(p,"og:description") or meta(p,"description")
        out["pub"]=meta(p,"article:published_time") or meta(p,"datePublished") or ""
        if not out["pub"]:
            m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',p); out["pub"]=m.group(1) if m else ""
        t=trafilatura.extract(p) or ""
        if len(t)<150: t=(t+" "+out["ogd"]+" "+out["rss_desc"]).strip()
        out["tx"]=re.sub(r"\s+"," ",t)[:800]
    except Exception as e: out["status"]=str(e)[:60]
    return k,out
ids=list(dict.fromkeys(i for ed in P.values() for v in ed.values() for i in v))
with ThreadPoolExecutor(8) as ex:
    for n,(k,o) in enumerate(ex.map(work,ids)):
        cache[k]=o
        if n%50==0: print(n,flush=True); json.dump(cache,open("fetched_new.json","w"))
json.dump(cache,open("fetched_new.json","w"),indent=0)
from collections import Counter
print(Counter(str(cache[str(i)]["status"]) for i in ids))
