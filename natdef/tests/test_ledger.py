"""Ledger loading, normalisation and the two real format ambiguities it absorbs."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from natdef.errors import LedgerNotFoundError, LedgerParseError, LedgerSchemaError
from natdef.ledger import Ledger, format_cutoff, parse_cutoff, parse_ledger_date
from tests.fixtures import MINIMAL_LEDGER, with_defect, write_ledger


class TestCutoffParsing(unittest.TestCase):
    def test_accepts_both_real_formats(self) -> None:
        """Every brief but 12 used HH:MM; Brief 12 used HHMM. Same instant."""
        with_colon = parse_cutoff("2026-08-29T22:00Z")
        without = parse_cutoff("2026-08-29T2200Z")
        self.assertIsNotNone(with_colon)
        self.assertEqual(with_colon, without)
        self.assertEqual(with_colon.tzinfo, timezone.utc)

    def test_rejects_garbage_rather_than_guessing(self) -> None:
        for bad in ("", None, "2026-08-29", "yesterday", "2026-13-01T00:00Z"):
            self.assertIsNone(parse_cutoff(bad), f"{bad!r} should not parse")

    def test_format_emits_the_documented_form(self) -> None:
        moment = datetime(2026, 8, 29, 22, 0, tzinfo=timezone.utc)
        self.assertEqual(format_cutoff(moment), "2026-08-29T22:00Z")


class TestLedgerDateParsing(unittest.TestCase):
    """The timeline's 37 real date shapes all have to sort."""

    def test_iso_forms(self) -> None:
        self.assertEqual(parse_ledger_date("2026-08-23"), (2026, 8, 23))
        self.assertEqual(parse_ledger_date("2025-09"), (2025, 9, 0))

    def test_prose_forms(self) -> None:
        self.assertEqual(parse_ledger_date("Jan 23, 2026"), (2026, 1, 23))
        self.assertEqual(parse_ledger_date("Sept 17, 2025"), (2025, 9, 17))
        self.assertEqual(parse_ledger_date("Sept 2025"), (2025, 9, 0))
        self.assertEqual(parse_ledger_date("Aug 5–6, 2026"), (2026, 8, 5))
        self.assertEqual(parse_ledger_date("Early Mar 2025"), (2025, 3, 0))

    def test_bare_and_vague_forms(self) -> None:
        self.assertEqual(parse_ledger_date("2016"), (2016, 0, 0))
        self.assertEqual(parse_ledger_date("2023–24"), (2023, 0, 0))
        self.assertEqual(parse_ledger_date("2030s"), (2030, 0, 0))
        self.assertEqual(parse_ledger_date("2026 →"), (2026, 0, 0))
        self.assertEqual(parse_ledger_date("Mid-2024"), (2024, 6, 0))
        self.assertEqual(parse_ledger_date("Late 2022"), (2022, 10, 0))
        self.assertEqual(parse_ledger_date("Through 2028"), (2028, 12, 0))

    def test_a_bare_year_sorts_before_its_own_months(self) -> None:
        self.assertLess(parse_ledger_date("2026"), parse_ledger_date("Jan 2026"))
        self.assertLess(parse_ledger_date("Jan 2026"), parse_ledger_date("2026-01-15"))

    def test_unparseable_returns_none_rather_than_a_wrong_answer(self) -> None:
        self.assertIsNone(parse_ledger_date(""))
        self.assertIsNone(parse_ledger_date("sometime soon"))


class TestLoading(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_loads_a_valid_ledger(self) -> None:
        ledger = Ledger.load(write_ledger(self.root))
        self.assertEqual(ledger.brief_number, 2)
        self.assertEqual(len(ledger.threads), 2)
        self.assertEqual(ledger.thread_codes, {"IR", "RU"})

    def test_missing_file_refuses_rather_than_defaulting(self) -> None:
        with self.assertRaises(LedgerNotFoundError):
            Ledger.load(self.root / "nope.json")

    def test_invalid_json_is_a_parse_error(self) -> None:
        path = self.root / "intel-ledger.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(LedgerParseError):
            Ledger.load(path)

    def test_missing_required_key_refuses_to_render(self) -> None:
        """"render.py refuses to run on a ledger missing required keys (including archive)"."""
        broken = with_defect(lambda d: d.pop("archive"))
        path = write_ledger(self.root, broken)
        with self.assertRaises(LedgerSchemaError) as ctx:
            Ledger.load(path)
        self.assertIn("archive", str(ctx.exception))

    def test_wrong_container_type_refuses(self) -> None:
        broken = with_defect(lambda d: d.__setitem__("threads", {"IR": 9}))
        with self.assertRaises(LedgerSchemaError):
            Ledger.load(write_ledger(self.root, broken))

    def test_validator_can_load_a_broken_ledger_to_report_on_it(self) -> None:
        """The gate must be able to open what it is meant to describe."""
        broken = with_defect(lambda d: d.pop("archive"))
        ledger = Ledger.load(write_ledger(self.root, broken), require_schema=False)
        self.assertTrue(any("archive" in p for p in ledger.schema_problems()))


class TestNormalisation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_pre_escaped_fields_come_back_as_plain_text(self) -> None:
        """`map_nodes[].label` really does hold "ISRAEL &amp; GULF PARTNERS" in the ledger."""
        data = with_defect(
            lambda d: d["map_nodes"][0].__setitem__("label", "ISRAEL &amp; GULF PARTNERS")
        )
        ledger = Ledger.load(write_ledger(self.root, data))
        self.assertEqual(ledger.map_nodes[0].label, "ISRAEL & GULF PARTNERS")

    def test_archive_file_resolves_under_both_conventions(self) -> None:
        data = with_defect(
            lambda d: d["archive"][0].__setitem__("file", "daily-brief-2026-08-08.html")
        )
        path = write_ledger(self.root, data)
        ledger = Ledger.load(path)
        entry = ledger.archive[0]
        self.assertEqual(entry.brief_filename, "daily-brief-2026-08-08.html")
        self.assertIsNotNone(entry.resolve_file(ledger.root))

    def test_late_file_items_sort_first(self) -> None:
        ledger = Ledger.load(write_ledger(self.root))
        entry = ledger.latest_archive
        self.assertIsNotNone(entry)
        self.assertTrue(entry.sorted_items()[0].is_late_file)


class TestCitations(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.ledger = Ledger.load(write_ledger(self.root))

    def test_registry_code_resolves_to_a_url(self) -> None:
        citation = self.ledger.resolve_citation("ATA26")
        self.assertEqual(citation.kind, "registry")
        self.assertTrue(citation.url)

    def test_legacy_source_urls_registry_still_resolves(self) -> None:
        self.assertEqual(self.ledger.resolve_citation("ATA").kind, "legacy")

    def test_documented_sentinel_is_not_a_dead_reference(self) -> None:
        self.assertEqual(self.ledger.resolve_citation("PRESS").kind, "sentinel")

    def test_free_text_never_gets_an_invented_url(self) -> None:
        citation = self.ledger.resolve_citation("Reuters via AOL, 28 Aug 2026")
        self.assertEqual(citation.kind, "free-text")
        self.assertIsNone(citation.url)

    def test_unresolvable_short_code_is_dead(self) -> None:
        citation = self.ledger.resolve_citation("UKMTO")
        self.assertEqual(citation.kind, "dead")
        self.assertTrue(citation.is_dead)


class TestDerived(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.ledger = Ledger.load(write_ledger(self.root))

    def test_stats_count_what_the_pages_display(self) -> None:
        stats = self.ledger.stats()
        self.assertEqual(stats.threads, 2)
        self.assertEqual(stats.timeline_events, 2)
        self.assertEqual(stats.additions, 1)
        self.assertEqual(stats.archive_entries, 2)
        self.assertEqual(stats.node_history_entries, 1)
        self.assertEqual(stats.current_sources, 1)

    def test_node_deep_dive_is_derived_through_node_topics(self) -> None:
        events = self.ledger.events_for_node("iran")
        self.assertTrue(events)
        self.assertTrue(all(e.thread == "iran" for e in events))
        self.assertEqual(self.ledger.events_for_node("nonexistent"), [])

    def test_horizon_sorts_nearest_first(self) -> None:
        ordered = self.ledger.horizon_sorted()
        self.assertEqual(ordered[0].when, "Days")

    def test_events_merge_and_sort_chronologically(self) -> None:
        dates = [e.date for e in self.ledger.all_events()]
        self.assertEqual(dates, ["2016", "2026-08-08", "2049"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
