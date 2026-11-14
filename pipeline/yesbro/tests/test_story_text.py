#!/usr/bin/env python3
"""Blurbs must not open with a bot wall, a cookie banner, or the headline glued to a source."""
from __future__ import annotations

import html as html_lib
import re
import sys
import unittest
from pathlib import Path

PIPE = Path(__file__).resolve().parents[2]
REPO = PIPE.parent
sys.path.insert(0, str(PIPE))

import story_text  # noqa: E402

LEAK = re.compile(
    r"enable javascript|please enable js|disable any ad blocker|just a moment|"
    r"access denied|edgesuite|px-captcha|you don't have permission to access|"
    r"403 forbidden|trouble reading this e-mail|verifying your browser|"
    r"just a quick check|full piece is for subscribers|cookie preferences|"
    r"checking your browser|not redirected automatically|by clicking accept|"
    r"we use cookies to authenticate|empty shell|article body to go on|"
    r"stays with the headline|open teaser|open text|further details were|"
    r"source page returned|for subscribers|subscription required",
    re.I,
)

# Live blurbs from the 14 Nov 2026 sustainability paper (the phone screenshots).
TAXCORP_TITLE = "Legal and Tax Framework for Carbon Credit Transactions and Fraud in India - TaxCorp AI"
TAXCORP = (
    "Enable JavaScript and cookies to continue Legal and Tax Framework for Carbon Credit "
    "Transactions and Fraud in India TaxCorp AI The full piece is for subscribers, and the "
    "headline is all that is public for now."
)
REUTERS_TITLE = "UK, Norway and Canada launch $10 billion climate finance initiative - Reuters"
REUTERS = (
    "Please enable JS and disable any ad blocker UK, Norway and Canada launch $10 billion "
    "climate finance initiative Reuters The full piece is for subscribers, and the headline "
    "is all that is public for now."
)
GREEN_TITLE = "UK SRS for CFOs: Why climate risk is a financial opportunity"
GREEN = (
    "Enable JavaScript and cookies to continue Partner Insight: Emma Littlewood from "
    "51toCarbonZero explains why data can help CFOs better manage risks, identify "
    "opportunities for growth, and build a stronger case for investment Credit - 51 Delta "
    "Intelligence : Climate Risk Matrix This year, there's been"
)
BRUSSELS_TITLE = "Corporate sustainability reports face scrutiny as EU drafts oversight standards - The Brussels Times"
BRUSSELS = (
    "Corporate sustainability reports face scrutiny as EU drafts oversight standards The "
    "Brussels Times The full piece is for subscribers, and the headline is all that is public "
    "for now. Further details were not available in the open teaser."
)
UNDP_TITLE = "COP31: Caspian Sea countries discuss joint action and international support for the region - UNDP"
UNDP = (
    'Access Denied You don\'t have permission to access "http://www.undp.org/kazakhstan/press-releases/'
    'cop31-caspian-sea-countries-discuss-joint-action-and-international-support-region" on this server. '
    "Reference #18.857b3517.1794609420.31c021c https://errors.edgesuite.net/18.857b3517.1794609420.31c021c "
    "The full piece is for subscribers, and the headline is all that is public for now."
)

CF_HTML = (
    "<html><head><title>Just a moment...</title></head>"
    "<body>Just a moment... Enable JavaScript and cookies to continue</body></html>"
)
REUTERS_HTML = (
    "<html><head><title>reuters.com</title></head>"
    "<body>reuters.com Please enable JS and disable any ad blocker</body></html>"
)
AKAMAI_HTML = (
    "<html><head><title>Access Denied</title></head><body>Access Denied "
    "You don't have permission to access \"http://www.undp.org/x\" on this server. "
    "Reference #18.abc https://errors.edgesuite.net/18.abc</body></html>"
)

GOOD = (
    "SAP has made product level emissions and energy data available for selected cloud services. "
    "The methodology uses server activity and aligns with the GHG Protocol ICT Sector Guidance. "
    "The company plans to expand coverage and include more detail for AI workloads. Data is now a product feature."
)
CONSENT_STORY = (
    "The Uttar Pradesh Real Estate Regulatory Authority has barred promoters from using generic "
    "consent forms when altering building plans. Developers must now disclose specific impacts on "
    "carpet area and project specifications before they ask buyers to sign."
)


def _words(text: str) -> int:
    return len(text.split())


class StoryTextTests(unittest.TestCase):
    def test_screenshot_walls_leave_no_blurb(self):
        tax = story_text.present_summary(TAXCORP, TAXCORP_TITLE)
        reuters = story_text.present_summary(REUTERS, REUTERS_TITLE)
        green = story_text.present_summary(GREEN, GREEN_TITLE)
        self.assertEqual(tax, "")
        self.assertEqual(reuters, "")
        self.assertIsNone(LEAK.search(green), green)
        self.assertTrue(green.startswith("Partner Insight:"))
        self.assertIn("Emma Littlewood", green)
        self.assertNotIn("51 Delta", green)
        self.assertNotIn("shell", green.lower())
        self.assertNotIn("subscribers", green.lower())

    def test_headline_plus_source_leaves_no_blurb(self):
        self.assertEqual(story_text.present_summary(BRUSSELS, BRUSSELS_TITLE), "")

    def test_access_denied_page_leaves_no_blurb(self):
        cleaned = story_text.present_summary(UNDP, UNDP_TITLE)
        self.assertEqual(cleaned, "")
        self.assertIsNone(LEAK.search(cleaned))

    def test_live_challenge_pages_do_not_supply_the_blurb(self):
        tax = story_text.assemble_story(
            CF_HTML, 403, TAXCORP_TITLE,
            "Legal and Tax Framework for Carbon Credit Transactions and Fraud in India TaxCorp AI",
            extracted="Enable JavaScript and cookies to continue",
        )
        reuters = story_text.assemble_story(
            REUTERS_HTML, 401, REUTERS_TITLE,
            "UK, Norway and Canada launch $10 billion climate finance initiative Reuters",
            extracted="Please enable JS and disable any ad blocker",
        )
        undp = story_text.assemble_story(
            AKAMAI_HTML, 403, UNDP_TITLE, "",
            extracted=UNDP,
        )
        green = story_text.assemble_story(
            CF_HTML, 403, GREEN_TITLE,
            "Partner Insight: Emma Littlewood from 51toCarbonZero explains why data can help "
            "CFOs better manage risks, identify opportunities for growth, and build a stronger "
            "case for investment. The note was in the feed, not on the blocked page.",
            extracted="Just a moment... Enable JavaScript and cookies to continue",
        )
        self.assertEqual(tax["summary"], "")
        self.assertEqual(reuters["summary"], "")
        self.assertEqual(undp["summary"], "")
        self.assertEqual(tax["text"], "")
        self.assertEqual(reuters["text"], "")
        self.assertIn("Emma Littlewood", green["text"])
        self.assertNotIn("Enable JavaScript", green["text"])
        self.assertIn("Emma Littlewood", green["summary"])
        self.assertIsNone(LEAK.search(green["summary"]), green["summary"])

    def test_real_article_with_a_cookie_banner_in_the_header_is_kept(self):
        article = (
            "Ghana has been issued 6.57 million carbon credits for forest protection efforts "
            "across 2.5 million hectares. The credits were issued under the ART TREES standard "
            "and are the first to receive the Integrity Council label. The country eyes $43 million "
            "from the first buyers and says the programme covers community forests in six regions."
        )
        page = "<html><head><title>Ghana carbon credits</title></head><body>" + article + \
               "<noscript>Enable JavaScript and cookies to continue</noscript></body></html>"
        self.assertFalse(story_text.page_is_challenge(page, 200, article))
        row = story_text.assemble_story(page, 200, "Ghana issues forest carbon credits", article, extracted=article)
        self.assertIn("6.57 million", row["summary"])
        self.assertNotIn("Enable JavaScript", row["summary"])

    def test_clean_summary_and_consent_story_stay(self):
        self.assertEqual(story_text.present_summary(GOOD, "SAP adds product level emissions data"), GOOD)
        self.assertEqual(
            story_text.present_summary(CONSENT_STORY, "UP RERA bars generic consent forms"),
            CONSENT_STORY,
        )

    def test_other_walls(self):
        cases = [
            ("Just a moment... Checking your browser before accessing the site.", "Markets fall for a second week - Reuters"),
            ("px-captcha OpenAI launches ChatGPT Wallet that lets agents make purchases Seeking Alpha "
             "The full piece is for subscribers, and the headline is all that is public for now.",
             "OpenAI launches ChatGPT Wallet that lets agents make purchases - Seeking Alpha"),
            ("🛡️ Just a quick check We’re checking your connection to prevent automated abuse "
             "Lip-reading AI fills gaps in sentences Tech Xplore The full piece is for subscribers, "
             "and the headline is all that is public for now.",
             "Lip-reading AI fills gaps in sentences - Tech Xplore"),
            ("| | | If you have trouble reading this e-mail read the online version | ISSN 2363-4421 | Finance news hub | |",
             "EU newsletter on assurance standards - European Commission"),
            ("Основные файлы cookie позволяют выполнять базовые функции. Cookie Preferences "
             "This cookie is used to store the user's cookie consent preferences. Cookie Preferences "
             "Cookie Preferences Cookie Preferences Cookie Preferences",
             "A firm publishes its climate accounts - Example"),
            ("Oeps, je hebt JavaScript nodig voor deze website. The archaeological research project "
             "of the North/South metro line lends the River Amstel a voice in the historical portrayal of Amsterdam.",
             "River Amstel metro dig - Local desk"),
            ("403 Forbidden nginx Magnifica Air places order for 10 ACJ220-300 aircraft Business Jet Interiors "
             "The full piece is for subscribers, and the headline is all that is public for now.",
             "Magnifica Air places order for 10 ACJ220-300 aircraft - Business Jet Interiors"),
        ]
        for raw, title in cases:
            cleaned = story_text.present_summary(raw, title)
            self.assertIsNone(LEAK.search(cleaned), (raw, cleaned))
            if "archaeological" in raw:
                self.assertIn("Amstel", cleaned)
            else:
                self.assertEqual(cleaned, "", (raw, cleaned))

    def test_wall_prefix_with_real_reporting_keeps_the_reporting(self):
        raw = (
            "Enable JavaScript and cookies to continue A new playbook urges cities to establish "
            "partnerships with community development financial institutions, secure dedicated recovery "
            "funding and remove policy barriers that slow rebuilding after a flood. The note names "
            "three cities already using the checklist and says the next edition adds housing."
        )
        title = "Cities get a recovery playbook"
        cleaned = story_text.present_summary(raw, title)
        self.assertIsNone(LEAK.search(cleaned), cleaned)
        self.assertIn("community development", cleaned)
        self.assertNotIn("Enable JavaScript", cleaned)
        self.assertNotIn("open text", cleaned.lower())

    def test_present_summary_is_stable(self):
        for raw, title in (
            (TAXCORP, TAXCORP_TITLE),
            (REUTERS, REUTERS_TITLE),
            (GREEN, GREEN_TITLE),
            (GOOD, "SAP adds product level emissions data"),
            (UNDP, UNDP_TITLE),
        ):
            once = story_text.present_summary(raw, title)
            twice = story_text.present_summary(once, title)
            self.assertEqual(once, twice)

    def test_fallback_copy_does_not_glue_the_source_name(self):
        sys.path.insert(0, str(PIPE))
        import ai_write
        out = ai_write._fallback_copy([{
            "id": 7,
            "title": REUTERS_TITLE,
            "text": "Please enable JS and disable any ad blocker " + REUTERS_TITLE.replace(" - ", " "),
        }])
        headline, summary = out[7]
        self.assertEqual(summary, "")
        self.assertIn("climate finance", headline.lower())

    def test_published_papers_have_no_wall_left_after_cleaning(self):
        leaks = []
        changed = []
        for index in sorted(REPO.glob("*/index.html")):
            text = index.read_text(encoding="utf-8", errors="replace")
            for block in re.split(r"<article class=\"", text)[1:]:
                headline = re.search(r"<h3><a [^>]*>(.*?)</a>", block)
                summary = re.search(r'<p class="sum">(.*?)</p>', block)
                if not headline or not summary:
                    continue
                title = html_lib.unescape(re.sub(r"<[^>]+>", "", headline.group(1)))
                raw = html_lib.unescape(re.sub(r"<[^>]+>", "", summary.group(1)))
                cleaned = story_text.present_summary(raw, title)
                if LEAK.search(cleaned):
                    leaks.append((index.parent.name, title, cleaned[:220]))
                if story_text.collapse(raw) == cleaned:
                    continue
                wall_or_echo = bool(
                    LEAK.search(raw)
                    or story_text.is_headline_echo(raw, title)
                    or story_text.cookie_banner_dump(raw)
                )
                if wall_or_echo:
                    changed.append(index.parent.name)
                else:
                    leaks.append((index.parent.name, title, "rewrote a clean blurb", raw[:160], cleaned[:160]))
        self.assertEqual(leaks, [])
        self.assertGreaterEqual(len(changed), 3)

    def test_story_card_renders_the_cleaned_blurb(self):
        sys.path.insert(0, str(PIPE / "yesbro"))
        import build_html
        card = build_html.story_html(
            {"headline": REUTERS_TITLE, "summary": REUTERS, "url": "https://www.reuters.com/example"},
            True, "", {},
        )
        self.assertIn("climate finance", card)
        self.assertIn("Read more", card)
        self.assertNotIn('class="sum"', card)
        self.assertNotIn("Please enable JS", card)
        self.assertNotIn("subscribers", card)
        self.assertNotIn("shell", card)
        kept = build_html.story_html(
            {"headline": "A real report", "summary": GOOD, "url": "https://example.com/sap"},
            False, "", {},
        )
        self.assertIn('class="sum"', kept)
        self.assertIn("product level emissions", kept)


if __name__ == "__main__":
    unittest.main()
