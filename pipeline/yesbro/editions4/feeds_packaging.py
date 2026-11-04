# Yes Bro Packaging (from 27 Oct 2026): packaging industry news, plastic packaging first, India first then global.
# Trade press feeds that answer, then Google News queries. Expos and trade fairs are never covered for free (blocklist.py).
G="https://news.google.com/rss/search?q={}+when:3d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"):
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={"packaging":[
 "https://packagingsouthasia.com/feed/","https://www.packagingdive.com/feeds/news/","https://www.plasticstoday.com/rss.xml",
 "https://www.packworld.com/rss","https://www.packagingnews.co.uk/feed","https://www.recyclingtoday.com/rss/","https://www.circularonline.co.uk/feed/",
 g("plastic+packaging+India"),g("flexible+packaging+India"),g("packaging+industry+India"),g("packaging+company+India+results+OR+profit"),
 g("UFlex+OR+%22EPL+Ltd%22+OR+Huhtamaki+India+OR+%22TCPL+Packaging%22+OR+Cosmo+First+OR+Jindal+Poly"),
 g("polymer+prices+India+OR+polyethylene+OR+polypropylene+prices"),g("PET+resin+prices+OR+recycled+PET+India"),
 g("plastic+waste+management+rules+OR+EPR+plastic+packaging+India"),g("plastic+recycling+India"),g("single-use+plastic+India"),
 g("paper+packaging+India+OR+corrugated+boxes+India"),g("e-commerce+packaging+India"),g("FMCG+packaging+India"),
 g("packaging+machinery+India+OR+converting"),g("packaging+startup+India+funding"),g("sustainable+packaging+India"),
 g("Amcor+packaging","US"),g("Berry+Global+OR+Sealed+Air+OR+Sonoco+packaging","US"),g("Smurfit+Westrock+OR+Mondi+OR+DS+Smith+OR+Stora+Enso+packaging","GB"),
 g("flexible+packaging","US"),g("plastic+packaging+recycled+content","GB"),g("packaging+EPR+OR+%22PPWR%22+packaging+regulation","GB"),
 g("plastic+packaging+tax+OR+plastic+treaty+packaging","GB"),g("packaging+acquisition+OR+acquires+packaging+company","US"),
 g("packaging+machinery+OR+packaging+automation","US"),g("sustainable+packaging+brand","US"),g("polymer+resin+prices","US"),
 g("chemical+recycling+plastic","US"),g("bioplastics+OR+compostable+packaging","GB"),g("glass+packaging+OR+aluminium+cans+packaging","GB"),
]}
