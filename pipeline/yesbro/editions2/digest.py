import json,sys,re
from picks_new import P
c=json.load(open("fetched_new.json"))
ed=sys.argv[1]
for s,ids in P[ed].items():
    print("##",s)
    for i in ids:
        o=c[str(i)]; t=o.get("ogt") or o["title"]
        tx=o["tx"] if len(o["tx"])>200 else (o["tx"]+" "+o["ogd"]+" "+o["rss_desc"])
        print(f"{i}|{re.sub(r'https?://(www\.)?','',o['final'] or o['url'])[:40]}|{o['pub'][:10]}|{t}\n   {tx[:420]}")
