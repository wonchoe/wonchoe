"""Keep the portfolio card's scope and aggregates honest in every SVG variant."""
import copy
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import build_portfolio


SVG = "{http://www.w3.org/2000/svg}"


class PortfolioCardTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "schemaVersion": 1,
            "source": "Cloudflare / connected sites",
            "scope": "accessible_zones",
            "siteCount": 3,
            "updated": "2026-10-10",
            "period": {"start": "2026-09-10", "end": "2026-10-09", "days": 30},
            "totals": {"requests": 30000, "cachedRequests": 18000,
                       "bytes": 987654321, "cachedBytes": 567890123},
            "countries": [{"code": "US", "name": "United States", "requests": 20000},
                          {"code": "UA", "name": "Ukraine", "requests": 10000}],
        }

    def test_every_variant_reports_the_same_actual_metrics_and_domain_scope(self):
        descriptions = set()
        for mobile in (False, True):
            for static in (False, True):
                with self.subTest(mobile=mobile, static=static):
                    root = ET.fromstring(build_portfolio.build(self.data, mobile=mobile, static=static))
                    description = root.find(SVG + "desc").text
                    descriptions.add(description)
                    self.assertEqual(root.attrib["aria-label"], description)
                    for expected in ("30,000 HTTP requests", "987,654,321 transferred bytes",
                                     "3 connected Cloudflare domains", "18,000 requests served from cache",
                                     "2 countries and territories", "2026-09-10 to 2026-10-09 UTC",
                                     "all Cloudflare zones accessible", "not unique visitors"):
                        self.assertIn(expected, description)
                    self.assertNotIn("cursor.style", description)
                    ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
                    for node in root.iter():
                        reference = node.attrib.get("href")
                        if reference:
                            self.assertTrue(reference.startswith("#"), "Profile images must be self-contained")
                            self.assertIn(reference[1:], ids)
        self.assertEqual(len(descriptions), 1)

    def test_cursor_only_snapshot_cannot_be_rendered_as_portfolio(self):
        cursor = copy.deepcopy(self.data)
        cursor["source"] = "Cloudflare / cursor.style"
        cursor.pop("scope")
        cursor.pop("siteCount")
        with self.assertRaises(ValueError):
            build_portfolio.build(cursor)
        with self.assertRaises(ValueError):
            build_portfolio.build(None)

    def test_static_fallbacks_do_not_animate(self):
        for mobile in (False, True):
            root = ET.fromstring(build_portfolio.build(self.data, mobile=mobile, static=True))
            style = root.find(SVG + "style").text
            self.assertNotIn("@keyframes", style)
            self.assertIn("animation:none", style)
            self.assertFalse(any(node.tag.removeprefix(SVG) in ("animate", "animateMotion", "animateTransform")
                                 for node in root.iter()))

    def test_zero_traffic_is_data_and_does_not_become_missing_or_infinite(self):
        self.data["totals"] = dict.fromkeys(self.data["totals"], 0)
        self.data["countries"] = []
        for mobile in (False, True):
            root = ET.fromstring(build_portfolio.build(self.data, mobile=mobile))
            description = root.find(SVG + "desc").text
            self.assertIn("0 HTTP requests and 0 transferred bytes", description)
            self.assertIn("0 countries and territories", description)
            self.assertNotIn("awaiting", description.lower())
            self.assertNotIn("nan", description.lower())
            self.assertNotIn("infinity", description.lower())

    def test_unknown_or_invalid_domain_scope_is_rejected(self):
        for key, value in (("scope", "all_sites"), ("scope", None),
                           ("siteCount", True), ("siteCount", 0),
                           ("siteCount", -1), ("siteCount", 2.5)):
            with self.subTest(key=key, value=value):
                data = dict(self.data, **{key: value})
                with self.assertRaises(ValueError):
                    build_portfolio.build(data)


if __name__ == "__main__":
    unittest.main()
