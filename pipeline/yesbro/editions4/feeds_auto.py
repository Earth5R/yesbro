# Yes Bro Auto (from 31 Oct 2026): Indian auto trade paper, India first then global.
# Trade press plus Google News. Auto Expo, motor shows, trade fairs and expos are never covered for free (blocklist.py).
G="https://news.google.com/rss/search?q={}+when:3d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"):
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={"auto":[
 "https://auto.economictimes.indiatimes.com/rss/recent",
 "https://www.autocarindia.com/rss",
 "https://www.carwale.com/news/feed/",
 "https://www.cardekho.com/news/rss",
 "https://www.moneycontrol.com/rss/automobile.xml",
 "https://economictimes.indiatimes.com/industry/auto/rssfeeds/13357270.cms",
 "https://www.livemint.com/rss/industry",
 "https://www.hindustantimes.com/feeds/rss/auto/rssfeed.xml",
 g("automobile+India+OR+auto+sales+India+OR+SIAM+OR+FADA"),
 g("Maruti+Suzuki+OR+Tata+Motors+OR+Mahindra+OR+Hyundai+India+OR+Toyota+Kirloskar"),
 g("SUV+India+OR+hatchback+India+OR+sedan+India+launch"),
 g("two+wheeler+India+OR+Hero+MotoCorp+OR+Bajaj+Auto+OR+TVS+Motor+OR+Royal+Enfield"),
 g("three+wheeler+India+OR+auto+rickshaw+EV+OR+Piaggio+India"),
 g("electric+vehicle+India+OR+EV+sales+India+OR+charging+station+India+OR+Ola+Electric+OR+Ather"),
 g("commercial+vehicle+India+OR+Ashok+Leyland+OR+Tata+Motors+CV+OR+Eicher"),
 g("tractor+India+OR+Mahindra+tractor+OR+off+highway+OR+JCB+India"),
 g("auto+component+India+OR+ACMA+OR+Bosch+India+OR+Motherson+OR+tyre+India+OR+MRF+OR+Apollo+Tyres"),
 g("car+dealer+India+OR+FADA+OR+auto+retail+India+OR+used+car+India"),
 g("auto+finance+India+OR+vehicle+insurance+India+OR+car+loan+India"),
 g("ADAS+India+OR+software+defined+vehicle+OR+autonomous+vehicle+India+OR+auto+tech"),
 g("FAME+OR+PM+E-DRIVE+OR+CAFE+norms+India+OR+BS+VI+OR+vehicle+scrappage"),
 g("Formula+E+OR+Indian+racing+league+OR+motorsport+India+OR+MotoGP+India"),
 g("green+mobility+India+OR+clean+mobility+OR+hydrogen+vehicle+India"),
 g("automotive","US"),
 g("electric+vehicle+OR+EV+sales","US"),
 g("auto+supplier+OR+automotive+components","US"),
 g("autonomous+driving+OR+ADAS+OR+software+defined+vehicle","US"),
 g("car+sales+OR+dealer","US"),
 g("automotive+OR+electric+vehicle","GB"),
 g("tyre+OR+auto+parts","GB"),
]}
