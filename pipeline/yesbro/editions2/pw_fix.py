import json,re,trafilatura,asyncio
from playwright.async_api import async_playwright
c=json.load(open("fetched_new.json"))
todo=[k for k,o in c.items() if o["status"]!=200 and o.get("url")]
async def one(br,k,sem):
    async with sem:
        o=c[k]; pg=await br.new_page()
        try:
            r=await pg.goto(o["url"],timeout=35000,wait_until="domcontentloaded")
            await pg.wait_for_timeout(2500)
            t=await pg.title(); h=await pg.content()
            bad=re.search(r"just a moment|access denied|attention required|are you a robot|verify you are human|403 forbidden|not found",t,re.I)
            o["pw_status"]=r.status if r else None; o["pw_title"]=t
            if not bad and len(h)>5000:
                o["status"]=200; o["final"]=pg.url; o["via"]="browser"
                tx=trafilatura.extract(h) or ""
                m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',h); o["pub"]=o.get("pub") or (m.group(1) if m else "")
                if len(tx)<150: 
                    m=re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:description|description)["\'][^>]*content=["\']([^"\']*)',h)
                    tx=(tx+" "+(m.group(1) if m else "")+" "+o["rss_desc"]).strip()
                o["tx"]=re.sub(r"\s+"," ",tx)[:800]
        except Exception as e: o["pw_err"]=str(e)[:80]
        finally: await pg.close()
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await br.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",locale="en-US")
        sem=asyncio.Semaphore(6)
        await asyncio.gather(*[one(ctx,k,sem) for k in todo])
        await br.close()
asyncio.run(main())
json.dump(c,open("fetched_new.json","w"),indent=0)
print(len(todo),"fixed",sum(1 for k in todo if c[k]["status"]==200))
for k in todo:
    if c[k]["status"]!=200: print(k,c[k]["url"][:70],c[k].get("pw_status"),c[k].get("pw_title","")[:40],c[k].get("pw_err","")[:40])
