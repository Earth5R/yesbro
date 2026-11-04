import json,re,html,trafilatura,requests
from concurrent.futures import ThreadPoolExecutor
c=json.load(open("fetched.json"))
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
def strip(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()
def w(k):
    o=c[k]
    if o.get("tx"): return k,o
    t=""
    if o["status"]==200:
        try:
            r=requests.get(o["final"] or o["url"],headers=UA,timeout=25)
            t=trafilatura.extract(r.text) or ""
        except Exception: pass
    if len(t)<150: t=(t+" "+strip(o["rss_desc"])).strip()
    o["tx"]=re.sub(r"\s+"," ",t)[:700]; return k,o
with ThreadPoolExecutor(8) as ex:
    for k,o in ex.map(w,list(c)): c[k]=o
json.dump(c,open("fetched.json","w"),indent=0)
