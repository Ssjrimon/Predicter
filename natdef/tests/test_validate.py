"""Every Step 6 check, asserted by breaking exactly one thing at a time.

A validator nobody has seen fail is a validator nobody knows works. Each test here
introduces one defect and asserts the specific check catches it — including the four
freshness checks and the retired-claims sweep, which had never run at all before this
rebuild.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from natdef import render, validate
from natdef.ledger import Ledger
from tests.fixtures import with_defect, write_ledger


class ValidateCase(unittest.TestCase):
    """Loads a fixture ledger into a temp directory and validates it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def report_for(self, data=None, *, strict: bool = False, render_pages: bool = False):
        path = write_ledger(self.root, data)
        ledger = Ledger.load(path, require_schema=False)
        if render_pages:
            render.render_all(ledger, out_dir=self.root)
            ledger = Ledger.load(path, require_schema=False)
        # A fixed "now" keeps the cutoff-age check from turning into a clock-dependent test.
        return validate.run(
            ledger, strict=strict, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
        )

    def assertFailsWith(self, report, needle: str) -> None:
        joined = "\n".join(report.failures)
        self.assertTrue(
            report.failed and needle in joined,
            f"expected a failure containing {needle!r}; got failures: {report.failures}",
        )


class TestCleanLedger(ValidateCase):
    def test_the_fixture_passes(self) -> None:
        report = self.report_for()
        self.assertFalse(report.failed, f"unexpected failures: {report.failures}")

    def test_no_check_is_silently_skipped_once_pages_exist(self) -> None:
        report = self.report_for(render_pages=True)
        self.assertFalse(report.failed, report.failures)
        self.assertEqual(report.skipped, [], f"unexpected skips: {report.skipped}")


class TestThreadChecks(ValidateCase):
    def test_intensity_out_of_range(self) -> None:
        data = with_defect(lambda d: d["threads"][0].__setitem__("intensity", 11))
        self.assertFailsWith(self.report_for(data), "intensity")

    def test_invalid_direction(self) -> None:
        data = with_defect(lambda d: d["threads"][0].__setitem__("direction", "worsening"))
        self.assertFailsWith(self.report_for(data), "direction")

    def test_duplicate_thread_codes(self) -> None:
        data = with_defect(lambda d: d["threads"][1].__setitem__("code", "IR"))
        self.assertFailsWith(self.report_for(data), "duplicate thread codes")

    def test_threads_out_of_sync_with_newest_archive(self) -> None:
        """The Brief 011 defect: Step 4.8 done, Step 4.2 skipped."""
        data = with_defect(lambda d: d["threads"][0].__setitem__("intensity", 7))
        self.assertFailsWith(self.report_for(data), "out of sync with the newest archive")


class TestSourceChecks(ValidateCase):
    def test_superseded_by_must_resolve(self) -> None:
        data = with_defect(lambda d: d["sources"][0].__setitem__("superseded_by", "NOPE"))
        self.assertFailsWith(self.report_for(data), "superseded_by")

    def test_superseded_without_a_replacement(self) -> None:
        data = with_defect(lambda d: d["sources"][0].pop("superseded_by"))
        self.assertFailsWith(self.report_for(data), "names no superseded_by")


class TestCitationChecks(ValidateCase):
    def test_dead_registry_code_fails(self) -> None:
        data = with_defect(lambda d: d["timeline"][0].__setitem__("src", ["GHOST"]))
        self.assertFailsWith(self.report_for(data), "dead reference")

    def test_free_text_fails_by_default(self) -> None:
        """Since the 6 Sep 2026 backfill there are none left, so a new one is a defect."""
        data = with_defect(
            lambda d: d["timeline"][0].__setitem__("src", ["Reuters via AOL, 28 Aug 2026"])
        )
        self.assertFailsWith(self.report_for(data), "free-text citation")

    def test_a_long_registry_code_that_resolves_nowhere_is_dead_not_free_text(self) -> None:
        """The discriminator is whitespace, not length: a mistyped long code is a dead ref."""
        data = with_defect(lambda d: d["timeline"][0].__setitem__("src", ["AJ-HORMUZ-0827"]))
        self.assertFailsWith(self.report_for(data), "dead reference")

    def test_a_source_registered_without_a_url_warns_by_default(self) -> None:
        data = with_defect(lambda d: d["sources"][1].pop("url"))
        report = self.report_for(data)
        self.assertFalse(report.failed, report.failures)
        self.assertTrue(any("carries no url" in w for w in report.warnings))

    def test_a_source_registered_without_a_url_fails_under_strict(self) -> None:
        data = with_defect(lambda d: d["sources"][1].pop("url"))
        self.assertFailsWith(self.report_for(data, strict=True), "carries no url")

    def test_the_press_sentinel_never_fails_even_under_strict(self) -> None:
        """It has no single URL by design; failing it would be asking for a fabrication."""
        data = with_defect(lambda d: d["timeline"][0].__setitem__("src", ["PRESS"]))
        report = self.report_for(data, strict=True)
        self.assertFalse(report.failed, report.failures)


class TestCutoffChecks(ValidateCase):
    def test_malformed_cutoff_fails(self) -> None:
        data = with_defect(lambda d: d["ledger_meta"].__setitem__("last_cutoff", "yesterday"))
        self.assertFailsWith(self.report_for(data), "does not parse")

    def test_future_cutoff_fails(self) -> None:
        data = with_defect(
            lambda d: d["ledger_meta"].__setitem__("last_cutoff", "2030-01-01T00:00Z")
        )
        self.assertFailsWith(self.report_for(data), "in the future")

    def test_stale_cutoff_warns_but_does_not_fail(self) -> None:
        data = with_defect(
            lambda d: d["ledger_meta"].__setitem__("last_cutoff", "2026-08-01T00:00Z")
        )
        report = self.report_for(data)
        self.assertFalse(report.failed, report.failures)
        self.assertTrue(any("multi-day catch-up" in w for w in report.warnings))


class TestArchiveChecks(ValidateCase):
    def test_numbering_gap_fails(self) -> None:
        data = with_defect(lambda d: d["archive"][1].__setitem__("number", 3))
        self.assertFailsWith(self.report_for(data), "sequential")

    def test_duplicate_dates_fail(self) -> None:
        data = with_defect(lambda d: d["archive"][1].__setitem__("date", "2026-08-08"))
        self.assertFailsWith(self.report_for(data), "duplicate dates")

    def test_unknown_item_thread_code_fails(self) -> None:
        data = with_defect(lambda d: d["archive"][0]["items"][0].__setitem__("thread", "ZZ"))
        self.assertFailsWith(self.report_for(data), "unknown thread code")

    def test_cross_thread_em_dash_sentinel_is_allowed(self) -> None:
        """A real, allow-listed sentinel — Brief 002 item 05. Do not "fix" it."""
        data = with_defect(lambda d: d["archive"][0]["items"][0].__setitem__("thread", "—"))
        report = self.report_for(data)
        self.assertFalse(report.failed, report.failures)

    def test_archive_entry_pointing_at_a_missing_file_fails(self) -> None:
        write_ledger(self.root)
        # write_ledger creates a file for every archive entry, so delete one to produce the
        # defect rather than renaming the entry (which would just create the new name too).
        (self.root / "briefs" / "daily-brief-2026-08-08.html").unlink()
        ledger = Ledger.load(self.root / "intel-ledger.json", require_schema=False)
        report = validate.run(ledger, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFailsWith(report, "does not exist on disk")

    def test_a_brief_on_disk_with_no_archive_entry_fails(self) -> None:
        """The other direction — this is what catches a skipped Step 4.8."""
        path = write_ledger(self.root)
        (self.root / "briefs" / "daily-brief-2026-08-30.html").write_text("<html>", "utf-8")
        ledger = Ledger.load(path, require_schema=False)
        report = validate.run(ledger, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFailsWith(report, "Step 4.8 was skipped")


class TestNodeChecks(ValidateCase):
    def test_edge_to_a_nonexistent_node_fails(self) -> None:
        data = with_defect(lambda d: d["node_edges"][0].__setitem__("to", "atlantis"))
        self.assertFailsWith(self.report_for(data), "is not a map_nodes id")

    def test_self_referential_edge_fails(self) -> None:
        data = with_defect(lambda d: d["node_edges"][0].__setitem__("to", "iran"))
        self.assertFailsWith(self.report_for(data), "self-referential")

    def test_invalid_edge_type_fails(self) -> None:
        data = with_defect(lambda d: d["node_edges"][0].__setitem__("type", "friendly"))
        self.assertFailsWith(self.report_for(data), "type")

    def test_node_history_needs_a_date_title_and_body(self) -> None:
        data = with_defect(lambda d: d["node_history"]["iran"][0].pop("date"))
        self.assertFailsWith(self.report_for(data), "missing")

    def test_node_history_tier_must_be_valid(self) -> None:
        data = with_defect(lambda d: d["node_history"]["iran"][0].__setitem__("tier", "solid"))
        self.assertFailsWith(self.report_for(data), "tier")


class TestRenderedFreshness(ValidateCase):
    """The four checks that were SKIPPED before render.py existed."""

    def test_missing_pages_are_skipped_not_failed(self) -> None:
        report = self.report_for()
        self.assertFalse(report.failed, report.failures)
        self.assertTrue(any("run `python3 -m natdef.render`" in s for s in report.skipped))

    def test_a_page_behind_the_ledger_fails(self) -> None:
        path = write_ledger(self.root)
        ledger = Ledger.load(path)
        render.render_all(ledger, out_dir=self.root)
        # Add an archive entry and its file, without re-rendering. This is drift.
        data = with_defect(
            lambda d: (
                d["archive"].append(
                    {
                        **d["archive"][1],
                        "number": 3,
                        "date": "2026-08-10",
                        "file": "briefs/daily-brief-2026-08-10.html",
                        "cutoff": "2026-08-10T15:00Z",
                    }
                ),
                d["ledger_meta"].__setitem__("brief_number", 3),
            )
        )
        write_ledger(self.root, data)
        drifted = Ledger.load(self.root / "intel-ledger.json", require_schema=False)
        report = validate.run(drifted, now=datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc))
        self.assertFailsWith(report, "the page is behind the ledger")

    def test_brief_number_mismatch_is_caught(self) -> None:
        path = write_ledger(self.root)
        ledger = Ledger.load(path)
        render.render_all(ledger, out_dir=self.root)
        data = with_defect(lambda d: d["ledger_meta"].__setitem__("brief_number", 99))
        write_ledger(self.root, data)
        drifted = Ledger.load(self.root / "intel-ledger.json", require_schema=False)
        report = validate.run(drifted, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFailsWith(report, "brief number")

    def test_a_page_without_the_counts_tag_fails(self) -> None:
        path = write_ledger(self.root)
        (self.root / "index.html").write_text("<html><body>hand-written</body></html>", "utf-8")
        ledger = Ledger.load(path, require_schema=False)
        report = validate.run(ledger, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFailsWith(report, "natdef:counts")


class TestRetiredClaims(ValidateCase):
    """The check Step 6 required and that nothing had ever implemented."""

    RETIRED = {
        "id": "test-claim",
        "claim": "A claim that was withdrawn.",
        "retired_on": "2026-08-08",
        "retired_by_brief": 2,
        "reason": "It was wrong.",
        "patterns": [r"scheduled tasks?[^.]{0,40}run in the cloud"],
        "exempt_files": [],
    }

    def test_empty_registry_passes_but_is_reported_as_enforced(self) -> None:
        report = self.report_for()
        self.assertTrue(any("retired claims" in p for p in report.passed))

    def test_a_reappearing_claim_fails(self) -> None:
        data = with_defect(lambda d: d["retired_claims"].append(self.RETIRED))
        write_ledger(self.root, data)
        (self.root / "briefs" / "daily-brief-2026-08-09.html").write_text(
            "<html><body><p>Scheduled tasks run in the cloud, as established.</p></body></html>",
            "utf-8",
        )
        ledger = Ledger.load(self.root / "intel-ledger.json", require_schema=False)
        report = validate.run(ledger, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFailsWith(report, "test-claim")

    def test_a_brief_filed_before_the_retirement_is_exempt(self) -> None:
        """Delivered briefs are never rewritten, so they still hold the claim they made."""
        data = with_defect(lambda d: d["retired_claims"].append(self.RETIRED))
        write_ledger(self.root, data)
        (self.root / "briefs" / "daily-brief-2026-08-08.html").write_text(
            "<html><body><p>Scheduled tasks run in the cloud.</p></body></html>", "utf-8"
        )
        ledger = Ledger.load(self.root / "intel-ledger.json", require_schema=False)
        report = validate.run(ledger, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFalse(report.failed, report.failures)

    def test_a_preserved_retraction_notice_is_exempt(self) -> None:
        data = with_defect(lambda d: d["retired_claims"].append(self.RETIRED))
        write_ledger(self.root, data)
        (self.root / "briefs" / "RETRACTED-brief-003-2026-08-16.html").write_text(
            "<html><body><p>Scheduled tasks run in the cloud.</p></body></html>", "utf-8"
        )
        ledger = Ledger.load(self.root / "intel-ledger.json", require_schema=False)
        report = validate.run(ledger, now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
        self.assertFalse(report.failed, report.failures)

    def test_an_uncompilable_pattern_is_reported_not_swallowed(self) -> None:
        bad = {**self.RETIRED, "patterns": ["(unclosed"]}
        data = with_defect(lambda d: d["retired_claims"].append(bad))
        self.assertFailsWith(self.report_for(data), "not a valid regex")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
