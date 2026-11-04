import json,sys,re,time
c=json.load(open('/workspace/yesbro/editions/fetched.json'))
BAD=re.compile('[\u2014\u2013;]')
for ed,fn in [("ux","copy_ux.py"),("arch","copy_arch.py"),("schools","copy_schools.py")]:
    g={};exec(open('/workspace/yesbro/editions/'+fn).read(),g);S=g['S']
    out=[];urls=set();ids=set();probs=[]
    for sec,L in S:
        for i,h,s in L:
            o=c[str(i)];u=o['url']
            if '?source=rss' in u: u=u.split('?')[0]
            n=len(s.split())
            if not 30<=n<=50: probs.append(f"{i} words={n}")
            if BAD.search(h+s): probs.append(f"{i} badchar")
            if u in urls or i in ids: probs.append(f"{i} dup")
            if 'news.google' in u: probs.append(f"{i} gnews url")
            pub=str(o.get('pub',''))[:10]
            if pub[:4]=='2026' and pub<'2026-10-15': probs.append(f"{i} old pub {pub}")
            urls.add(u);ids.add(i)
            out.append({"section":sec,"headline":h,"summary":s,"url":u})
        print(ed,sec,len(L))
    json.dump(out,open(f'/workspace/yesbro/stories_{ed}_2026-10-25.json','w'),indent=1,ensure_ascii=False)
    print(ed,"TOTAL",len(out),"PROBLEMS",probs)
