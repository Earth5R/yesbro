import json,sys,re
c=json.load(open('/workspace/yesbro/editions2/fetched_new.json'))
BAD=re.compile('[\u2014\u2013;]')
allurls={}
for ed in sys.argv[1:]:
    g={};exec(open(f'/workspace/yesbro/editions2/copy/copy_{ed}.py').read(),g);S=g['S']
    out=[];urls=set();ids=set();probs=[]
    for sec,L in S:
        for i,h,s in L:
            o=c[str(i)];u=o.get('final') or o['url']
            u=re.sub(r'[?&](source|utm_[a-z]+)=[^&]*','',u)
            if o.get('status')!=200: probs.append(f"{i} status {o.get('status')}")
            n=len(s.split())
            if not 30<=n<=50: probs.append(f"{i} words={n}")
            if BAD.search(h+s+sec): probs.append(f"{i} badchar")
            if u in urls or i in ids: probs.append(f"{i} dup")
            if 'news.google' in u: probs.append(f"{i} gnews url")
            pub=str(o.get('pub',''))[:10]
            if pub[:4]=='2026' and pub<'2026-10-21': probs.append(f"{i} old pub {pub}")
            urls.add(u);ids.add(i)
            out.append({"section":sec,"headline":h,"summary":s,"url":u})
    json.dump(out,open(f'/workspace/yesbro/stories_{ed}_2026-10-25.json','w'),indent=1,ensure_ascii=False)
    print(ed,[ (s,len(L)) for s,L in S],"TOTAL",len(out),"PROBLEMS",probs)
