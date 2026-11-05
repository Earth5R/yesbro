"""Share button for every paper and the landing page (imported by build_html.py and build_landing.py).

A visible Share button and a WhatsApp button sit under the dateline, a smaller pair repeats near the foot
of the page, and papers also get a Share line in the slide-out menu. Share uses navigator.share (the
phone's own share sheet) when the browser has it, otherwise it opens a small panel with WhatsApp, X,
LinkedIn, Telegram, Email and Copy link. The shared URL is always the stable paper URL (for example
https://yesbrohq.com/ux/), never an archive URL, and https://yesbrohq.com/ on the landing page.
Share text is house copy: deadpan, no dashes, semicolons, tricolons, counting or intern words, and
Healing never mentions FIELDWORK or Earth5R (the Healing guard in build_html.py still checks the page).
"""
import html, json, re

SITE = "https://yesbrohq.com"

# One deadpan line per paper. The key matches the config "key" (columns.py edition key).
TEXT = {
    "landing": "The newspaper for your field. News, jobs, opportunities and research, every morning.",
    "daily": "India and the world, before your chai goes cold.",
    "business": "Today's deals and markets, without the conference call.",
    "ux": "Today's UX and design news, minus the dark patterns.",
    "arch": "Today's building news, structurally sound.",
    "schools": "Today's school news. Homework optional.",
    "sustainability": "Today's climate and ESG news, printed on recycled pixels.",
    "startups": "Today's startup news. Valuation pending.",
    "highered": "Today's campus news. No entrance exam required.",
    "consulting": "Today's consulting news, billed at zero hours.",
    "health": "Today's health news, handled with care.",
    "marketing": "Today's marketing news, with the adjectives trimmed.",
    "finance": "Today's money news. Past performance guarantees nothing.",
    "aviation": "Today's aviation news, cleared for reading.",
    "healing": "Gentle, evidence-minded news for a calmer day.",
    "ai": "Today's AI news, with the hype left at the door.",
    "packaging": "Today's packaging news, plastic first, with the bubble wrap left on.",
    "fashion": "Today's fashion news, India first, with the receipts attached.",
    "realestate": "Today's real estate news, India first, carpet area included.",
    "auto": "Today's auto news, India first, on-road price included.",
}

def text_for(key, title):
    line = TEXT.get(key) or "Today's paper. Free, unlike your opinions."
    return f"{title}. {line}"

def _check(s):
    bad = [ch for ch in ("\u2014", "\u2013", ";") if ch in s]
    if bad or re.search(r"(?i)\bintern(ship)?s?\b", s):
        raise SystemExit(f"share copy breaks house rules: {s!r}")
for _k, _v in TEXT.items():
    _check(_v)

WA_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2.2a9.7 9.7 0 0 0-8.4 14.6L2.2 21.8l5.1-1.3A9.7 9.7 0 1 0 12 2.2zm0 17.7a8 8 0 0 1-4.1-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 1 1 12 19.9zm4.4-6c-.2-.1-1.4-.7-1.7-.8s-.4-.1-.5.1-.6.8-.8.9-.3.2-.5.1a6.6 6.6 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.5-.4h-.5a.9.9 0 0 0-.6.3 2.7 2.7 0 0 0-.9 2 4.7 4.7 0 0 0 1 2.5 10.8 10.8 0 0 0 4.1 3.6c1.5.7 2.1.7 2.9.6a2.4 2.4 0 0 0 1.6-1.1 2 2 0 0 0 .1-1.1c0-.1-.2-.2-.4-.3z"/></svg>')
SHARE_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M12 3v12M7.5 7.5 12 3l4.5 4.5M5 12v7.5h14V12"/></svg>')

CSS = r"""
.sharebar{display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:8px 10px;margin:10px 0 4px}
.sharebar.foot{margin:18px 0 6px}
.sh-btn{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:0 14px;background:#f3ead6;color:var(--ink);
  border:2px solid var(--rule);border-radius:3px;font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;text-decoration:none;cursor:pointer;-webkit-tap-highlight-color:transparent;line-height:1}
.sh-btn svg{width:18px;height:18px;flex:none}
.sh-btn:hover,.sh-btn:focus-visible{background:#e8dbbb;outline:none}
.sh-btn.wa{border-style:double;border-width:3px}
.sharebar.foot .sh-btn{min-height:34px;font-size:11.5px;padding:0 11px}
@media (max-width:480px){.sharebar{gap:8px}.sh-btn{letter-spacing:.06em;padding:0 10px;font-size:12px;gap:6px}.sh-btn svg{width:16px;height:16px}}
.sharebar .sh-note{flex-basis:100%;text-align:center;font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:12.5px;color:var(--ink-faint);margin:0}
.sh-scrim{position:fixed;inset:0;z-index:90;background:rgba(46,42,36,.42);opacity:0;visibility:hidden;transition:opacity .2s,visibility .2s}
.sh-panel{position:fixed;left:50%;bottom:0;z-index:95;width:min(100%,440px);transform:translate(-50%,105%);visibility:hidden;
  background-color:#f3ead6;border:3px double var(--rule);border-bottom:0;box-shadow:0 -6px 30px rgba(70,50,20,.35);
  padding:12px 16px 18px;transition:transform .22s ease,visibility .22s;color:var(--ink)}
body.share-open .sh-panel{transform:translate(-50%,0);visibility:visible}
body.share-open .sh-scrim{opacity:1;visibility:visible}
@media (min-width:700px){.sh-panel{bottom:auto;top:50%;transform:translate(-50%,-40%);opacity:0;border-bottom:3px double var(--rule)}
  body.share-open .sh-panel{transform:translate(-50%,-50%);opacity:1}}
@media (prefers-reduced-motion:reduce){.sh-panel,.sh-scrim{transition:none}}
.sh-head{display:flex;align-items:center;justify-content:space-between;gap:10px;border-bottom:4px double var(--rule);padding:0 0 8px;margin:0 0 10px}
.sh-head p{margin:0;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-size:30px;line-height:1}
.sh-head p small{display:block;margin-top:4px;font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-faint)}
.sh-x{flex:none;width:42px;height:42px;display:inline-flex;align-items:center;justify-content:center;background:transparent;border:2px solid var(--rule);
  border-radius:3px;color:var(--ink);cursor:pointer;font-size:22px;line-height:1}
.sh-x:hover,.sh-x:focus-visible{background:#e8dbbb;outline:none}
.sh-say{margin:0 0 12px;font-family:"Libre Caslon Text",Georgia,serif;font-style:italic;font-size:14px;line-height:1.4;color:var(--ink-soft)}
.sh-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.sh-grid a,.sh-grid button{display:flex;align-items:center;justify-content:center;gap:7px;min-height:46px;padding:0 10px;background:transparent;
  border:1px solid var(--rule);color:var(--ink);text-decoration:none;font-family:"Old Standard TT",Georgia,serif;font-size:13px;font-weight:700;
  letter-spacing:.1em;text-transform:uppercase;cursor:pointer}
.sh-grid a:hover,.sh-grid button:hover,.sh-grid a:focus-visible,.sh-grid button:focus-visible{background:rgba(90,70,40,.1);outline:none}
.sh-grid .sh-wa{grid-column:1/-1;border:3px double var(--rule);font-size:14px;background:rgba(232,219,187,.7)}
.sh-grid .sh-wa svg{width:20px;height:20px}
.sh-grid .sh-copy{grid-column:1/-1}
.sh-grid .sh-copy.done{background:var(--ink);color:#f3ead6}
.sh-url{margin:10px 0 0;font-family:"Old Standard TT",Georgia,serif;font-size:12px;color:var(--ink-faint);text-align:center;word-break:break-all}
html.share-lock,html.share-lock body{overflow:hidden}
.menu-list .m-share a{color:var(--ink);font-style:normal;font-weight:700}
"""

def _q(s):
    from urllib.parse import quote
    return quote(s, safe="")

def links(url, title, text):
    msg = f"{text} {url}"
    return {
        "wa": "https://wa.me/?text=" + _q(msg),
        "x": "https://x.com/intent/post?text=" + _q(text) + "&url=" + _q(url),
        "li": "https://www.linkedin.com/sharing/share-offsite/?url=" + _q(url),
        "tg": "https://t.me/share/url?url=" + _q(url) + "&text=" + _q(text),
        "mail": "mailto:?subject=" + _q(title) + "&body=" + _q(msg),
    }

def bar(url, title, text, foot=False, label="Share this paper"):
    e = lambda s: html.escape(s, quote=True)
    L = links(url, title, text)
    note = '<p class="sh-note">Forwarding is encouraged here.</p>' if foot else ""
    return (f'<div class="sharebar{" foot" if foot else ""}">'
            f'<button type="button" class="sh-btn sh-open" aria-haspopup="dialog" aria-controls="sh-panel">{SHARE_ICON}{e(label)}</button>'
            f'<a class="sh-btn wa" href="{e(L["wa"])}" target="_blank" rel="noopener" data-sh="wa">{WA_ICON}WhatsApp</a>{note}</div>')

def panel(url, title, text, heading="Share this paper"):
    e = lambda s: html.escape(s, quote=True)
    L = links(url, title, text)
    return (f'<div class="sh-scrim" id="sh-scrim"></div>'
            f'<div class="sh-panel" id="sh-panel" role="dialog" aria-modal="true" aria-labelledby="sh-h" aria-hidden="true"'
            f' data-url="{e(url)}" data-title="{e(title)}" data-text="{e(text)}">'
            f'<div class="sh-head"><p id="sh-h">Pass it on<small>{e(heading)}</small></p>'
            f'<button type="button" class="sh-x" id="sh-x" aria-label="Close share options">&times;</button></div>'
            f'<p class="sh-say">{e(text)}</p>'
            f'<div class="sh-grid">'
            f'<a class="sh-wa" href="{e(L["wa"])}" target="_blank" rel="noopener">{WA_ICON}WhatsApp</a>'
            f'<a href="{e(L["x"])}" target="_blank" rel="noopener">X</a>'
            f'<a href="{e(L["li"])}" target="_blank" rel="noopener">LinkedIn</a>'
            f'<a href="{e(L["tg"])}" target="_blank" rel="noopener">Telegram</a>'
            f'<a href="{e(L["mail"])}">Email</a>'
            f'<button type="button" class="sh-copy" id="sh-copy">Copy link</button></div>'
            f'<p class="sh-url">{e(url)}</p></div>')

# Share opens the native sheet when there is one, otherwise the panel. Escape, the X or a tap outside closes it.
JS = r"""<script>(function(){
var b=document.body,h=document.documentElement,p=document.getElementById('sh-panel');if(!p)return;
var s=document.getElementById('sh-scrim'),x=document.getElementById('sh-x'),cp=document.getElementById('sh-copy'),last=null;
var d={url:p.getAttribute('data-url'),title:p.getAttribute('data-title'),text:p.getAttribute('data-text')};
function open(){b.classList.add('share-open');h.classList.add('share-lock');p.setAttribute('aria-hidden','false');setTimeout(function(){x.focus()},60)}
function close(){b.classList.remove('share-open');h.classList.remove('share-lock');p.setAttribute('aria-hidden','true');if(last)last.focus()}
window.ybShareOpen=open;
function share(e){if(e)e.preventDefault();last=this||null;var mc=document.getElementById('menu-close');if(mc&&b.classList.contains('menu-open')){mc.click();last=document.getElementById('menu-btn')}
 if(navigator.share){navigator.share({title:d.title,text:d.text,url:d.url}).catch(function(err){if(err&&err.name!=='AbortError')open()})}else open()}
var o=document.querySelectorAll('.sh-open');for(var i=0;i<o.length;i++)o[i].addEventListener('click',share);
x.addEventListener('click',close);s.addEventListener('click',close);
document.addEventListener('keydown',function(e){if((e.key==='Escape'||e.key==='Esc')&&b.classList.contains('share-open'))close()});
function done(){cp.textContent='Copied';cp.classList.add('done');setTimeout(function(){cp.textContent='Copy link';cp.classList.remove('done')},2200)}
function fallback(){var t=document.createElement('textarea');t.value=d.url;t.setAttribute('readonly','');t.style.position='fixed';t.style.opacity='0';
 document.body.appendChild(t);t.select();try{document.execCommand('copy');done()}catch(e){prompt('Copy this link',d.url)}document.body.removeChild(t)}
cp.addEventListener('click',function(){if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(d.url).then(done,fallback)}else fallback()});
})();</script>"""

def og_image(key, site_dir="/workspace/yesbro-site"):
    import os
    if key and os.path.exists(os.path.join(site_dir, "img", "landing", f"{key}.webp")):
        return f"{SITE}/img/landing/{key}.webp"
    return f"{SITE}/icon-512.png"
