"""Rendering, the console, and the brief — asserted on output, not on internals."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from html import unescape
from pathlib import Path

from natdef import brief, build_app, render
from natdef.errors import RenderError
from natdef.ledger import Ledger
from tests.fixtures import with_defect, write_ledger

_COUNTS = re.compile(r'name="natdef:counts" content="([^"]*)"')


class RenderCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.path = write_ledger(self.root)
        self.ledger = Ledger.load(self.path)


class TestRenderAll(RenderCase):
    def test_writes_all_four_pages(self) -> None:
        results = render.render_all(self.ledger, out_dir=self.root)
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertTrue(result.path.is_file(), result.filename)
            self.assertGreater(result.size, 1000)

    def test_no_unresolved_tokens_reach_the_page(self) -> None:
        for result in render.render_all(self.ledger, out_dir=self.root):
            self.assertNotRegex(
                result.html, r"\{\{[A-Z][A-Z0-9_]*\}\}", f"{result.filename} shipped a token"
            )

    def test_counts_meta_matches_the_ledger(self) -> None:
        stats = self.ledger.stats()
        for result in render.render_all(self.ledger, out_dir=self.root):
            match = _COUNTS.search(result.html)
            self.assertIsNotNone(match, result.filename)
            counts = json.loads(unescape(match.group(1)))
            self.assertEqual(counts["brief_number"], stats.brief_number)
            if "timeline_events" in counts:
                self.assertEqual(
                    counts["timeline_events"], stats.timeline_events + stats.additions
                )
            if "archive_entries" in counts:
                self.assertEqual(counts["archive_entries"], stats.archive_entries)

    def test_rendering_is_deterministic_apart_from_the_timestamp(self) -> None:
        first = render.render_all(self.ledger, out_dir=self.root, generated_at="2026-01-01T00:00Z")
        second = render.render_all(self.ledger, out_dir=self.root, generated_at="2026-01-01T00:00Z")
        self.assertEqual([r.html for r in first], [r.html for r in second])

    def test_second_render_reports_unchanged(self) -> None:
        render.render_all(self.ledger, out_dir=self.root)
        again = render.render_all(self.ledger, out_dir=self.root, dry_run=True)
        self.assertTrue(all(not r.changed for r in again), [r.filename for r in again if r.changed])

    def test_a_later_stamp_alone_does_not_count_as_changed(self) -> None:
        """Regression: the stamp appears in the meta tag *and* the footer.

        Masking only the meta tag made every page report stale on every run, which silently
        turned `--check` into a function that always says "stale" — worse than not having it,
        because it trains people to ignore it.
        """
        render.render_all(self.ledger, out_dir=self.root, generated_at="2026-01-01T00:00Z")
        later = render.render_all(
            self.ledger, out_dir=self.root, dry_run=True, generated_at="2026-06-30T23:59Z"
        )
        self.assertTrue(
            all(not r.changed for r in later),
            [r.filename for r in later if r.changed],
        )

    def test_a_real_ledger_change_does_count_as_changed(self) -> None:
        render.render_all(self.ledger, out_dir=self.root)
        data = with_defect(lambda d: d["ledger_meta"].__setitem__("brief_number", 3))
        changed_ledger = Ledger.load(write_ledger(self.root, data), require_schema=False)
        again = render.render_all(changed_ledger, out_dir=self.root, dry_run=True)
        self.assertTrue(any(r.changed for r in again))

    def test_dry_run_writes_nothing(self) -> None:
        render.render_all(self.ledger, out_dir=self.root, dry_run=True)
        self.assertFalse((self.root / "index.html").exists())

    def test_ledger_text_is_escaped_into_the_page(self) -> None:
        data = with_defect(
            lambda d: d["threads"][0].__setitem__("one_line", "<script>alert(1)</script>")
        )
        ledger = Ledger.load(write_ledger(self.root, data))
        html, _, _ = __import__("natdef.pages", fromlist=["x"]).build_dashboard(ledger)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_unknown_page_name_is_an_error(self) -> None:
        with self.assertRaises(Exception):
            render.render_page(self.ledger, "not-a-page.html")


class TestConsole(RenderCase):
    def test_builds_and_bakes_the_ledger(self) -> None:
        html = build_app.build_console(self.ledger, generated_at="2026-01-01T00:00Z")
        self.assertIn('id="natdef-ledger"', html)
        self.assertIn("Test Ledger", html)
        self.assertNotRegex(html, r"\{\{[A-Z][A-Z0-9_]*\}\}")

    def test_fingerprint_detects_a_stale_console(self) -> None:
        out = self.root / build_app.CONSOLE_FILENAME
        out.write_text(build_app.build_console(self.ledger), encoding="utf-8")
        self.assertTrue(build_app.console_is_current(out, self.ledger))

        data = with_defect(lambda d: d["ledger_meta"].__setitem__("brief_number", 3))
        stale_against = Ledger.load(write_ledger(self.root, data), require_schema=False)
        self.assertFalse(build_app.console_is_current(out, stale_against))

    def test_fingerprint_ignores_key_order_and_whitespace(self) -> None:
        reordered = dict(reversed(list(self.ledger.data.items())))
        self.assertEqual(
            build_app.ledger_fingerprint(self.ledger),
            build_app.ledger_fingerprint(Ledger(reordered, path=self.path)),
        )

    def test_missing_console_is_not_current(self) -> None:
        self.assertFalse(
            build_app.console_is_current(self.root / "nope.html", self.ledger)
        )


class TestBrief(RenderCase):
    def test_renders_from_the_archive_entry(self) -> None:
        html = brief.build_brief(self.ledger, 2)
        self.assertIn("The second brief.", html)  # the bottom line, from archive[]
        self.assertIn("A late-file item", html)
        self.assertNotRegex(html, r"\{\{[A-Z][A-Z0-9_]*\}\}")

    def test_late_file_items_run_first(self) -> None:
        html = brief.build_brief(self.ledger, 2)
        self.assertLess(html.index("A late-file item"), html.index("A normal item"))

    def test_item_body_is_used_when_present(self) -> None:
        html = brief.build_brief(self.ledger, 2)
        self.assertIn("First paragraph.", html)

    def test_a_missing_body_is_visibly_marked_not_quietly_empty(self) -> None:
        html = brief.build_brief(self.ledger, 1)
        self.assertIn("Body not written", html)

    def test_refuses_a_number_with_no_archive_entry(self) -> None:
        with self.assertRaises(RenderError) as ctx:
            brief.build_brief(self.ledger, 99)
        self.assertIn("Step 4", str(ctx.exception))

    def test_multi_day_interval_is_stated_on_the_masthead(self) -> None:
        data = with_defect(
            lambda d: (
                d["archive"][1].__setitem__("cutoff", "2026-08-14T15:00Z"),
                d["ledger_meta"].__setitem__("last_cutoff", "2026-08-14T15:00Z"),
            )
        )
        ledger = Ledger.load(write_ledger(self.root, data))
        self.assertIn("multi-day catch-up", brief.build_brief(ledger, 2))

    def test_filename_follows_the_protocol(self) -> None:
        self.assertEqual(
            brief.brief_filename("2026-08-29"), "daily-brief-2026-08-29.html"
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
