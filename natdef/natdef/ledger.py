"""The one place ``intel-ledger.json`` is parsed.

BRIEFING-PROTOCOL.md, Step 1: "The ledger is the source of truth. Both the dashboard and
the briefs are generated from it." Every other module in this package goes through
:class:`Ledger` rather than calling ``json.load`` itself, so that the ledger's real,
sometimes messy history is normalised in exactly one place instead of being re-derived
(and re-guessed) by four renderers.

Three pieces of that history are load-bearing and are handled here rather than at the
call sites:

* **Two cutoff formats.** ``2026-08-25T04:00Z`` (every brief but 12) and
  ``2026-08-29T2200Z`` (Brief 12). Same instant, different string. :func:`parse_cutoff`
  accepts both; :func:`format_cutoff` emits the documented ``HH:MM`` form for anything
  written from here on.
* **Two ``archive[].file`` conventions.** A bare filename for Briefs 1-11, a ``briefs/``
  prefix for Brief 12. :meth:`ArchiveEntry.brief_filename` normalises to the basename and
  :meth:`ArchiveEntry.resolve_file` finds it either way.
* **Two citation styles.** Short registry codes resolved against ``sources[]`` /
  ``source_urls{}``, and inline free text ("Reuters via AOL, 28 Aug 2026") that resolves
  against nothing. :meth:`Ledger.resolve_citation` reports which of the two a given
  ``src[]`` value is, and never invents a URL for the second.

Objects here are deliberately thin wrappers that keep ``.raw`` around. A renderer that
needs a field this module does not model reads it from ``.raw`` — nothing in the ledger is
silently dropped on the way through.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .errors import LedgerNotFoundError, LedgerParseError, LedgerSchemaError

__all__ = [
    "VALID_DIRECTIONS",
    "VALID_ATTRIBUTION_CLASSES",
    "VALID_LOG_CLASSES",
    "VALID_NODE_TIERS",
    "VALID_EDGE_TYPES",
    "CROSS_THREAD_SENTINEL",
    "KNOWN_GENERIC_SENTINELS",
    "Citation",
    "Thread",
    "Source",
    "ArchiveItem",
    "ArchiveEntry",
    "MapNode",
    "NodeEdge",
    "NodeHistoryEntry",
    "HorizonItem",
    "TimelineEvent",
    "RetiredClaim",
    "LedgerStats",
    "Ledger",
    "parse_cutoff",
    "parse_ledger_date",
    "format_cutoff",
]


# --------------------------------------------------------------------------------------
# Controlled vocabularies. These are the ledger's schema, expressed once.
# --------------------------------------------------------------------------------------

#: BRIEFING-PROTOCOL.md, "The ten threads". ``volatile`` means large movement without a
#: consistent direction and is explicitly *not* a hedge.
VALID_DIRECTIONS: frozenset[str] = frozenset({"escalating", "holding", "easing", "volatile"})

#: BRIEFING-PROTOCOL.md, Step 3, point 6.
VALID_ATTRIBUTION_CLASSES: frozenset[str] = frozenset(
    {"verified-primary", "attributed-claim", "contested", "single-source", "analyst-judgment"}
)

#: ``verification_log[].class`` additionally uses ``incomplete`` — an established sentinel
#: (first used 2026-08-08 for ATA26 gap-tracking) for a log entry that flags unfinished
#: work rather than adjudicating a claim. Not a data error.
VALID_LOG_CLASSES: frozenset[str] = VALID_ATTRIBUTION_CLASSES | {"incomplete"}

#: ``node_history[].tier`` uses a smaller, separate vocabulary — BRIEFING-PROTOCOL.md
#: Step 4.7. ``reference`` means general historical record not re-verified this sweep.
VALID_NODE_TIERS: frozenset[str] = frozenset({"verified-primary", "attributed-claim", "reference"})

#: ``node_edges[].type`` — BRIEFING-PROTOCOL.md, Step 1 table.
VALID_EDGE_TYPES: frozenset[str] = frozenset(
    {"alliance", "adversarial-cooperation", "conflict", "contested", "hemisphere"}
)

#: A formally allow-listed sentinel thread code for archive items that genuinely span
#: several threads or report "nothing moved" across several at once (Brief 002 item 05).
#: BRIEFING-PROTOCOL.md, "Cross-thread archive items". Do not "fix" this to a real code.
CROSS_THREAD_SENTINEL: str = "—"  # em dash

#: ``PRESS`` means "general contemporaneous press reporting, no single canonical primary
#: document". It is absent from ``source_urls{}`` because there is no one URL to put
#: there, not because it was missed. Three pre-2026 uses.
KNOWN_GENERIC_SENTINELS: frozenset[str] = frozenset({"PRESS"})

#: Keys that must be lists, and must exist for the renderer to run at all.
REQUIRED_LIST_KEYS: tuple[str, ...] = (
    "sources",
    "threads",
    "timeline",
    "timeline_additions_2026",
    "horizon",
    "archive",
    "map_nodes",
    "node_edges",
    "briefings",
)

#: Keys that must be lists when present, but whose absence is survivable.
OPTIONAL_LIST_KEYS: tuple[str, ...] = (
    "revisions",
    "standing_watchlist",
    "verification_log",
    "schema_notes",
    "retired_claims",
)

#: Keys that must be JSON objects when present.
DICT_KEYS: tuple[str, ...] = ("ledger_meta", "categories", "source_urls", "node_topics", "node_history")

#: ``ledger_meta`` fields the renderer cannot sensibly substitute a default for.
REQUIRED_META_KEYS: tuple[str, ...] = ("title", "brief_number", "last_cutoff", "last_updated")

#: Accepts both real cutoff spellings. See the module docstring.
CUTOFF_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):?(\d{2})Z$")

#: A ``src[]`` value that *looks* like it was meant to resolve against a registry. Anything
#: matching this and resolving nowhere is a dead reference; anything not matching it is
#: read as an inline free-text citation instead.
SHORT_CODE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{1,11}$")


def parse_cutoff(value: str | None) -> datetime | None:
    """Parse an information cutoff in either real format. ``None`` if it does not parse.

    Returns an aware UTC datetime. Callers must treat ``None`` as "malformed" and say so,
    never as "no cutoff" — a brief without a parseable cutoff has no contract with its
    reader (BRIEFING-PROTOCOL.md, "Lookback discipline").
    """
    if not value:
        return None
    m = CUTOFF_RE.match(value)
    if m is None:
        return None
    date_part, hh, mm = m.groups()
    try:
        parsed = datetime.strptime(f"{date_part}T{hh}:{mm}Z", "%Y-%m-%dT%H:%MZ")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def format_cutoff(moment: datetime) -> str:
    """Render a cutoff in the documented ``YYYY-MM-DDTHH:MMZ`` form.

    Historical entries are never rewritten to match (BRIEFING-PROTOCOL.md forbids editing
    delivered records); this is only for cutoffs minted from here on.
    """
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


#: Month-name prefixes as they actually appear in the ledger, including the ``Sept``
#: spelling that ``%b`` will not parse.
_MONTHS: dict[str, int] = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

#: Vague period qualifiers, mapped to the month they sort at. These are ordering hints
#: only — nothing displays a month the ledger did not state.
_PERIOD_HINTS: tuple[tuple[str, int], ...] = (
    ("early", 2), ("mid", 6), ("late", 10), ("fall", 9), ("autumn", 9),
    ("spring", 4), ("summer", 7), ("winter", 12), ("through", 12),
)

#: A trailing ``\b`` would miss ``2030s`` (decade shorthand, used once in the timeline),
#: since ``0`` and ``s`` are both word characters. A negative lookahead for another digit
#: keeps ``20301`` from being read as ``2030`` while letting the decade form through.
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})(?!\d)")
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})(?:-(\d{2}))?")
_MONTH_DAY_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b",
    re.IGNORECASE,
)
_MONTH_ONLY_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\b", re.IGNORECASE
)


def parse_ledger_date(text: str | None) -> tuple[int, int, int] | None:
    """Sortable ``(year, month, day)`` for a ledger date of any real shape, or ``None``.

    ``timeline[].d`` and ``timeline_additions_2026[].date`` hold 37 distinct date shapes
    across this ledger's history — ISO dates, bare years, ``Jan 23, 2026``, ``Sept 2025``,
    ``Aug 5-6, 2026``, ``2023-24``, ``Mid-2024``, ``Through 2028``, ``2030s``. A strict
    parser drops roughly 40% of the timeline into an "unparseable" bucket that then renders
    in arbitrary order, which is what makes a chronology stop being one.

    Missing components resolve to ``0``, so a bare year sorts immediately before its own
    months rather than after them. A vague period ("Late 2022", "Fall 2025") resolves to the
    month named in :data:`_PERIOD_HINTS` *for ordering only* — the page always displays the
    ledger's own string, never this interpretation of it.

    Returns ``None`` only when no year can be found at all, which the caller must handle as
    "sorts last", not as a crash.
    """
    if not text:
        return None
    raw = str(text).strip()
    lowered = raw.lower()

    iso = _ISO_RE.search(raw)
    if iso is not None:
        year, month, day = iso.groups()
        return (int(year), int(month), int(day or 0))

    year_match = _YEAR_RE.search(raw)
    if year_match is None:
        return None
    year = int(year_match.group(1))

    month_day = _MONTH_DAY_RE.search(raw)
    if month_day is not None:
        name, day = month_day.groups()
        month = _MONTHS.get(name.lower(), 0)
        # Guard a day number that is really part of a range or a year fragment.
        day_int = int(day)
        return (year, month, day_int if 1 <= day_int <= 31 else 0)

    month_only = _MONTH_ONLY_RE.search(raw)
    if month_only is not None:
        return (year, _MONTHS.get(month_only.group(1).lower(), 0), 0)

    for hint, month in _PERIOD_HINTS:
        if hint in lowered:
            return (year, month, 0)

    return (year, 0, 0)


def _text(value: Any) -> str:
    """Normalise a ledger string field to plain text.

    Several ledger fields were authored by hand directly into HTML and carry entities even
    though they are otherwise plain text — ``map_nodes[].label`` holds
    ``"ISRAEL &amp; GULF PARTNERS"``, and a number of ``timeline[].t`` titles do the same.
    Anything read through this module comes out as text, so a consumer can escape it once
    for HTML or hand it to ``textContent`` in a page script and get the same characters
    either way. ``briefings[].html`` deliberately does not pass through here: it is authored
    as markup and is read from the raw dict.
    """
    if value is None:
        return ""
    return html.unescape(str(value))


# --------------------------------------------------------------------------------------
# Row types
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Citation:
    """The outcome of resolving one ``src[]`` value.

    ``kind`` is one of:

    ``registry``    Resolved to a ``sources[]`` entry with a URL.
    ``legacy``      Resolved via the older ``source_urls{}`` shorthand dict.
    ``sentinel``    A documented generic sentinel (``PRESS``) with no single URL.
    ``free-text``   An inline citation ("Reuters via AOL, 28 Aug 2026"). Real, but not
                    registered anywhere, so no URL can be recovered from the ledger alone.
    ``dead``        Looks like a registry code and resolves nowhere. A defect.
    """

    raw: str
    kind: str
    url: str | None = None
    title: str | None = None

    @property
    def is_dead(self) -> bool:
        return self.kind == "dead"

    @property
    def is_resolved(self) -> bool:
        return self.kind in {"registry", "legacy"}

    def label(self) -> str:
        """Human-facing text for this citation, preferring a real title over the code."""
        return self.title or self.raw


@dataclass(frozen=True)
class Thread:
    """One of the ten tracked threads."""

    code: str
    id: str
    label: str
    intensity: int
    direction: str
    status: str
    one_line: str
    watch: tuple[str, ...]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "Thread":
        intensity = raw.get("intensity")
        return cls(
            code=_text(raw.get("code")),
            id=_text(raw.get("id")),
            label=_text(raw.get("label")) or _text(raw.get("code")),
            intensity=intensity if isinstance(intensity, int) else -1,
            direction=_text(raw.get("direction")),
            status=_text(raw.get("status")),
            one_line=_text(raw.get("one_line")),
            watch=tuple(str(w) for w in (raw.get("watch") or [])),
            raw=raw,
        )

    @property
    def intensity_is_valid(self) -> bool:
        return isinstance(self.intensity, int) and 1 <= self.intensity <= 10

    @property
    def direction_is_valid(self) -> bool:
        return self.direction in VALID_DIRECTIONS


@dataclass(frozen=True)
class Source:
    """A primary or tracked document in ``sources[]``."""

    id: str
    title: str
    publisher: str
    published: str
    url: str | None
    status: str
    superseded_by: str | None
    tier: str | None
    note: str
    attribution_class: str | None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "Source":
        return cls(
            id=_text(raw.get("id")),
            title=_text(raw.get("title")),
            publisher=_text(raw.get("publisher")),
            published=_text(raw.get("published")),
            url=(_text(raw["url"]) if raw.get("url") else None),
            status=_text(raw.get("status")),
            superseded_by=(_text(raw["superseded_by"]) if raw.get("superseded_by") else None),
            tier=(_text(raw["tier"]) if raw.get("tier") else None),
            note=_text(raw.get("note")),
            attribution_class=(
                _text(raw["attribution_class"]) if raw.get("attribution_class") else None
            ),
            raw=raw,
        )

    @property
    def is_superseded(self) -> bool:
        return self.status == "superseded"

    @property
    def is_current(self) -> bool:
        return self.status == "current"


@dataclass(frozen=True)
class ArchiveItem:
    """One numbered item inside an archive entry: headline plus its So-what."""

    n: str
    thread: str
    head: str
    sowhat: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "ArchiveItem":
        return cls(
            n=str(raw.get("n") if raw.get("n") is not None else ""),
            thread=_text(raw.get("thread")),
            head=_text(raw.get("head")),
            sowhat=_text(raw.get("sowhat")),
            raw=raw,
        )

    @property
    def is_late_file(self) -> bool:
        """Late-file items carry an ``LF``-prefixed number and run first (Step 5, point 4)."""
        return self.n.upper().startswith("LF")


@dataclass(frozen=True)
class ArchiveEntry:
    """One brief's permanent record: ``archive[]``, written in Step 4.8."""

    number: int
    date: str
    weekday: str
    file: str
    cutoff: str
    revision: str
    bottom_line: str
    threads: Mapping[str, Sequence[Any]]
    items: tuple[ArchiveItem, ...]
    changed: tuple[str, ...]
    verification: Mapping[str, Any]
    headline_correction: str | None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "ArchiveEntry":
        number = raw.get("number")
        changed_raw = raw.get("changed") or []
        # `changed` is a list of strings in every real entry, but a single string would be
        # an easy hand-edit slip; normalise rather than crash a renderer downstream.
        if isinstance(changed_raw, str):
            changed: tuple[str, ...] = (changed_raw,)
        else:
            changed = tuple(str(c) for c in changed_raw)
        verification = raw.get("verification")
        return cls(
            number=number if isinstance(number, int) else -1,
            date=_text(raw.get("date")),
            weekday=_text(raw.get("weekday")),
            file=_text(raw.get("file")),
            cutoff=_text(raw.get("cutoff")),
            revision=_text(raw.get("revision")),
            bottom_line=_text(raw.get("bottom_line")),
            threads=raw.get("threads") if isinstance(raw.get("threads"), dict) else {},
            items=tuple(
                ArchiveItem.from_raw(i) for i in (raw.get("items") or []) if isinstance(i, dict)
            ),
            changed=changed,
            verification=verification if isinstance(verification, dict) else {},
            headline_correction=(
                _text(raw["headline_correction"]) if raw.get("headline_correction") else None
            ),
            raw=raw,
        )

    @property
    def brief_filename(self) -> str:
        """The basename, whichever of the two ``file`` conventions this entry uses."""
        return Path(self.file).name if self.file else ""

    def resolve_file(self, root: Path) -> Path | None:
        """Find this entry's brief on disk, trying both conventions. ``None`` if missing."""
        if not self.file:
            return None
        for candidate in (root / self.file, root / "briefs" / self.brief_filename):
            if candidate.is_file():
                return candidate
        return None

    @property
    def cutoff_datetime(self) -> datetime | None:
        return parse_cutoff(self.cutoff)

    @property
    def date_datetime(self) -> datetime | None:
        try:
            return datetime.strptime(self.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

    def sorted_items(self) -> tuple[ArchiveItem, ...]:
        """Late-file items first, per Step 5 point 4, then in ledger order."""
        return tuple(sorted(self.items, key=lambda i: (not i.is_late_file,)))


@dataclass(frozen=True)
class MapNode:
    """A region or actor on the strategic map / node graph."""

    id: str
    label: str
    cat: str
    brief: str
    link: str
    severity: int
    x: float
    y: float
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "MapNode":
        severity = raw.get("severity")
        return cls(
            id=_text(raw.get("id")),
            label=_text(raw.get("label")),
            cat=_text(raw.get("cat")),
            brief=_text(raw.get("brief")),
            link=_text(raw.get("link")),
            severity=severity if isinstance(severity, int) else 1,
            x=float(raw.get("x") or 0),
            y=float(raw.get("y") or 0),
            raw=raw,
        )


@dataclass(frozen=True)
class NodeEdge:
    """A connection between two map nodes."""

    frm: str
    to: str
    type: str
    label: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "NodeEdge":
        return cls(
            frm=_text(raw.get("from")),
            to=_text(raw.get("to")),
            type=_text(raw.get("type")),
            label=_text(raw.get("label")),
            raw=raw,
        )


@dataclass(frozen=True)
class NodeHistoryEntry:
    """Hand-curated archival background for one node. Never auto-generated (Step 4.7)."""

    node: str
    date: str
    title: str
    text: str
    tier: str
    source_title: str
    source_url: str | None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, node: str, raw: Mapping[str, Any]) -> "NodeHistoryEntry":
        return cls(
            node=node,
            date=_text(raw.get("date")),
            title=_text(raw.get("title")),
            text=_text(raw.get("text")),
            tier=_text(raw.get("tier")),
            source_title=_text(raw.get("source_title")),
            source_url=(_text(raw["source_url"]) if raw.get("source_url") else None),
            raw=raw,
        )


@dataclass(frozen=True)
class HorizonItem:
    """A dated thing ahead, with its confidence label (Step 5, point 6)."""

    when: str
    thread: str
    item: str
    confidence: str
    note: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "HorizonItem":
        return cls(
            when=_text(raw.get("when")),
            thread=_text(raw.get("thread")),
            item=_text(raw.get("item")),
            confidence=_text(raw.get("confidence")),
            note=_text(raw.get("note")),
            raw=raw,
        )

    #: ``when`` is deliberately free text ("Days", "13 Dec 2026 (runoff 21 Feb 2027)"), so
    #: sorting is by this coarse bucket rather than by a date parse that would fail on most
    #: real entries. Nearest first, per Step 5 point 6.
    _URGENCY = {"hours": 0, "days": 1, "week": 2, "weeks": 2, "month": 3, "months": 3}

    @property
    def urgency_rank(self) -> int:
        lowered = self.when.strip().lower()
        for key, rank in self._URGENCY.items():
            if lowered.startswith(key):
                return rank
        year = re.search(r"\b(20\d{2})\b", self.when)
        if year is not None:
            # Dated items sort after the relative buckets, oldest year first.
            return 10 + (int(year.group(1)) - 2026)
        return 50


@dataclass(frozen=True)
class TimelineEvent:
    """A row from either timeline array, normalised to one shape.

    ``timeline[]`` uses ``{d, t, c, txt, src, future}``; ``timeline_additions_2026[]`` uses
    ``{date, title, thread, text, src, attribution_class}``. They are the same kind of
    thing recorded under two field vocabularies, and every renderer wants them merged, so
    the normalisation happens once, here.
    """

    date: str
    title: str
    thread: str
    text: str
    src: tuple[str, ...]
    future: bool
    attribution_class: str | None
    origin: str  # "timeline" | "additions"
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_timeline(cls, raw: Mapping[str, Any]) -> "TimelineEvent":
        return cls(
            date=_text(raw.get("d")),
            title=_text(raw.get("t")),
            thread=_text(raw.get("c")),
            text=_text(raw.get("txt")),
            src=tuple(str(s) for s in (raw.get("src") or [])),
            future=bool(raw.get("future")),
            attribution_class=(
                _text(raw["attribution_class"]) if raw.get("attribution_class") else None
            ),
            origin="timeline",
            raw=raw,
        )

    @classmethod
    def from_addition(cls, raw: Mapping[str, Any]) -> "TimelineEvent":
        return cls(
            date=_text(raw.get("date")),
            title=_text(raw.get("title")),
            thread=_text(raw.get("thread")),
            text=_text(raw.get("text")),
            src=tuple(str(s) for s in (raw.get("src") or [])),
            future=bool(raw.get("future")),
            attribution_class=(
                _text(raw["attribution_class"]) if raw.get("attribution_class") else None
            ),
            origin="additions",
            raw=raw,
        )

    @property
    def sort_key(self) -> tuple[int, int, int]:
        """Chronological sort over the ledger's mixed date granularity.

        See :func:`parse_ledger_date`. An unparseable date sorts last rather than being
        dropped — an event with a date nothing can read is still an event, and burying it
        silently would be worse than showing it at the end where someone notices.
        """
        parsed = parse_ledger_date(self.date)
        return parsed if parsed is not None else (9999, 99, 99)


@dataclass(frozen=True)
class RetiredClaim:
    """A claim withdrawn by a later brief, which must never reappear in rendered output.

    BRIEFING-PROTOCOL.md, Step 6 lists "retired claims cannot reappear — swept across the
    dashboard, the archive, and every ``daily-brief-*.html`` on disk" as a required
    validator check. It had no registry to check against until this one; see
    ``docs/REBUILD-NOTES.md``.

    ``patterns`` are regular expressions matched case-insensitively against the *text* of
    rendered pages. ``exempt_files`` names the files that are allowed to contain the
    pattern because they are where the retraction itself is recorded — the brief that
    issued the correction necessarily quotes the claim it is withdrawing, and flagging
    that would make the check unusable rather than strict.
    """

    id: str
    claim: str
    retired_on: str
    retired_by_brief: int | None
    reason: str
    patterns: tuple[str, ...]
    exempt_files: tuple[str, ...]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "RetiredClaim":
        brief = raw.get("retired_by_brief")
        return cls(
            id=_text(raw.get("id")),
            claim=_text(raw.get("claim")),
            retired_on=_text(raw.get("retired_on")),
            retired_by_brief=brief if isinstance(brief, int) else None,
            reason=_text(raw.get("reason")),
            patterns=tuple(str(p) for p in (raw.get("patterns") or [])),
            exempt_files=tuple(str(f) for f in (raw.get("exempt_files") or [])),
            raw=raw,
        )

    def compiled_patterns(self) -> list[re.Pattern[str]]:
        """Compile this claim's patterns, skipping (not crashing on) an invalid one.

        An unusable pattern is reported by the validator as a failure in its own right;
        raising here would take down every other check with it.
        """
        compiled: list[re.Pattern[str]] = []
        for pattern in self.patterns:
            try:
                compiled.append(re.compile(pattern, re.IGNORECASE | re.DOTALL))
            except re.error:
                continue
        return compiled

    def invalid_patterns(self) -> list[tuple[str, str]]:
        """``(pattern, error)`` for every pattern that does not compile."""
        bad: list[tuple[str, str]] = []
        for pattern in self.patterns:
            try:
                re.compile(pattern, re.IGNORECASE | re.DOTALL)
            except re.error as exc:
                bad.append((pattern, str(exc)))
        return bad


@dataclass(frozen=True)
class LedgerStats:
    """Counts the rendered pages display and the validator diffs against them.

    Every number a rendered page shows comes from here, so a freshness check is a
    comparison between this object and the page, not between two independent counts that
    happen to be computed the same way twice.
    """

    brief_number: int
    threads: int
    current_sources: int
    total_sources: int
    timeline_events: int
    additions: int
    horizon: int
    archive_entries: int
    verification_checks: int
    map_nodes: int
    node_edges: int
    node_history_entries: int
    briefings: int
    revisions: int
    watchlist: int


# --------------------------------------------------------------------------------------
# The ledger itself
# --------------------------------------------------------------------------------------


class Ledger:
    """A parsed, validated-for-shape ``intel-ledger.json``.

    Construction enforces only *structural* correctness — the keys exist and hold the
    right container types — which is the "refuses to run on a ledger missing required
    keys" contract from BRIEFING-PROTOCOL.md Step 6. Everything semantic (intensities in
    range, citations resolvable, archive numbering) is :mod:`natdef.validate`'s job, and is
    deliberately *not* enforced here: the validator must be able to load a broken ledger in
    order to report what is broken about it.
    """

    def __init__(self, data: Mapping[str, Any], path: Path | None = None) -> None:
        self._data: dict[str, Any] = dict(data)
        self.path: Path | None = path
        self.root: Path = path.parent if path is not None else Path.cwd()

    # -- construction ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path | str, *, require_schema: bool = True) -> "Ledger":
        """Read and parse the ledger.

        :param require_schema: when true (the default, and what every renderer uses),
            missing required keys raise :class:`LedgerSchemaError` before any caller can
            act on a half-populated ledger. The validator passes false so it can report
            the missing keys itself rather than dying on the first one.
        """
        path = Path(path)
        if not path.is_file():
            raise LedgerNotFoundError(
                f"ledger not found: {path}. Refusing to continue — "
                "BRIEFING-PROTOCOL.md: do not reconstruct it from memory."
            )
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise LedgerNotFoundError(f"ledger at {path} could not be read: {exc}") from exc
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise LedgerParseError(f"ledger at {path} is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise LedgerSchemaError(
                f"ledger root must be a JSON object, got {type(data).__name__}"
            )
        ledger = cls(data, path=path)
        if require_schema:
            problems = ledger.schema_problems()
            if problems:
                raise LedgerSchemaError(
                    "ledger fails its structural contract and cannot be rendered:\n  - "
                    + "\n  - ".join(problems)
                )
        return ledger

    def schema_problems(self) -> list[str]:
        """Structural problems, as a list. Empty means the ledger is renderable."""
        problems: list[str] = []
        meta = self._data.get("ledger_meta")
        if not isinstance(meta, dict):
            problems.append("ledger_meta is missing or is not an object")
        else:
            for key in REQUIRED_META_KEYS:
                if meta.get(key) in (None, ""):
                    problems.append(f"ledger_meta.{key} is missing or empty")
        for key in REQUIRED_LIST_KEYS:
            if key not in self._data:
                problems.append(f"required key {key!r} is missing")
            elif not isinstance(self._data[key], list):
                problems.append(
                    f"{key} must be a list, got {type(self._data[key]).__name__}"
                )
        for key in OPTIONAL_LIST_KEYS:
            if key in self._data and not isinstance(self._data[key], list):
                problems.append(f"{key} must be a list, got {type(self._data[key]).__name__}")
        for key in DICT_KEYS:
            if key in self._data and not isinstance(self._data[key], dict):
                problems.append(f"{key} must be an object, got {type(self._data[key]).__name__}")
        return problems

    # -- raw access --------------------------------------------------------------------

    @property
    def data(self) -> dict[str, Any]:
        """The underlying dict. Used by ``build_app`` to bake a verbatim copy."""
        return self._data

    def _list(self, key: str) -> list[Mapping[str, Any]]:
        value = self._data.get(key)
        if not isinstance(value, list):
            return []
        return [v for v in value if isinstance(v, Mapping)]

    def _dict(self, key: str) -> dict[str, Any]:
        value = self._data.get(key)
        return dict(value) if isinstance(value, Mapping) else {}

    # -- typed views -------------------------------------------------------------------

    @property
    def meta(self) -> dict[str, Any]:
        return self._dict("ledger_meta")

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or "Strategic Threat & Posture Ledger")

    @property
    def brief_number(self) -> int:
        value = self.meta.get("brief_number")
        return value if isinstance(value, int) else 0

    @property
    def last_cutoff(self) -> str:
        return _text(self.meta.get("last_cutoff"))

    @property
    def last_cutoff_datetime(self) -> datetime | None:
        return parse_cutoff(self.last_cutoff)

    @property
    def last_updated(self) -> str:
        return _text(self.meta.get("last_updated"))

    @property
    def revision(self) -> str:
        return _text(self.meta.get("revision"))

    @property
    def threads(self) -> list[Thread]:
        return [Thread.from_raw(t) for t in self._list("threads")]

    @property
    def sources(self) -> list[Source]:
        return [Source.from_raw(s) for s in self._list("sources")]

    @property
    def archive(self) -> list[ArchiveEntry]:
        """Archive entries in ledger order. Use :meth:`archive_sorted` for numeric order."""
        return [ArchiveEntry.from_raw(a) for a in self._list("archive")]

    def archive_sorted(self, *, newest_first: bool = True) -> list[ArchiveEntry]:
        entries = sorted(self.archive, key=lambda a: a.number, reverse=newest_first)
        return entries

    @property
    def latest_archive(self) -> ArchiveEntry | None:
        entries = self.archive
        if not entries:
            return None
        return max(entries, key=lambda a: a.number)

    @property
    def map_nodes(self) -> list[MapNode]:
        return [MapNode.from_raw(n) for n in self._list("map_nodes")]

    @property
    def node_edges(self) -> list[NodeEdge]:
        return [NodeEdge.from_raw(e) for e in self._list("node_edges")]

    @property
    def node_topics(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for node_id, topics in self._dict("node_topics").items():
            if isinstance(topics, list):
                out[str(node_id)] = [str(t) for t in topics]
        return out

    @property
    def node_history(self) -> dict[str, list[NodeHistoryEntry]]:
        out: dict[str, list[NodeHistoryEntry]] = {}
        for node_id, entries in self._dict("node_history").items():
            if not isinstance(entries, list):
                continue
            out[str(node_id)] = [
                NodeHistoryEntry.from_raw(str(node_id), e) for e in entries if isinstance(e, Mapping)
            ]
        return out

    @property
    def horizon(self) -> list[HorizonItem]:
        return [HorizonItem.from_raw(h) for h in self._list("horizon")]

    def horizon_sorted(self) -> list[HorizonItem]:
        """Nearest first — BRIEFING-PROTOCOL.md Step 5, point 6."""
        return sorted(self.horizon, key=lambda h: (h.urgency_rank, h.when))

    @property
    def timeline(self) -> list[TimelineEvent]:
        return [TimelineEvent.from_timeline(e) for e in self._list("timeline")]

    @property
    def timeline_additions(self) -> list[TimelineEvent]:
        return [TimelineEvent.from_addition(e) for e in self._list("timeline_additions_2026")]

    def all_events(self) -> list[TimelineEvent]:
        """Both timeline arrays merged and sorted chronologically."""
        return sorted(self.timeline + self.timeline_additions, key=lambda e: e.sort_key)

    @property
    def briefings(self) -> list[Mapping[str, Any]]:
        return self._list("briefings")

    @property
    def revisions(self) -> list[Mapping[str, Any]]:
        return self._list("revisions")

    @property
    def verification_log(self) -> list[Mapping[str, Any]]:
        return self._list("verification_log")

    @property
    def schema_notes(self) -> list[Mapping[str, Any]]:
        return self._list("schema_notes")

    @property
    def standing_watchlist(self) -> list[str]:
        value = self._data.get("standing_watchlist")
        if not isinstance(value, list):
            return []
        return [str(v) for v in value]

    @property
    def categories(self) -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        for key, value in self._dict("categories").items():
            if isinstance(value, Mapping):
                out[str(key)] = {str(k): str(v) for k, v in value.items()}
        return out

    @property
    def source_urls(self) -> dict[str, str]:
        return {str(k): str(v) for k, v in self._dict("source_urls").items()}

    @property
    def retired_claims(self) -> list[RetiredClaim]:
        """The registry the "retired claims cannot reappear" check sweeps for.

        Absent from the pre-rebuild schema entirely, which is why that check could not be
        implemented before now. An empty list is a valid state and means the check passes
        trivially — it does not mean the check is disabled.
        """
        return [RetiredClaim.from_raw(c) for c in self._list("retired_claims")]

    # -- lookups -----------------------------------------------------------------------

    def thread_by_code(self, code: str) -> Thread | None:
        for thread in self.threads:
            if thread.code == code:
                return thread
        return None

    def thread_by_id(self, thread_id: str) -> Thread | None:
        for thread in self.threads:
            if thread.id == thread_id:
                return thread
        return None

    @property
    def thread_codes(self) -> set[str]:
        return {t.code for t in self.threads if t.code}

    @property
    def thread_ids(self) -> set[str]:
        return {t.id for t in self.threads if t.id}

    def source_by_id(self, source_id: str) -> Source | None:
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    @property
    def node_ids(self) -> set[str]:
        return {n.id for n in self.map_nodes if n.id}

    def resolve_citation(self, src_id: str) -> Citation:
        """Classify and, where possible, resolve one ``src[]`` value.

        Never invents a URL. A free-text citation comes back as ``kind="free-text"`` with
        ``url=None``, which is the honest answer — the URL for those lives in the delivered
        brief's own Sources table, not in the ledger.
        """
        if not src_id:
            return Citation(raw=src_id, kind="dead")
        source = self.source_by_id(src_id)
        if source is not None:
            if source.url:
                return Citation(raw=src_id, kind="registry", url=source.url, title=source.title)
            return Citation(raw=src_id, kind="dead", title=source.title)
        legacy = self.source_urls.get(src_id)
        if legacy:
            return Citation(raw=src_id, kind="legacy", url=legacy)
        if src_id in KNOWN_GENERIC_SENTINELS:
            return Citation(raw=src_id, kind="sentinel")
        if SHORT_CODE_RE.match(src_id):
            return Citation(raw=src_id, kind="dead")
        return Citation(raw=src_id, kind="free-text")

    def brief_files_on_disk(self) -> list[Path]:
        """Every delivered brief in ``briefs/``, sorted by filename (so, by date)."""
        briefs_dir = self.root / "briefs"
        if not briefs_dir.is_dir():
            return []
        return sorted(briefs_dir.glob("daily-brief-*.html"))

    # -- derived -----------------------------------------------------------------------

    def stats(self) -> LedgerStats:
        """The counts every rendered page displays and the validator checks against."""
        node_history_entries = sum(len(v) for v in self.node_history.values())
        sources = self.sources
        return LedgerStats(
            brief_number=self.brief_number,
            threads=len(self.threads),
            current_sources=sum(1 for s in sources if s.is_current),
            total_sources=len(sources),
            timeline_events=len(self.timeline),
            additions=len(self.timeline_additions),
            horizon=len(self.horizon),
            archive_entries=len(self.archive),
            verification_checks=len(self.verification_log),
            map_nodes=len(self.map_nodes),
            node_edges=len(self.node_edges),
            node_history_entries=node_history_entries,
            briefings=len(self.briefings),
            revisions=len(self.revisions),
            watchlist=len(self.standing_watchlist),
        )

    def events_for_node(self, node_id: str) -> list[TimelineEvent]:
        """Every timeline event mapped to a node through ``node_topics``.

        BRIEFING-PROTOCOL.md, Step 6: the node map's history/recent/future timelines are
        "computed from ``timeline[]``, ``timeline_additions_2026[]`` and ``horizon[]`` via
        ``node_topics`` — only ``node_edges[]`` and ``node_history[]`` are hand-curated
        inputs; everything else on that page is derived, never duplicated."
        """
        topics = set(self.node_topics.get(node_id, ()))
        if not topics:
            return []
        return [e for e in self.all_events() if e.thread in topics]

    def horizon_for_node(self, node_id: str) -> list[HorizonItem]:
        topics = set(self.node_topics.get(node_id, ()))
        if not topics:
            return []
        return [h for h in self.horizon_sorted() if h.thread in topics]

    def iter_citations(self) -> Iterator[tuple[str, int, str, Citation]]:
        """``(array_name, index, raw_src, resolution)`` for every citation in the ledger."""
        for i, event in enumerate(self.timeline):
            for src_id in event.src:
                yield ("timeline", i, src_id, self.resolve_citation(src_id))
        for i, event in enumerate(self.timeline_additions):
            for src_id in event.src:
                yield ("timeline_additions_2026", i, src_id, self.resolve_citation(src_id))


def load_ledger(path: Path | str, *, require_schema: bool = True) -> Ledger:
    """Convenience wrapper mirroring :meth:`Ledger.load`."""
    return Ledger.load(path, require_schema=require_schema)


def default_ledger_path(start: Path | None = None) -> Path:
    """Locate ``intel-ledger.json`` from the repository root this package sits in."""
    here = (start or Path(__file__).resolve().parent).resolve()
    for candidate in (here, *here.parents):
        ledger = candidate / "intel-ledger.json"
        if ledger.is_file():
            return ledger
    return (start or Path.cwd()) / "intel-ledger.json"


def iter_mappings(values: Iterable[Any]) -> Iterator[Mapping[str, Any]]:
    """Yield only the mapping members of a heterogeneous list, ignoring the rest."""
    for value in values:
        if isinstance(value, Mapping):
            yield value
