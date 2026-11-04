# Yes Bro Healing (from 26 Oct 2026): personal wellbeing news. Evidence-minded sources first.
G="https://news.google.com/rss/search?q={}+when:3d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"):
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={"healing":[
 g("site:health.harvard.edu","US"),"https://www.mindful.org/feed/","https://greatergood.berkeley.edu/site/rss/articles",
 "https://www.sciencedaily.com/rss/mind_brain.xml","https://www.sciencedaily.com/rss/health_medicine/nutrition.xml",
 "https://www.sciencedaily.com/rss/health_medicine/fitness.xml","https://www.sciencedaily.com/rss/health_medicine/sleep_disorders.xml",
 "https://www.sciencedaily.com/rss/health_medicine/healthy_aging.xml","https://www.sciencedaily.com/rss/health_medicine/alternative_medicine.xml",
 "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml","https://www.theguardian.com/lifeandstyle/health-and-wellbeing/rss",
 "https://www.theguardian.com/society/mental-health/rss","https://feeds.bbci.co.uk/news/health/rss.xml",
 "https://www.thehindu.com/sci-tech/health/feeder/default.rss","https://indianexpress.com/section/lifestyle/health/feed/",
 "https://www.hindustantimes.com/feeds/rss/lifestyle/health/rssfeed.xml","https://timesofindia.indiatimes.com/life-style/health-fitness/rssfeeds/2886704.cms",
 "https://www.who.int/rss-feeds/news-english.xml",g("site:nccih.nih.gov+OR+site:nih.gov+wellness","US"),
"https://www.npr.org/rss/rss.php?id=1128",
 g("mental+health+India"),g("anxiety+OR+depression+study"),g("longevity+study+OR+%22healthy+ageing%22+OR+%22healthy+aging%22"),
 g("meditation+OR+mindfulness+study"),g("yoga+study+OR+yoga+benefits+research"),g("ayurveda"),g("acupuncture+OR+shiatsu+OR+reflexology+OR+massage+therapy+study"),
 g("breathwork+OR+%22breathing+exercises%22"),g("sleep+study+OR+insomnia"),g("nutrition+study+OR+diet+study"),g("gut+health+study"),
 g("exercise+study+OR+walking+study+OR+strength+training"),g("loneliness+OR+burnout+OR+stress+study"),g("mental+health",'US'),g("wellbeing+OR+wellness",'GB'),
]}
