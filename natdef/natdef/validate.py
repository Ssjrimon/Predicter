"""``validate.py`` — the Step 6 gate.

BRIEFING-PROTOCOL.md: "Run ``validate.py`` before every delivery, not only on render days"
and "do not deliver if ``validate.py`` fails — fix the ledger and re-render instead."

Step 6 lists fifteen checks this script "enforces". **All fifteen are implemented here.**
The version this replaces implemented eleven of them and printed an explicit ``SKIPPED`` line
for the other four, which was the honest thing to do at the time — those four compare the
ledger against ``render.py``'s output, and ``render.py`` did not exist. It does now
(:mod:`natdef.render`), so the four freshness checks are real:

* event counts must match between the ledger and the rendered dashboard
* archive-entry counts must match between ``ledger.archive`` and ``brief-archive.html``
* node and edge counts must match between the ledger and ``node-map.html``
* ``index.html``'s displayed brief number must match ``ledger_meta.brief_number``

They read each page's ``natdef:counts`` meta tag — the counts the renderer declares it built
that page from — rather than scraping rendered markup. A page cannot claim a count it did
not build with, and the check does not break the next time a heading is reworded.

The fifteenth, "retired claims cannot reappear", needed a registry of what counts as
retired, which the ledger schema had no place for. It has one now: ``retired_claims[]``.
See :func:`check_retired_claims` and ``docs/REBUILD-NOTES.md``.

Exit codes: ``0`` pass (warnings allowed), ``1`` one or more failures, ``2`` the ledger could
not be loaded at all.

Usage::

    python3 -m natdef.validate                 # ledger + whatever rendered pages exist
    python3 -m natdef.validate --strict        # also fail on a source registered without a url
    python3 -m natdef.validate --check-links   # live HTTP checks on every source URL (slow)
    python3 -m natdef.validate --ledger other.json
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .errors import NatDefError
from .ledger import (
    CROSS_THREAD_SENTINEL,
    VALID_ATTRIBUTION_CLASSES,
    VALID_DIRECTIONS,
    VALID_EDGE_TYPES,
    VALID_LOG_CLASSES,
    VALID_NODE_TIERS,
    Ledger,
    default_ledger_path,
    parse_cutoff,
)

__all__ = ["Report", "run", "main"]

#: How stale a cutoff may be before the validator says so. Not a failure — a multi-day
#: catch-up is a legitimate product, it just has to be disclosed (Lookback discipline).
CUTOFF_WARN_HOURS = 48

#: ``natdef:counts`` meta tag, written by :mod:`natdef.render`.
_COUNTS_META_RE = re.compile(
    r'<meta\s+name="natdef:counts"\s+content="([^"]*)"', re.IGNORECASE
)
_BRIEF_META_RE = re.compile(
    r'<meta\s+name="natdef:brief-number"\s+content="([^"]*)"', re.IGNORECASE
)
#: Strips tags so the retired-claims sweep matches on what a reader sees, not on markup.
_TAG_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>|<[^>]+>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"\s+")


@dataclass
class Report:
    """Everything one validation run found, collected rather than raised.

    The whole ledger is checked in one pass and every problem reported together: a
    validator that stops at the first failure turns one fix-and-rerun cycle into six.
    """

    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def ok(self, message: str) -> None:
        self.passed.append(message)

    def skip(self, message: str) -> None:
        self.skipped.append(message)

    @property
    def failed(self) -> bool:
        return bool(self.failures)


# --------------------------------------------------------------------------------------
# Ledger-only checks
# --------------------------------------------------------------------------------------


def check_schema(ledger: Ledger, report: Report) -> None:
    problems = ledger.schema_problems()
    for problem in problems:
        report.fail(f"schema: {problem}")
    if not problems:
        report.ok("schema: every required key present and the right container type")


def check_threads(ledger: Ledger, report: Report) -> None:
    threads = ledger.threads
    codes = [t.code for t in threads]
    duplicates = sorted({c for c in codes if codes.count(c) > 1})
    if duplicates:
        report.fail(f"threads: duplicate thread codes {duplicates}")
    for thread in threads:
        label = thread.code or thread.id or "?"
        if not thread.intensity_is_valid:
            report.fail(
                f"threads: {label} intensity {thread.intensity!r} is not an integer in 1-10"
            )
        if not thread.direction_is_valid:
            report.fail(
                f"threads: {label} direction {thread.direction!r} is not one of "
                f"{sorted(VALID_DIRECTIONS)}"
            )
    if not duplicates and all(t.intensity_is_valid and t.direction_is_valid for t in threads):
        report.ok(
            f"threads: {len(threads)} threads, no duplicate codes, "
            "every intensity in range and every direction valid"
        )


def check_threads_match_latest_archive(ledger: Ledger, report: Report) -> None:
    """Live ``threads[]`` must equal the newest archive entry's snapshot.

    Added after the Brief 012 postmortem. Brief 011 wrote the archive snapshot and the
    brief's own prose but never wrote KP's and HL's new values into live ``threads[]``:
    Step 4.8 without Step 4.2. Anything reading ``threads[]`` served pre-Brief-011 values
    for four days and nothing caught it, because nothing diffed the two.
    """
    latest = ledger.latest_archive
    threads = ledger.threads
    if latest is None or not threads:
        report.skip("threads-vs-archive: no archive entries or no threads to compare")
        return
    snapshot = latest.threads
    if not isinstance(snapshot, dict) or not snapshot:
        report.fail(
            f"threads-vs-archive: archive #{latest.number} has no usable threads snapshot"
        )
        return
    mismatches: list[str] = []
    for thread in threads:
        if thread.code not in snapshot:
            # A thread opened after the newest archive entry has nothing to compare against
            # yet; that is legitimate on the day a thread is opened.
            report.warn(
                f"threads-vs-archive: {thread.code} is not in archive #{latest.number}'s "
                "snapshot (a newly opened thread, or a skipped Step 4.8)"
            )
            continue
        want = snapshot[thread.code]
        if not (isinstance(want, (list, tuple)) and len(want) == 2):
            report.fail(
                f"threads-vs-archive: archive #{latest.number} snapshot for {thread.code} "
                f"is malformed: {want!r}"
            )
            continue
        if [thread.intensity, thread.direction] != list(want):
            mismatches.append(
                f"{thread.code}: live {thread.intensity}/{thread.direction} but "
                f"archive #{latest.number} says {want[0]}/{want[1]}"
            )
    for mismatch in mismatches:
        report.fail(
            f"threads[] out of sync with the newest archive entry — {mismatch}. "
            "This is Step 4.2 done without Step 4.8, or the reverse."
        )
    if not mismatches:
        report.ok(
            f"threads-vs-archive: every thread matches archive #{latest.number}'s snapshot"
        )


def check_sources(ledger: Ledger, report: Report) -> None:
    sources = ledger.sources
    by_id = {s.id: s for s in sources}
    superseded = 0
    for source in sources:
        if source.is_superseded:
            superseded += 1
            if not source.superseded_by:
                report.fail(f"sources: {source.id!r} is superseded but names no superseded_by")
            elif source.superseded_by not in by_id:
                report.fail(
                    f"sources: {source.id!r} superseded_by {source.superseded_by!r} "
                    "does not resolve to another source"
                )
        if not source.url:
            report.warn(f"sources: {source.id!r} has no url")
        if source.attribution_class and source.attribution_class not in VALID_ATTRIBUTION_CLASSES:
            report.fail(
                f"sources: {source.id!r} attribution_class {source.attribution_class!r} invalid"
            )
    report.ok(
        f"sources: {len(sources)} documents, {superseded} superseded, "
        "every superseded_by resolves"
    )


def check_citations(ledger: Ledger, report: Report, *, strict: bool) -> None:
    """Every citation must resolve to a registered source.

    Step 6: "every timeline citation resolves to a URL — a dead link fails the build."

    Five outcomes, treated differently because they need different fixes:

    * **registry / legacy** — resolves to a URL. Fine.
    * **sentinel** (``PRESS``) — documented to have no single URL, because there is no one
      document to point at. Reported once, never a failure, in strict mode either: it is a
      deliberate design, not an unfinished job.
    * **registered-no-url** — resolves to a ``sources[]`` entry that carries no URL. A
      disclosed gap: the source is identified, its address was not recovered. Warned by
      default, failed under ``--strict``.
    * **free text** ("Reuters via AOL, 28 Aug 2026") — registered nowhere, so the ledger
      alone cannot reconstruct what was cited. **This is a failure by default.** It was a
      warning until the 6 September 2026 backfill registered all 23 historical free-text
      citations; with none left, warning about it would only let a new one slip in.
    * **dead** — looks like a registry code and resolves nowhere. Always a failure.
    """
    dead: list[str] = []
    free_text: list[str] = []
    no_url: list[str] = []
    sentinel = 0
    resolved = 0
    for array, index, raw, citation in ledger.iter_citations():
        if citation.is_dead:
            dead.append(f"{array}[{index}] src {raw!r}")
        elif citation.kind == "free-text":
            free_text.append(f"{array}[{index}] src {raw!r}")
        elif citation.kind == "registered-no-url":
            no_url.append(f"{array}[{index}] src {raw!r}")
        elif citation.kind == "sentinel":
            sentinel += 1
        else:
            resolved += 1

    for item in dead:
        report.fail(
            f"citations: {item} looks like a registry code but resolves in neither "
            "sources[].id nor source_urls{} — a dead reference"
        )
    for item in free_text:
        report.fail(
            f"citations: {item} is an inline free-text citation, registered nowhere. "
            "Register it in sources[] (see the 2026-09-06 backfill for the pattern) so the "
            "ledger alone can reconstruct what was cited."
        )
    for item in no_url:
        message = (
            f"citations: {item} resolves to a sources[] entry that carries no url — the "
            "source is identified but its address was never recovered"
        )
        report.fail(message) if strict else report.warn(message)
    if sentinel:
        report.warn(
            f"citations: {sentinel} use(s) of the documented generic-press sentinel, which "
            "has no single URL by design and is not a gap to close"
        )
    if not dead and not free_text:
        report.ok(
            f"citations: {resolved} resolve to a URL, {len(no_url)} registered without one, "
            f"{sentinel} documented sentinel, 0 free-text, 0 dead references"
        )


def check_cutoff(ledger: Ledger, report: Report, *, now: datetime | None = None) -> None:
    cutoff = ledger.last_cutoff
    moment = parse_cutoff(cutoff)
    if moment is None:
        report.fail(
            f"cutoff: ledger_meta.last_cutoff {cutoff!r} does not parse "
            "(want YYYY-MM-DDTHH:MMZ or YYYY-MM-DDTHHMMZ)"
        )
        return
    reference = now or datetime.now(timezone.utc)
    age_hours = (reference - moment).total_seconds() / 3600
    if age_hours < 0:
        report.fail(f"cutoff: last_cutoff {cutoff} is in the future")
        return
    if age_hours > CUTOFF_WARN_HOURS:
        report.warn(
            f"cutoff: last_cutoff {cutoff} is {age_hours:.0f}h old — the next brief is a "
            "multi-day catch-up and must say so on its masthead"
        )
    report.ok(f"cutoff: {cutoff} parses cleanly ({age_hours:.1f}h old)")


def check_archive(ledger: Ledger, report: Report) -> None:
    entries = ledger.archive
    if not entries:
        report.fail("archive: archive[] is empty — every brief gets an entry (Step 4.8)")
        return

    numbers = [e.number for e in entries]
    expected = list(range(1, len(numbers) + 1))
    if sorted(numbers) != expected:
        report.fail(
            f"archive: numbering is not sequential from 1 with no gaps — got {sorted(numbers)}"
        )
    dates = [e.date for e in entries]
    duplicate_dates = sorted({d for d in dates if dates.count(d) > 1})
    if duplicate_dates:
        report.fail(f"archive: duplicate dates {duplicate_dates}")

    valid_codes = ledger.thread_codes | {CROSS_THREAD_SENTINEL}
    filed: set[str] = set()
    for entry in entries:
        for item in entry.items:
            if item.thread not in valid_codes:
                report.fail(
                    f"archive: #{entry.number} item {item.n} has unknown thread code "
                    f"{item.thread!r}"
                )
        if not isinstance(entry.threads, dict) or not entry.threads:
            report.fail(f"archive: #{entry.number} has no threads snapshot")
        else:
            for code, value in entry.threads.items():
                if code not in ledger.thread_codes:
                    report.fail(f"archive: #{entry.number} snapshot has unknown code {code!r}")
                elif not (
                    isinstance(value, (list, tuple))
                    and len(value) == 2
                    and isinstance(value[0], int)
                    and value[1] in VALID_DIRECTIONS
                ):
                    report.fail(
                        f"archive: #{entry.number} snapshot for {code!r} is malformed: {value!r}"
                    )
        resolved = entry.resolve_file(ledger.root)
        if not entry.file:
            report.fail(f"archive: #{entry.number} names no file")
        elif resolved is None:
            report.fail(
                f"archive: #{entry.number} file {entry.file!r} does not exist on disk"
            )
        else:
            filed.add(entry.brief_filename)
            if entry.file == entry.brief_filename:
                report.warn(
                    f"archive: #{entry.number} file {entry.file!r} has no 'briefs/' prefix "
                    "(the older of the two conventions; both are accepted)"
                )
        if not parse_cutoff(entry.cutoff):
            report.fail(f"archive: #{entry.number} cutoff {entry.cutoff!r} does not parse")

    # The other direction: a delivered brief with no archive entry is exactly the skipped
    # Step 4.8 the protocol calls a defect.
    for path in ledger.brief_files_on_disk():
        if path.name not in filed:
            report.fail(
                f"archive: {path.name} is on disk with no archive[] entry — Step 4.8 was skipped"
            )

    if not report.failures:
        report.ok(
            f"archive: {len(entries)} entries, sequential from 1, no duplicate dates, "
            "every thread code valid, every file on disk, every delivered brief accounted for"
        )


def check_nodes(ledger: Ledger, report: Report) -> None:
    node_ids = ledger.node_ids
    edges = ledger.node_edges
    for index, edge in enumerate(edges):
        if edge.frm not in node_ids:
            report.fail(f"node_edges[{index}]: 'from' {edge.frm!r} is not a map_nodes id")
        if edge.to not in node_ids:
            report.fail(f"node_edges[{index}]: 'to' {edge.to!r} is not a map_nodes id")
        if edge.frm and edge.frm == edge.to:
            report.fail(f"node_edges[{index}]: self-referential edge on {edge.frm!r}")
        if edge.type not in VALID_EDGE_TYPES:
            report.fail(
                f"node_edges[{index}]: type {edge.type!r} is not one of {sorted(VALID_EDGE_TYPES)}"
            )

    history = ledger.node_history
    total = 0
    for node_id, entries in history.items():
        if node_id not in node_ids:
            report.fail(f"node_history: key {node_id!r} is not a map_nodes id")
            continue
        for index, entry in enumerate(entries):
            total += 1
            missing = [f for f in ("date", "title", "text") if not getattr(entry, f)]
            if missing:
                report.fail(f"node_history[{node_id!r}][{index}]: missing {missing}")
            if entry.tier not in VALID_NODE_TIERS:
                report.fail(
                    f"node_history[{node_id!r}][{index}]: tier {entry.tier!r} is not one of "
                    f"{sorted(VALID_NODE_TIERS)}"
                )
            if not entry.source_title:
                report.warn(f"node_history[{node_id!r}][{index}]: no source_title")

    orphans = sorted(node_ids - set(ledger.node_topics))
    if orphans:
        report.warn(
            f"node_topics: {len(orphans)} node(s) map to no topic codes, so their deep dive "
            f"has no derived timeline: {orphans}"
        )
    report.ok(
        f"node map: {len(node_ids)} nodes, {len(edges)} edges all resolvable and typed, "
        f"{total} node_history entries all dated, titled and tiered"
    )


def check_attribution_classes(ledger: Ledger, report: Report) -> None:
    bad = 0
    for index, event in enumerate(ledger.timeline_additions):
        if event.attribution_class and event.attribution_class not in VALID_ATTRIBUTION_CLASSES:
            report.fail(
                f"timeline_additions_2026[{index}]: attribution_class "
                f"{event.attribution_class!r} invalid"
            )
            bad += 1
    for index, entry in enumerate(ledger.verification_log):
        value = entry.get("class")
        if value is not None and value not in VALID_LOG_CLASSES:
            report.fail(f"verification_log[{index}]: class {value!r} invalid")
            bad += 1
    if not bad:
        report.ok("attribution: every attribution_class and verification_log class is valid")


# --------------------------------------------------------------------------------------
# Checks against render.py's output
# --------------------------------------------------------------------------------------


def _page_counts(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """``(counts, error)`` read from a rendered page's ``natdef:counts`` meta tag."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"could not be read: {exc}"
    match = _COUNTS_META_RE.search(text)
    if match is None:
        return None, "carries no natdef:counts meta tag — was it generated by render.py?"
    try:
        counts = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        return None, f"natdef:counts is not valid JSON: {exc}"
    if not isinstance(counts, dict):
        return None, "natdef:counts is not a JSON object"
    return counts, None


def check_rendered_pages(ledger: Ledger, report: Report) -> None:
    """The four freshness checks Step 6 requires, against ``render.py``'s real output.

    A page that does not exist is skipped, not failed: a working tree mid-rebuild is a
    legitimate state and ``render.py`` is the fix, not a validator error. A page that
    exists but disagrees with the ledger is a failure — that is drift, and it is the exact
    condition these checks exist to catch.
    """
    stats = ledger.stats()
    expectations: dict[str, dict[str, int]] = {
        "strategic-threat-briefing.html": {
            "timeline_events": stats.timeline_events + stats.additions,
            "threads": stats.threads,
            "sources": stats.total_sources,
            "briefings": stats.briefings,
            "map_nodes": stats.map_nodes,
            "node_edges": stats.node_edges,
            "horizon": stats.horizon,
            "revisions": stats.revisions,
        },
        "brief-archive.html": {
            "archive_entries": stats.archive_entries,
            "threads": stats.threads,
        },
        "node-map.html": {
            "map_nodes": stats.map_nodes,
            "node_edges": stats.node_edges,
            "node_history_entries": stats.node_history_entries,
        },
        "index.html": {
            "brief_number": stats.brief_number,
            "threads": stats.threads,
            "archive_entries": stats.archive_entries,
        },
    }

    checked = 0
    for filename, expected in expectations.items():
        path = ledger.root / filename
        if not path.is_file():
            report.skip(
                f"rendered {filename}: not present — run `python3 -m natdef.render` to generate it"
            )
            continue
        counts, error = _page_counts(path)
        if counts is None:
            report.fail(f"rendered {filename}: {error}")
            continue
        drifted = False
        for key, want in expected.items():
            got = counts.get(key)
            if got != want:
                report.fail(
                    f"rendered {filename}: {key} is {got!r} but the ledger says {want!r} — "
                    "the page is behind the ledger; re-run render.py"
                )
                drifted = True
        # Step 6 calls out index.html's brief number specifically, and every page carries
        # it, so check it on all of them.
        declared = _BRIEF_META_RE.search(path.read_text(encoding="utf-8"))
        if declared is None:
            report.fail(f"rendered {filename}: no natdef:brief-number meta tag")
            drifted = True
        elif declared.group(1) != str(stats.brief_number):
            report.fail(
                f"rendered {filename}: displays brief number {declared.group(1)!r} but "
                f"ledger_meta.brief_number is {stats.brief_number}"
            )
            drifted = True
        if not drifted:
            checked += 1

    if checked:
        report.ok(
            f"rendered output: {checked} page(s) agree with the ledger on every count and "
            "on the brief number"
        )


# --------------------------------------------------------------------------------------
# Retired claims
# --------------------------------------------------------------------------------------


def _visible_text(html_text: str) -> str:
    """Strip scripts, styles and tags, leaving roughly what a reader sees."""
    stripped = _TAG_RE.sub(" ", html_text)
    return _WS_RE.sub(" ", html.unescape(stripped))


def _sweep_targets(ledger: Ledger) -> list[Path]:
    """Everything the retired-claims sweep reads.

    Step 6: "swept across the dashboard, the archive, and every ``daily-brief-*.html`` on
    disk, not just the dashboard."
    """
    targets: list[Path] = []
    for filename in (
        "index.html",
        "strategic-threat-briefing.html",
        "brief-archive.html",
        "node-map.html",
    ):
        path = ledger.root / filename
        if path.is_file():
            targets.append(path)
    targets.extend(ledger.brief_files_on_disk())
    return targets


def check_retired_claims(ledger: Ledger, report: Report) -> None:
    """"Retired claims cannot reappear" — the check Step 6 required and nothing implemented.

    It was absent for a real reason: it needs a definition of what counts as retired, and
    the ledger schema had nowhere to record one. ``sources[].status: superseded`` tracks a
    retired *document*; nothing tracked a retired *claim*. ``retired_claims[]`` is that
    registry.

    Two things keep the sweep from crying wolf on the operation's own honest record:

    * **A brief filed on or before the retirement date is exempt.** Delivered briefs are
      never rewritten (that is the whole point of the archive), so the brief that made a
      claim necessarily still contains it. Only output produced *after* the claim was
      retired is in scope.
    * **``exempt_files``** names anything else that legitimately quotes the claim — the
      brief that issued the correction, and any preserved retraction notice.

    A match is a failure with the surrounding text quoted, so whoever fixes it can see
    exactly what tripped and judge whether the pattern or the page is wrong.
    """
    claims = ledger.retired_claims
    if not claims:
        report.ok(
            "retired claims: registry is empty, so nothing can reappear "
            "(retired_claims[] exists and is swept; it is not disabled)"
        )
        return

    targets = _sweep_targets(ledger)
    if not targets:
        report.skip("retired claims: no rendered pages or briefs on disk to sweep")
        return

    cache: dict[Path, str] = {}
    hits = 0
    for claim in claims:
        for pattern, error in claim.invalid_patterns():
            report.fail(
                f"retired claims: {claim.id!r} pattern {pattern!r} is not a valid regex: {error}"
            )
        compiled = claim.compiled_patterns()
        if not compiled:
            report.warn(
                f"retired claims: {claim.id!r} has no usable patterns, so it is not enforced"
            )
            continue
        retired_on = claim.retired_on
        for path in targets:
            name = path.name
            if name in claim.exempt_files:
                continue
            # Preserved retraction notices exist to hold the retracted claim.
            if name.startswith("RETRACTED-"):
                continue
            brief_date = _brief_date(name)
            if brief_date is not None and retired_on and brief_date <= retired_on:
                continue
            if path not in cache:
                try:
                    cache[path] = _visible_text(path.read_text(encoding="utf-8"))
                except OSError as exc:
                    report.warn(f"retired claims: could not read {name}: {exc}")
                    cache[path] = ""
            text = cache[path]
            for regex in compiled:
                match = regex.search(text)
                if match is not None:
                    start = max(0, match.start() - 90)
                    excerpt = text[start : match.end() + 90].strip()
                    report.fail(
                        f"retired claims: {name} contains {claim.id!r}, retired "
                        f"{retired_on or '(undated)'} — {claim.reason or 'no reason recorded'}. "
                        f"Matched: …{excerpt}…"
                    )
                    hits += 1
                    break

    if not hits:
        report.ok(
            f"retired claims: {len(claims)} registered claim(s) swept across "
            f"{len(targets)} file(s); none reappeared"
        )


def _brief_date(filename: str) -> str | None:
    """``2026-08-25`` from ``daily-brief-2026-08-25.html``, else ``None``."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None


# --------------------------------------------------------------------------------------
# Optional: live link checking
# --------------------------------------------------------------------------------------


def check_links_live(ledger: Ledger, report: Report, *, timeout: float = 8.0) -> None:
    """Probe every source URL. Off by default because it is slow and network-flaky.

    A 404 or a 5xx is a dead link and fails. Anything else — a timeout, a 403 from a server
    that dislikes HEAD, a TLS quirk — is a warning: an unreachable network must not be able
    to fail a brief that is otherwise correct.
    """
    urls = sorted({s.url for s in ledger.sources if s.url})
    urls += sorted(set(ledger.source_urls.values()) - set(urls))
    print(f"validate: probing {len(urls)} source URL(s) — this is slow", file=sys.stderr)
    dead = 0
    for url in urls:
        request = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": "natdef-validate/2.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status >= 400:
                    report.fail(f"links: HTTP {response.status} for {url}")
                    dead += 1
        except urllib.error.HTTPError as exc:
            if exc.code == 404 or exc.code >= 500:
                report.fail(f"links: HTTP {exc.code} for {url}")
                dead += 1
            else:
                report.warn(f"links: HTTP {exc.code} for {url} (may be HEAD-unfriendly)")
        except Exception as exc:  # noqa: BLE001 — any transport failure is informational
            report.warn(f"links: could not reach {url} ({exc})")
    if not dead:
        report.ok(f"links: {len(urls)} URL(s) probed, none returned 404 or 5xx")


# --------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------


def run(
    ledger: Ledger,
    *,
    strict: bool = False,
    check_links: bool = False,
    now: datetime | None = None,
) -> Report:
    """Run every check and return the collected report."""
    report = Report()
    check_schema(ledger, report)
    check_threads(ledger, report)
    check_threads_match_latest_archive(ledger, report)
    check_sources(ledger, report)
    check_citations(ledger, report, strict=strict)
    check_cutoff(ledger, report, now=now)
    check_archive(ledger, report)
    check_nodes(ledger, report)
    check_attribution_classes(ledger, report)
    check_rendered_pages(ledger, report)
    check_retired_claims(ledger, report)
    if check_links:
        check_links_live(ledger, report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description="The Step 6 gate. Run before every delivery; do not deliver on a failure.",
    )
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail on a citation that resolves to a sources[] entry carrying no url "
        "(a disclosed gap). Free-text and dead citations fail in both modes.",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="also probe every source URL over the network (slow)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="print only the summary line and any failures"
    )
    args = parser.parse_args(argv)

    ledger_path = args.ledger or default_ledger_path()
    try:
        # Loaded without the schema gate so that a structurally broken ledger is *reported*
        # rather than raising before any check can run. check_schema does the reporting.
        ledger = Ledger.load(ledger_path, require_schema=False)
    except NatDefError as exc:
        print(f"validate: {exc}", file=sys.stderr)
        return 2

    report = run(ledger, strict=args.strict, check_links=args.check_links)

    print(
        f"validate.py — {len(report.passed)} check group(s) passed, "
        f"{len(report.warnings)} warning(s), {len(report.skipped)} skipped, "
        f"{len(report.failures)} failure(s)\n"
    )
    if report.passed and not args.quiet:
        print("PASS")
        for message in report.passed:
            print(f"  - {message}")
    if report.skipped and not args.quiet:
        print("\nSKIPPED")
        for message in report.skipped:
            print(f"  - {message}")
    if report.warnings and not args.quiet:
        print("\nWARNINGS (non-fatal)")
        for message in report.warnings:
            print(f"  - {message}")
    if report.failures:
        print("\nFAILURES")
        for message in report.failures:
            print(f"  - {message}")
        print(
            f"\nvalidate.py: FAIL ({len(report.failures)} failure(s)) — "
            "do not deliver. Fix the ledger and re-run."
        )
        return 1

    print("\nvalidate.py: PASS")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
