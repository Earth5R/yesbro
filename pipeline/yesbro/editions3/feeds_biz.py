G="https://news.google.com/rss/search?q={}+when:3d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"):
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={"business":[
 "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms","https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
 "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms","https://economictimes.indiatimes.com/small-biz/rssfeeds/5575607.cms",
 "https://www.livemint.com/rss/companies","https://www.livemint.com/rss/markets","https://www.livemint.com/rss/economy","https://www.livemint.com/rss/money",
 "https://www.business-standard.com/rss/companies-101.rss","https://www.business-standard.com/rss/markets-106.rss","https://www.business-standard.com/rss/economy-102.rss",
 "https://www.thehindubusinessline.com/companies/feeder/default.rss","https://www.thehindubusinessline.com/markets/feeder/default.rss",
 "https://www.thehindubusinessline.com/economy/feeder/default.rss","https://www.moneycontrol.com/rss/business.xml","https://www.moneycontrol.com/rss/latestnews.xml",
 "https://www.financialexpress.com/business/feed/","https://www.financialexpress.com/market/feed/","https://www.vccircle.com/rss",
 g("acquisition+OR+acquires+OR+merger+India+company"),g("%22stake%22+deal+crore+India"),g("Sensex+Nifty"),g("IPO+India+subscription+OR+listing"),
 g("Q2+results+profit+India"),g("%22explained%22+OR+explainer+business+India"),g("tender+OR+%22bids+invited%22+OR+%22floats+tender%22+India"),
 g("MSME+India+scheme"),g("GST+council+OR+%22GST+rate%22"),g("%22private+equity%22+India+deal"),g("%22what+is%22+OR+%22how+does%22+stock+market+investors+India"),
]}
