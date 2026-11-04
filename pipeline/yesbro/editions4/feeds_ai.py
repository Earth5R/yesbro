# Yes Bro AI (from 26 Oct 2026): artificial intelligence news. Lab and trade press first, India desks, then Google News queries.
G="https://news.google.com/rss/search?q={}+when:3d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"):
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={"ai":[
 "https://techcrunch.com/category/artificial-intelligence/feed/","https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
 "https://venturebeat.com/category/ai/feed/","https://www.technologyreview.com/topic/artificial-intelligence/feed",
 "https://arstechnica.com/ai/feed/","https://the-decoder.com/feed/","https://www.marktechpost.com/feed/",
 "https://openai.com/news/rss.xml","https://deepmind.google/blog/rss.xml","https://blog.google/technology/ai/rss/",
 "https://huggingface.co/blog/feed.xml","https://www.theregister.com/software/ai_ml/headlines.atom",
 "https://analyticsindiamag.com/feed/","https://inc42.com/tag/artificial-intelligence/feed/","https://yourstory.com/feed",
 "https://www.medianama.com/feed/","https://economictimes.indiatimes.com/tech/artificial-intelligence/rssfeeds/119215726.cms",
 "https://www.livemint.com/rss/AI","https://www.tomshardware.com/feeds/all","https://www.wired.com/feed/tag/ai/latest/rss",
 "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml","https://news.mit.edu/rss/topic/artificial-intelligence2",
 g("artificial+intelligence+India"),g("AI+startup+India+funding"),g("AI+startup+raises","US"),g("OpenAI","US"),g("Anthropic+Claude","US"),
 g("Google+Gemini+AI","US"),g("Meta+AI+Llama+OR+%22Meta+Superintelligence%22","US"),g("xAI+Grok","US"),g("Mistral+AI+OR+DeepSeek+OR+Qwen","US"),
 g("Nvidia+AI+chips","US"),g("AI+data+centre+OR+%22data+center%22+compute","US"),g("AI+chips+India+OR+semiconductor+India+AI"),
 g("large+language+model+research+OR+arxiv+AI+study","US"),g("AI+safety+OR+AI+regulation+OR+%22AI+Act%22","GB"),g("IndiaAI+Mission+OR+MeitY+AI"),
 g("AI+jobs+OR+AI+layoffs+OR+%22AI+at+work%22","US"),g("AI+agents+launch","US"),g("generative+AI+enterprise+India"),
]}
