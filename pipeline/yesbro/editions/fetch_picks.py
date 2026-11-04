import json,re,html,requests,time
from concurrent.futures import ThreadPoolExecutor
from googlenewsdecoder import gnewsdecoder
from picks import P
items={i["id"]:i for i in json.load(open("all.json"))}
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36","Accept-Language":"en"}
try: cache=json.load(open("fetched.json"))
except: cache={}
def resolve(u):
    if "news.google.com" not in u: return u
    for k in range(3):
        try:
            r=gnewsdecoder(u,interval=1)
            if r.get("status") or r.get("success"): return r["decoded_url"]
        except Exception as e: pass
        time.sleep(2)
    return None
def meta(page,prop):
    m=re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']*)'%prop,page,re.I) or re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']%s["\']'%prop,page,re.I)
    return html.unescape(m.group(1)).strip() if m else ""
def work(i):
    k=str(i)
    if k in cache and cache[k].get("status")==200: return k,cache[k]
    it=items[i]; u=resolve(it["url"])
    out={"id":i,"title":it["title"],"rss_desc":it["desc"][:300],"url":u,"status":None,"final":"","ogt":"","ogd":"","text":"","ts":it["ts"]}
    if not u: out["status"]="unresolved"; return k,out
    try:
        r=requests.get(u,headers=UA,timeout=25,allow_redirects=True); out["status"]=r.status_code; out["final"]=r.url
        p=r.text
        out["ogt"]=meta(p,"og:title"); out["ogd"]=meta(p,"og:description") or meta(p,"description")
        ps=[re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",x))).strip() for x in re.findall(r"<p[^>]*>(.*?)</p>",p,re.S)]
        ps=[x for x in ps if len(x)>80]
        out["text"]=" ".join(ps)[:900]
        dm=meta(p,"article:published_time"); out["pub"]=dm
    except Exception as e: out["status"]=str(e)[:60]
    return k,out
ids=[i for ed in P.values() for v in ed.values() for i in v]
ids=list(dict.fromkeys(ids))
with ThreadPoolExecutor(6) as ex:
    for k,o in ex.map(work,ids): cache[k]=o
json.dump(cache,open("fetched.json","w"),indent=0)
from collections import Counter
print(Counter(str(cache[str(i)]["status"]) for i in ids))
