# Yes Bro Architecture, section "Building for India's Climate Zones" (from 27 Oct 2026).
# Climate-responsive building tech for India's five climate zones (hot-dry, warm-humid, composite, temperate, cold, per ECBC and NBC).
G="https://news.google.com/rss/search?q={}+when:3d&hl={}&gl={}&ceid={}:en"
def g(q,r="IN"):
    hl={"IN":"en-IN","US":"en-US","GB":"en-GB"}[r]; return G.format(q,hl,r,r)
FEEDS={"arch":[
 g("%22rammed+earth%22+India+OR+%22mud+house%22+architect"),g("%22compressed+stabilised+earth%22+OR+%22compressed+earth+blocks%22+OR+CSEB"),
 g("%22AAC+blocks%22+OR+%22fly+ash+bricks%22+OR+%22fly+ash+bricks%22+construction+India"),g("%22cool+roof%22+OR+%22cool+roofs%22+India"),
 g("%22heat+action+plan%22+roofs+OR+buildings+India"),g("%22passive+cooling%22+OR+%22natural+ventilation%22+building+India"),
 g("jaali+OR+courtyard+architecture+climate+India"),g("%22climate+responsive%22+OR+%22climate-responsive%22+architecture+India"),
 g("%22vernacular+architecture%22+India"),g("bamboo+construction+OR+%22bamboo+house%22+India"),g("%22mass+timber%22+OR+%22cross+laminated+timber%22+India"),
 g("%22lime+plaster%22+OR+%22lime+mortar%22+building"),g("GRIHA+rating+OR+%22GRIHA+council%22"),g("IGBC+OR+%22Indian+Green+Building+Council%22"),
 g("ECBC+OR+%22Energy+Conservation+Building+Code%22+OR+%22Energy+Conservation+and+Sustainable+Building+Code%22"),
 g("%22Eco+Niwas+Samhita%22+OR+%22ENS%22+residential+energy+code"),g("%22net+zero%22+building+India+OR+%22green+building%22+India"),
 g("%22thermal+comfort%22+OR+%22indoor+heat%22+housing+India"),g("%22BEE%22+building+energy+efficiency+India+OR+%22star+rating%22+buildings"),
 g("%22earth+building%22+OR+%22earthen+architecture%22+OR+%22cob+house%22"),g("Ladakh+OR+Himalayan+%22passive+solar%22+building+OR+trombe"),
 g("Kerala+laterite+OR+%22Laurie+Baker%22+architecture"),g("%22low+carbon%22+construction+materials+India"),g("%22green+cement%22+OR+%22LC3%22+cement+India"),
 g("%22roof+garden%22+OR+%22green+roof%22+India+heat"),g("%22radiative+cooling%22+OR+%22cool+paint%22+building"),
]}
