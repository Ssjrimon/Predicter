"""A minimal but *valid* ledger, plus helpers to break it in one specific way.

The tests deliberately do not run against ``intel-ledger.json`` for correctness assertions.
That file is real operational history with real messiness in it — two cutoff formats, two
file conventions, free-text citations — and a test that asserts against it would either
encode that messiness as the expected shape or fail whenever a brief is filed. Instead:

* this fixture is the *clean* shape, used to assert what each check does; and
* :class:`tests.test_real_ledger` runs the whole pipeline against the real ledger and
  asserts only what must always be true of it (it loads, it renders, it validates clean).

``break_*`` helpers each introduce exactly one defect, so a failing test names the defect
rather than a diff.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

__all__ = ["MINIMAL_LEDGER", "write_ledger", "with_defect"]


MINIMAL_LEDGER: dict[str, Any] = {
    "$schema_version": "3",
    "ledger_meta": {
        "title": "Test Ledger",
        "brief_number": 2,
        "last_cutoff": "2026-08-09T15:00Z",
        "last_updated": "2026-08-09",
        "revision": "T — test fixture",
    },
    "sources": [
        {
            "id": "ATA25",
            "title": "Annual Threat Assessment 2025",
            "publisher": "ODNI",
            "published": "2025-03-25",
            "url": "https://example.invalid/ata25.pdf",
            "status": "superseded",
            "superseded_by": "ATA26",
        },
        {
            "id": "ATA26",
            "title": "Annual Threat Assessment 2026",
            "publisher": "ODNI",
            "published": "2026-03-18",
            "url": "https://example.invalid/ata26.pdf",
            "status": "current",
            "tier": "verified-primary",
        },
    ],
    "threads": [
        {
            "id": "iran",
            "code": "IR",
            "label": "Iran / Hormuz",
            "intensity": 9,
            "direction": "volatile",
            "status": "Two things moved in opposite directions.",
            "one_line": "Mediation and a tanker strike in the same window.",
            "watch": ["Hormuz transit counts"],
        },
        {
            "id": "russia",
            "code": "RU",
            "label": "Russia / Ukraine",
            "intensity": 8,
            "direction": "escalating",
            "status": "Attrition continues.",
            "one_line": "No territorial change.",
            "watch": ["Negotiating rounds"],
        },
    ],
    "revisions": [],
    "timeline": [
        {
            "d": "2016",
            "t": "Baseline event",
            "c": "iran",
            "txt": "Something that happened.",
            "src": ["ATA26"],
        },
        {
            "d": "2049",
            "t": "A projected milestone",
            "c": "russia",
            "future": True,
            "txt": "A stated goal, not a prediction.",
            "src": ["ATA26"],
        },
    ],
    "timeline_additions_2026": [
        {
            "date": "2026-08-08",
            "thread": "iran",
            "title": "A 2026 addition",
            "text": "An event added since the founding documents.",
            "src": ["ATA26"],
            "attribution_class": "verified-primary",
        }
    ],
    "horizon": [
        {
            "when": "Days",
            "thread": "iran",
            "item": "Something imminent",
            "confidence": "contested",
            "note": "Nothing scheduled has been announced.",
        },
        {
            "when": "13 Dec 2026",
            "thread": "russia",
            "item": "Something dated",
            "confidence": "scheduled",
            "note": "",
        },
    ],
    "standing_watchlist": ["Who currently holds the relevant offices"],
    "verification_log": [
        {
            "date": "2026-08-09",
            "claim": "A claim that was checked",
            "result": "confirmed",
            "class": "verified-primary",
            "method": "Fetched the primary document.",
            "finding": "It says what the brief says it says.",
        }
    ],
    "schema_notes": [],
    "map_nodes": [
        {
            "id": "iran",
            "x": 588,
            "y": 290,
            "label": "IRAN",
            "cat": "adversary",
            "brief": "A node.",
            "link": "#b-iran",
            "severity": 9,
        },
        {
            "id": "russia",
            "x": 635,
            "y": 145,
            "label": "RUSSIA",
            "cat": "adversary",
            "brief": "Another node.",
            "link": "#b-russia",
            "severity": 6,
        },
    ],
    "categories": {"iran": {"label": "Iran", "color": "var(--iran)"}},
    "source_urls": {"ATA": "https://example.invalid/ata.pdf"},
    "briefings": [
        {"id": "b-iran", "index": "01", "title": "Iran", "html": "<p>A briefing.</p>"}
    ],
    "archive": [
        {
            "number": 1,
            "date": "2026-08-08",
            "weekday": "Saturday",
            "file": "briefs/daily-brief-2026-08-08.html",
            "cutoff": "2026-08-08T15:00Z",
            "revision": "T",
            "bottom_line": "The first brief.",
            "threads": {"IR": [8, "escalating"], "RU": [8, "escalating"]},
            "items": [
                {"n": 1, "thread": "IR", "head": "An item", "sowhat": "Why it matters."}
            ],
            "changed": ["IR opened at 8."],
            "verification": {"confirmed": 1},
        },
        {
            "number": 2,
            "date": "2026-08-09",
            "weekday": "Sunday",
            "file": "briefs/daily-brief-2026-08-09.html",
            "cutoff": "2026-08-09T15:00Z",
            "revision": "T",
            "bottom_line": "The second brief.",
            "threads": {"IR": [9, "volatile"], "RU": [8, "escalating"]},
            "items": [
                {
                    "n": "LF1",
                    "thread": "RU",
                    "head": "A late-file item",
                    "sowhat": "It broke inside the prior window.",
                },
                {
                    "n": 1,
                    "thread": "IR",
                    "head": "A normal item",
                    "sowhat": "Why it matters.",
                    "body": ["First paragraph.", "Second paragraph."],
                },
            ],
            "changed": ["IR moved 8/escalating to 9/volatile."],
            "verification": {"confirmed": 2},
        },
    ],
    "node_topics": {"iran": ["iran"], "russia": ["russia"]},
    "node_history": {
        "iran": [
            {
                "date": "1953-08-19",
                "title": "A historical event",
                "text": "What happened.",
                "source_title": "National Security Archive",
                "source_url": "https://example.invalid/nsa",
                "tier": "verified-primary",
            }
        ]
    },
    "node_edges": [
        {
            "from": "iran",
            "to": "russia",
            "type": "adversarial-cooperation",
            "label": "Looser cooperation",
        }
    ],
    "retired_claims": [],
}


def write_ledger(root: Path, ledger: dict[str, Any] | None = None) -> Path:
    """Write a ledger and the brief files its archive entries point at.

    The archive checks assert in both directions — an entry with no file fails, and a file
    with no entry fails — so a fixture that writes one without the other would be testing a
    state the validator is designed to reject.
    """
    data = copy.deepcopy(ledger if ledger is not None else MINIMAL_LEDGER)
    root.mkdir(parents=True, exist_ok=True)
    briefs = root / "briefs"
    briefs.mkdir(exist_ok=True)
    for entry in data.get("archive", []):
        name = Path(str(entry.get("file", ""))).name
        if name:
            (briefs / name).write_text(
                f"<html><body><h1>{entry.get('date')}</h1></body></html>", encoding="utf-8"
            )
    path = root / "intel-ledger.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def with_defect(mutate) -> dict[str, Any]:
    """A deep copy of the fixture with exactly one thing broken by ``mutate``."""
    data = copy.deepcopy(MINIMAL_LEDGER)
    mutate(data)
    return data
