"""The whole pipeline against the real ``intel-ledger.json``.

These assert only what must always be true of the operation's real data — it loads, it
renders, it validates clean, and the pages agree with it. They deliberately do not assert
specific counts: a brief filed tomorrow changes every count, and a test that has to be
edited each brief is a test people learn to edit without reading.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from natdef import build_app, render, validate
from natdef.ledger import Ledger

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "intel-ledger.json"


@unittest.skipUnless(LEDGER.is_file(), "the real ledger is not present")
class TestRealLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = Ledger.load(LEDGER)

    def test_it_loads_and_meets_its_structural_contract(self) -> None:
        self.assertEqual(self.ledger.schema_problems(), [])
        self.assertGreaterEqual(self.ledger.brief_number, 12)

    def test_every_timeline_date_parses(self) -> None:
        """40% of them are free-text prose; an unsortable one silently breaks the chronology."""
        from natdef.ledger import parse_ledger_date

        unparseable = [e.date for e in self.ledger.all_events() if parse_ledger_date(e.date) is None]
        self.assertEqual(unparseable, [], f"unsortable dates: {unparseable}")

    def test_it_validates_with_no_failures(self) -> None:
        report = validate.run(self.ledger)
        self.assertFalse(report.failed, "\n".join(report.failures))

    def test_no_check_is_skipped(self) -> None:
        """The four render-dependent checks must be live, not stood down."""
        report = validate.run(self.ledger)
        self.assertEqual(report.skipped, [], f"skipped checks: {report.skipped}")

    def test_it_renders_without_shipping_a_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for result in render.render_all(self.ledger, out_dir=Path(tmp)):
                self.assertNotRegex(
                    result.html, r"\{\{[A-Z][A-Z0-9_]*\}\}", result.filename
                )

    def test_the_console_builds(self) -> None:
        html = build_app.build_console(self.ledger)
        self.assertGreater(len(html), 100_000)
        self.assertNotRegex(html, r"\{\{[A-Z][A-Z0-9_]*\}\}")

    def test_every_delivered_brief_has_an_archive_entry(self) -> None:
        filed = {e.brief_filename for e in self.ledger.archive}
        for path in self.ledger.brief_files_on_disk():
            self.assertIn(path.name, filed, f"{path.name} has no archive[] entry")

    def test_pages_on_disk_agree_with_the_ledger(self) -> None:
        """If this fails, someone committed a ledger change without re-rendering."""
        report = validate.Report()
        validate.check_rendered_pages(self.ledger, report)
        self.assertFalse(report.failed, "\n".join(report.failures))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
