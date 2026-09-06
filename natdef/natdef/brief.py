"""``brief.py`` — write ``briefs/daily-brief-YYYY-MM-DD.html`` from the ledger.

BRIEFING-PROTOCOL.md Step 5 specifies the brief's structure exactly, in order: masthead
with the information cutoff, the bottom line, the movement board, the numbered items with
late-file items first, what changed on the board, the horizon, the verification log, and
the sources. Everything in that list except the items' body prose already exists in the
ledger by the time Step 5 runs, because Step 4 put it there.

**So the brief is generated from the archive entry, not typed alongside it.** That is the
single most useful thing this rebuild does for correctness. Brief 011 shipped a defect
where the archive snapshot and the brief's prose said KP and HL had moved while live
``threads[]`` still held the old values, and nothing caught it for four days
(``docs/MIGRATION-NOTES.md``). ``validate.py`` now catches that class of error after the
fact; generating the brief from the same object the validator checks means the brief and
the ledger cannot disagree in the first place.

What the ledger cannot supply is each item's two paragraphs of body prose — ``archive[]``
stores a headline and a So-what, by design, because those are what the archive digest needs.
An item may carry an optional ``body`` (a list of paragraph strings) for this renderer to
use. Where it does not, the brief renders a visible, unmissable placeholder rather than a
plausible-looking gap: an unwritten item should look unwritten.

**Resolving the open template question.** ``docs/MIGRATION-NOTES.md`` flagged, as a genuine
open decision, that Briefs 001-011 used a light theme with an interactive board while Brief
012 used an unrelated dark theme — and that the next brief needed one or the other picked
deliberately rather than by whoever reached for which. This module picks: the dark theme,
shared with the dashboard through :mod:`natdef.theme`, so the daily brief and the standing
picture are visibly one product. Delivered briefs are not re-rendered into it — they are
never rewritten — so the two styles coexist in the archive exactly as delivered, which is
what the protocol requires.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from . import components as C
from .errors import NatDefError, RenderError
from .ledger import ArchiveEntry, Ledger, default_ledger_path
from .template import attr, esc, render_file
from .theme import CSS, direction_color

__all__ = ["build_brief", "brief_filename", "main"]

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_PLACEHOLDER = (
    '<p class="todo"><b>Body not written.</b> Add a <span class="mono">body</span> array of '
    "paragraph strings to this item in the ledger's archive entry, then re-run "
    "<span class=\"mono\">python3 -m natdef.brief</span>.</p>"
)


def brief_filename(date: str) -> str:
    """``daily-brief-2026-08-29.html``. The date must already be ``YYYY-MM-DD``."""
    return f"daily-brief-{date}.html"


def _interval_note(entry: ArchiveEntry, previous: ArchiveEntry | None) -> str:
    """The masthead's interval line.

    "If the interval exceeds 48 hours or a scheduled run was missed, state it here"
    (Step 5, point 1). Computed, not remembered — the failure mode this replaces is a
    multi-day catch-up shipped with a masthead that implies a daily.
    """
    now = entry.cutoff_datetime
    if now is None:
        return "Information cutoff does not parse — the interval covered cannot be stated."
    if previous is None:
        return "First brief in the ledger; no prior cutoff to measure from."
    before = previous.cutoff_datetime
    if before is None:
        return f"Prior cutoff {previous.cutoff} does not parse; interval cannot be computed."
    hours = (now - before).total_seconds() / 3600
    if hours > 48:
        return (
            f"Covers {hours:.0f} hours since brief {previous.number:03d}'s cutoff "
            f"({previous.cutoff}) — a multi-day catch-up, not a daily. "
            "Late-file items run first."
        )
    return (
        f"Covers {hours:.0f} hours since brief {previous.number:03d}'s cutoff "
        f"({previous.cutoff})."
    )


def _items_section(entry: ArchiveEntry, ledger: Ledger) -> str:
    """Numbered items, late file first, each with its headline, body and So-what."""
    blocks: list[str] = []
    for item in entry.sorted_items():
        thread = ledger.thread_by_code(item.thread)
        thread_label = thread.label if thread is not None else item.thread
        colour = direction_color(thread.direction) if thread is not None else "var(--dim)"
        body_source = item.raw.get("body")
        if isinstance(body_source, str):
            paragraphs = [body_source]
        elif isinstance(body_source, list):
            paragraphs = [str(p) for p in body_source if str(p).strip()]
        else:
            paragraphs = []
        body = (
            "".join(f"<p>{esc(p)}</p>" for p in paragraphs) if paragraphs else _PLACEHOLDER
        )
        late = '<span class="pill late">late file</span>' if item.is_late_file else ""
        blocks.append(
            '<article class="item">'
            '<div class="i-head">'
            f'<span class="i-n">{esc(item.n)}</span>'
            f'<span class="chip" style="border-color:{colour}">{esc(item.thread)} &middot; '
            f"{esc(thread_label)}</span>{late}</div>"
            f'<h3 class="i-title">{esc(item.head)}</h3>'
            f'<div class="i-body">{body}</div>'
            f'<p class="i-sowhat"><b>So what</b> &mdash; {esc(item.sowhat)}</p>'
            "</article>"
        )
    if not blocks:
        return (
            '<p class="todo"><b>No items in this brief\'s archive entry.</b> A quiet day is a '
            "legitimate outcome and a short brief is correct &mdash; but the entry still needs "
            "its items array, even if empty by intent.</p>"
        )
    return "".join(blocks)


def _changed_section(entry: ArchiveEntry, previous: ArchiveEntry | None) -> str:
    """What this brief altered in the standing picture (Step 5, point 5)."""
    moved: list[str] = []
    if previous is not None:
        for code, value in entry.threads.items():
            was = previous.threads.get(code)
            if was is None or list(was) == list(value):
                continue
            moved.append(
                f'<li><span class="mono">{esc(code)}</span> '
                f"{esc(was[0])}/{esc(was[1])} &rarr; <b>{esc(value[0])}/{esc(value[1])}</b></li>"
            )
    notes = "".join(f"<li>{esc(line)}</li>" for line in entry.changed)
    board = (
        f'<div class="c-eyebrow">Threads that moved</div><ul>{"".join(moved)}</ul>'
        if moved
        else '<div class="c-eyebrow">Threads that moved</div>'
        "<p>No thread changed intensity or direction in this window.</p>"
    )
    written = (
        f'<div class="c-eyebrow" style="margin-top:16px">Recorded in the ledger</div>'
        f"<ul>{notes}</ul>"
        if notes
        else ""
    )
    return f'<div class="panel">{board}{written}</div>'


def _verification_section(entry: ArchiveEntry, ledger: Ledger) -> str:
    """The tally from the archive entry, plus this date's verification_log entries in full.

    "Log every check in ``verification_log[]``... The log is part of the product" (Step 3),
    and "Corrections are never quiet" (Step 5, point 7). Both are satisfied by rendering the
    log rather than summarising it.
    """
    tally = "".join(
        f'<span class="chip">{esc(key)}: {esc(value)}</span>'
        for key, value in entry.verification.items()
    )
    rows: list[str] = []
    for log in ledger.verification_log:
        if str(log.get("date") or "") != entry.date:
            continue
        rows.append(
            "<tr>"
            f'<td><b>{esc(log.get("claim"))}</b><br>{esc(log.get("finding"))}</td>'
            f'<td>{esc(log.get("method"))}</td>'
            f'<td><span class="pill tier-{attr(log.get("class"))}">{esc(log.get("class"))}</span>'
            f'<br>{esc(log.get("result"))}</td>'
            "</tr>"
        )
    table = (
        '<div class="tablewrap"><table class="table"><thead><tr><th>Claim and finding</th>'
        f"<th>Method</th><th>Outcome</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
        if rows
        else '<p class="todo">No verification_log entries carry this brief\'s date. Every '
        "claim that ran in this brief should have one (Step 3).</p>"
    )
    correction = (
        f'<div class="notice" style="margin-bottom:16px">'
        f'<div class="n-label">Correction to a prior brief</div>{esc(entry.headline_correction)}'
        "</div>"
        if entry.headline_correction
        else ""
    )
    return f'{correction}<div class="bc-strip">{tally}</div>{table}'


def build_brief(ledger: Ledger, number: int) -> str:
    """Render the brief for archive entry ``number``."""
    entries = {e.number: e for e in ledger.archive}
    entry = entries.get(number)
    if entry is None:
        raise RenderError(
            f"no archive[] entry numbered {number}. Step 4.8 writes the archive entry; "
            "Step 5 renders the brief from it. Do Step 4 first."
        )
    previous = entries.get(number - 1)

    interval = _interval_note(entry, previous)
    over_48 = "multi-day catch-up" in interval

    tokens = {
        "BRIEF_NUMBER": f"{entry.number:03d}",
        "BRIEF_DATE": esc(entry.date),
        "BRIEF_WEEKDAY": esc(entry.weekday),
        "CUTOFF": esc(entry.cutoff),
        "INTERVAL": esc(interval),
        "INTERVAL_CLASS": "notice" if over_48 else "panel tight",
        "REVISION": esc(entry.revision or ledger.revision),
        "CSS": CSS,
        "BOTTOM_LINE": esc(entry.bottom_line),
        "BOARD": C.movement_board(ledger.threads, heading=False),
        "ITEMS": _items_section(entry, ledger),
        "CHANGED": _changed_section(entry, previous),
        "HORIZON": _horizon_list(ledger),
        "VERIFICATION": _verification_section(entry, ledger),
        "SOURCES": C.sources_table(ledger.sources),
        "GENERATED_AT": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "ARCHIVE_LINK": "../brief-archive.html",
    }
    return render_file(TEMPLATE_DIR / "brief.html.tmpl", tokens)


def _horizon_list(ledger: Ledger) -> str:
    labels = {t.id: t.label for t in ledger.threads}
    rows = "".join(
        "<tr>"
        f'<td class="mono">{esc(item.when)}</td>'
        f"<td>{esc(labels.get(item.thread, item.thread))}</td>"
        f'<td><b>{esc(item.item)}</b>{"<br>" + esc(item.note) if item.note else ""}</td>'
        f'<td><span class="pill">{esc(item.confidence)}</span></td>'
        "</tr>"
        for item in ledger.horizon_sorted()
    )
    return (
        '<div class="tablewrap"><table class="table"><thead><tr><th>When</th><th>Thread</th>'
        f"<th>Item</th><th>Confidence</th></tr></thead><tbody>{rows}</tbody></table></div>"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="brief.py",
        description="Render briefs/daily-brief-YYYY-MM-DD.html from its archive[] entry.",
    )
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument(
        "--number",
        type=int,
        default=None,
        help="archive entry to render (default: ledger_meta.brief_number, i.e. the newest)",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="output path (default: briefs/daily-brief-<date>.html)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing brief. Off by default: BRIEFING-PROTOCOL.md forbids "
        "rewriting a delivered brief, so overwriting one has to be deliberate.",
    )
    args = parser.parse_args(argv)

    try:
        ledger = Ledger.load(args.ledger or default_ledger_path())
        number = args.number if args.number is not None else ledger.brief_number
        html = build_brief(ledger, number)
    except NatDefError as exc:
        print(f"brief: {exc}", file=sys.stderr)
        return 1

    entry = next(e for e in ledger.archive if e.number == number)
    out = args.out or (ledger.root / "briefs" / brief_filename(entry.date))
    if out.exists() and not args.force:
        print(
            f"brief: {out.name} already exists. A delivered brief is never rewritten — "
            "corrections run in the next brief's verification log. Pass --force only if this "
            "one has not been delivered yet.",
            file=sys.stderr,
        )
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    try:
        shown: Path | str = out.relative_to(ledger.root)
    except ValueError:
        # --out can legitimately point outside the repository (a scratch preview, say).
        shown = out
    print(
        f"brief: wrote {shown} — brief {number:03d}, {entry.date}, "
        f"cutoff {entry.cutoff}, {len(entry.items)} item(s)"
    )
    print("brief: now run `python3 -m natdef.render`, `python3 -m natdef.build_app`, then "
          "`python3 -m natdef.validate`, and update briefs/INDEX.md.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
