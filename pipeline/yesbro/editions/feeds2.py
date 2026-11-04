G="https://news.google.com/rss/search?q={}+when:7d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"): 
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={
"ux":[g("%22design+system%22"),g("%22user+research%22+OR+%22usability%22","US"),g("typography+OR+typeface+design","GB"),
 g("India+%22design+agency%22+OR+%22design+studio%22+OR+%22design+firm%22"),g("%22India+Design%22+OR+NID+OR+%22design+week%22+India"),
 g("%22UX%22+OR+%22user+experience%22+Bengaluru+OR+Mumbai+OR+Delhi"),g("designer+jobs+OR+%22design+jobs%22+OR+%22UX+jobs%22","US"),
 g("%22Adobe+MAX%22","US"),g("Framer+OR+Webflow+launch","US"),g("%22AI+design+tool%22+OR+%22AI+for+designers%22","US"),
 g("%22design+startup%22+OR+%22design+platform%22+funding"),g("accessibility+design+app","US"),g("%22product+design%22","US"),
 g("rebrand+logo+India"),g("%22UI+design%22+OR+%22interface+design%22","US"),
 g("%22graphic+design%22+OR+%22visual+design%22","US"),
 g("%22industrial+design%22+OR+%22product+designer%22","US"),
 g("%22interior+design%22+India+OR+%22interior+designer%22"),
 g("%22Red+Dot+Award%22+OR+D%26AD+OR+Awwwards","US"),
 g("%22brand+identity%22+OR+%22logo+design%22","US")],
"arch":[g("Pritzker+OR+%22RIBA%22+OR+%22Aga+Khan+Award%22","GB"),g("%22architecture+competition%22+OR+%22design+competition%22+architecture","GB"),
 g("%22passive+house%22+OR+passivhaus","GB"),g("architect+India+project+design"),g("%22net+zero%22+building+India"),
 g("%22heat+action+plan%22+OR+%22cool+roofs%22+India"),g("%22urban+flooding%22+India"),g("%22affordable+housing%22+India+design"),
 g("bamboo+OR+%22rammed+earth%22+OR+%22hempcrete%22+building","US"),g("%223D+printed%22+house+OR+building","US"),
 g("BIM+OR+%22digital+twin%22+construction+AI","US"),g("%22architecture+biennale%22+OR+%22architecture+exhibition%22","GB"),
 g("%22School+of+Planning+and+Architecture%22+OR+CEPT+OR+%22Council+of+Architecture%22"),g("%22green+building%22+India")],
"schools":[g("%22IB+Diploma%22+OR+%22IB+programme%22+OR+IBO"),g("IGCSE+OR+%22Cambridge+International%22"),g("%22Cambridge+International%22+exam+leak","GB"),
 g("UCAS+deadline+OR+Oxbridge+applications","GB"),g("%22Common+App%22+OR+%22early+action%22+OR+%22early+decision%22","US"),
 g("%22summer+programme%22+OR+%22summer+program%22+high+school+students"),g("%22student+visa%22+UK+OR+US+OR+Canada+Indian"),
 g("teachers+professional+development+OR+pedagogy+OR+assessment","GB"),g("%22NEP+2020%22+OR+%22National+Education+Policy%22+school"),
 g("%22international+school%22+IB+OR+IGCSE+India"),g("%22future+skills%22+OR+careers+students+AI"),g("%22sustainability+education%22+OR+%22climate+curriculum%22+schools"),
 g("%22Indian+students%22+Germany+OR+Ireland+OR+France+OR+Japan")]}
