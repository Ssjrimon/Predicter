"""HTML fragments shared by more than one rendered page.

Anything that appears on two pages is built here exactly once, so the movement board on the
command centre and the movement board on the dashboard cannot drift into being two
subtly different components that both claim to be "the signature element of the product"
(BRIEFING-PROTOCOL.md, Step 5, point 3).

Every function returns a complete, already-escaped HTML string. Ledger text is escaped at
the point it is interpolated — with the single, marked exception of ``briefings[].html``,
which is authored as HTML in the ledger and is the one field intended to pass through raw.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from .ledger import (
    ArchiveEntry,
    Citation,
    Ledger,
    MapNode,
    Source,
    Thread,
    TimelineEvent,
    parse_cutoff,
)
from .template import attr, esc
from .theme import CATEGORY_COLORS, direction_color

__all__ = [
    "PAGES",
    "nav",
    "masthead",
    "stat_strip",
    "movement_board",
    "thread_rows",
    "bottom_line",
    "citations_line",
    "sources_table",
    "timeline_events",
    "briefings_accordion",
    "ARROWS",
    "map_svg",
    "archive_thread_strip",
    "cutoff_age_note",
    "direction_arrow",
    "humanize_ago",
]

#: The four generated pages, in navigation order. ``render`` and ``validate`` both read
#: this, so a page cannot be added to one without the other noticing.
PAGES: tuple[tuple[str, str], ...] = (
    ("index.html", "Command Center"),
    ("strategic-threat-briefing.html", "Dashboard"),
    ("node-map.html", "Node Map"),
    ("brief-archive.html", "Archive"),
)

#: Direction -> glyph. Chosen so the board is readable without colour, for print and for
#: anyone who cannot distinguish the palette's red from its green.
_ARROWS: dict[str, str] = {
    "escalating": "▲",  # up
    "easing": "▼",  # down
    "holding": "▬",  # flat
    "volatile": "◆",  # diamond: movement without a direction
}


#: Public, immutable view of the arrow map. The archive page embeds this into its digest
#: script so the client-side digest and the server-side board cannot disagree about which
#: glyph means which direction.
ARROWS: dict[str, str] = dict(_ARROWS)


def direction_arrow(direction: str) -> str:
    """Glyph for a thread direction. ``?`` for an unrecognised one, never a silent blank."""
    return _ARROWS.get(direction, "?")


def humanize_ago(date_text: str, *, now: datetime | None = None) -> str:
    """"how long ago" for a ledger date of any granularity, or ``""`` if it will not parse.

    BRIEFING-PROTOCOL.md describes the node map's deep dive as carrying "a date, a source,
    and a 'how long ago' readout". Ledger dates run ``1953-08-19``, ``2025-09`` and ``2016``
    in the same array, so this parses the most precise prefix available and says nothing at
    all when it cannot — an empty string, not a wrong number.
    """
    now = now or datetime.now(timezone.utc)
    text = (date_text or "").strip()
    for fmt, granularity in (("%Y-%m-%d", "day"), ("%Y-%m", "month"), ("%Y", "year")):
        try:
            when = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        delta_days = (now - when).days
        if delta_days < 0:
            years_ahead = -delta_days / 365.25
            if years_ahead >= 1:
                return f"in {years_ahead:.0f} yr"
            return f"in {-delta_days} d"
        if granularity == "day" and delta_days < 45:
            return "today" if delta_days == 0 else f"{delta_days} d ago"
        if delta_days < 365:
            return f"{max(1, round(delta_days / 30.44))} mo ago"
        return f"{delta_days / 365.25:.0f} yr ago"
    return ""


def nav(current: str) -> str:
    """The top navigation, with ``current`` marked. ``current`` must be a real page name."""
    parts: list[str] = []
    for filename, label in PAGES:
        here = ' class="here"' if filename == current else ""
        parts.append(f'<a href="{attr(filename)}"{here}>{esc(label)}</a>')
    return "".join(parts)


def masthead(
    *,
    eyebrow: str,
    title_html: str,
    subtitle: str,
    byline: Sequence[tuple[str, str]],
) -> str:
    """The page header. ``title_html`` is trusted markup built by the caller, not ledger text."""
    byline_html = "".join(
        f"<span><b>{esc(label)}</b> {esc(value)}</span>" for label, value in byline if value
    )
    return (
        '<header class="masthead"><div class="wrap">'
        '<div class="eyebrow-row"><span>Unclassified &mdash; Open-Source Compilation</span>'
        f'<span class="dim">{esc(eyebrow)}</span></div>'
        f'<h1 class="title">{title_html}</h1>'
        f'<p class="subtitle">{esc(subtitle)}</p>'
        f'<div class="byline">{byline_html}</div>'
        "</div></header>"
    )


def stat_strip(cells: Sequence[tuple[str, str]]) -> str:
    """The counts strip under the masthead. Every number here comes from ``Ledger.stats()``."""
    body = "".join(
        f'<div class="statcell"><div class="statnum">{esc(num)}</div>'
        f'<div class="statlabel">{esc(label)}</div></div>'
        for num, label in cells
    )
    return f'<div class="statstrip">{body}</div>'


def movement_board(threads: Sequence[Thread], *, heading: bool = True) -> str:
    """All ten threads as gauge columns — the five-second read.

    BRIEFING-PROTOCOL.md, Step 5, point 3: "intensity as bar height, direction as an arrow,
    colored by direction. This is the five-second read and the signature element of the
    product. It never gets dropped, even on a quiet day."
    """
    gauges: list[str] = []
    for thread in threads:
        colour = direction_color(thread.direction)
        # An invalid intensity draws an empty bar rather than a misleading full one; the
        # validator fails on it separately, so the page must not paper over it.
        height = max(0, min(100, thread.intensity * 10)) if thread.intensity_is_valid else 0
        gauges.append(
            '<div class="gauge">'
            f'<span class="g-code">{esc(thread.code)}</span>'
            f'<div class="g-bar" role="img" aria-label="{attr(thread.label)}: intensity '
            f'{attr(thread.intensity)} of 10, {attr(thread.direction)}">'
            f'<span class="g-fill" style="height:{height}%;background:{colour}"></span></div>'
            '<div class="g-meta">'
            f'<span class="g-int">{esc(thread.intensity if thread.intensity_is_valid else "?")}</span>'
            f'<span class="g-arrow" style="color:{colour}">{esc(direction_arrow(thread.direction))}</span>'
            "</div>"
            f'<span class="g-label">{esc(thread.label)}</span>'
            "</div>"
        )
    legend = "".join(
        f'<span class="lg"><span class="sw" style="background:{direction_color(d)}"></span>'
        f"{esc(d)} {esc(direction_arrow(d))}</span>"
        for d in ("escalating", "holding", "easing", "volatile")
    )
    head = ""
    if heading:
        head = (
            '<div class="sec-head"><div class="sec-eyebrow">Movement board</div>'
            '<h2 class="sec-title">All ten threads, right now</h2>'
            '<p class="sec-desc">Bar height is intensity on a 1-10 scale; colour and glyph are '
            "direction. <em>Volatile</em> means large movement without a consistent direction &mdash; "
            "it is a reading, not a hedge.</p></div>"
        )
    return f'{head}<div class="board">{"".join(gauges)}</div><div class="boardlegend">{legend}</div>'


def thread_rows(threads: Sequence[Thread]) -> str:
    """The long-form thread list: one-line assessment plus current status per thread."""
    rows: list[str] = []
    for thread in threads:
        colour = direction_color(thread.direction)
        rows.append(
            f'<div class="threadrow" id="thread-{attr(thread.code.lower())}">'
            '<div class="tr-head">'
            f'<span class="tr-code">{esc(thread.code)}</span>'
            f'<span class="tr-name">{esc(thread.label)}</span>'
            f'<span class="tr-dir" style="color:{colour}">'
            f'{esc(thread.intensity)}/10 &middot; {esc(thread.direction)} '
            f"{esc(direction_arrow(thread.direction))}</span>"
            "</div>"
            f'<p class="tr-one">{esc(thread.one_line)}</p>'
            f'<p class="tr-status">{esc(thread.status)}</p>'
            "</div>"
        )
    return "".join(rows)


def bottom_line(label: str, text: str) -> str:
    """The single assessment that matters, in the largest type on the page."""
    return (
        '<div class="bottomline">'
        f'<div class="bl-label">{esc(label)}</div>'
        f'<div class="bl-text">{esc(text)}</div>'
        "</div>"
    )


def citations_line(citations: Iterable[Citation]) -> str:
    """Render an event's citations as linked pills, honestly labelled.

    A registry-backed citation becomes a link. A free-text one becomes plain text, because
    the ledger holds no URL for it and inventing one is the exact failure mode
    BRIEFING-PROTOCOL.md's Step 3 gate exists to prevent. A dead reference is marked as
    such on the page rather than hidden — the validator fails the build on it anyway, so
    the only way this renders is in a working tree someone is mid-fix on.
    """
    parts: list[str] = []
    for citation in citations:
        if citation.url:
            parts.append(
                f'<a class="pill" href="{attr(citation.url)}" rel="noopener noreferrer" '
                f'target="_blank">{esc(citation.label())}</a>'
            )
        elif citation.kind == "dead":
            parts.append(
                f'<span class="pill tier-contested">{esc(citation.raw)} &mdash; unresolved</span>'
            )
        else:
            parts.append(f'<span class="pill">{esc(citation.label())}</span>')
    return "".join(parts)


def sources_table(sources: Sequence[Source]) -> str:
    """Every primary document, linked and tiered, current first then superseded."""
    # `cited` is a dated item a brief cited, as opposed to a standing document or a
    # recurring tracker; it sorts after both and before the superseded record.
    order = {"current": 0, "tracking": 1, "cited": 2, "superseded": 3}
    rows: list[str] = []
    for source in sorted(sources, key=lambda s: (order.get(s.status, 3), s.id)):
        link = (
            f'<a href="{attr(source.url)}" rel="noopener noreferrer" target="_blank">'
            f"{esc(source.title)}</a>"
            if source.url
            else esc(source.title)
        )
        status_pill = f'<span class="pill">{esc(source.status)}</span>'
        if source.is_superseded and source.superseded_by:
            status_pill += f' <span class="pill">&rarr; {esc(source.superseded_by)}</span>'
        tier = (
            f'<span class="pill tier-{attr(source.tier)}">{esc(source.tier)}</span>'
            if source.tier
            else ""
        )
        rows.append(
            "<tr>"
            f'<td class="mono">{esc(source.id)}</td>'
            f"<td><b>{link}</b><br>{esc(source.note)}</td>"
            f"<td>{esc(source.publisher)}</td>"
            f'<td class="mono">{esc(source.published)}</td>'
            f"<td>{status_pill} {tier}</td>"
            "</tr>"
        )
    return (
        '<div class="tablewrap"><table class="table">'
        "<thead><tr><th>Code</th><th>Document</th><th>Publisher</th><th>Published</th>"
        "<th>Status</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def timeline_events(
    ledger: Ledger,
    events: Sequence[TimelineEvent],
    *,
    thread_labels: Mapping[str, str] | None = None,
) -> str:
    """The chronological rail. Projected items are marked, never mixed in silently."""
    labels = dict(thread_labels or {})
    blocks: list[str] = []
    for event in events:
        classes = "event is-future" if event.future else "event"
        label = labels.get(event.thread, event.thread)
        pills = citations_line(ledger.resolve_citation(s) for s in event.src)
        klass = (
            f'<span class="pill tier-{attr(event.attribution_class)}">'
            f"{esc(event.attribution_class)}</span>"
            if event.attribution_class
            else ""
        )
        future_tag = '<span class="pill tier-attributed-claim">projected</span>' if event.future else ""
        blocks.append(
            f'<div class="{classes}" data-thread="{attr(event.thread)}" '
            f'data-future="{"1" if event.future else "0"}" data-date="{attr(event.date)}">'
            f'<div class="e-date">{esc(event.date)} &middot; {esc(label)}</div>'
            f'<div class="e-title">{esc(event.title)}</div>'
            f'<p class="e-text">{esc(event.text)}</p>'
            f'<div class="e-meta">{future_tag}{klass}{pills}</div>'
            "</div>"
        )
    if not blocks:
        return '<div class="emptystate">No events match the current filter.</div>'
    return "".join(blocks)


def briefings_accordion(briefings: Sequence[Mapping[str, object]]) -> str:
    """The thirteen actor/theatre briefings.

    ``briefings[].html`` is authored as HTML in the ledger and is interpolated raw — the one
    place in this package where ledger content is not escaped. That is intentional and is
    why the field is named ``html``; the titles beside it are escaped normally.
    """
    blocks: list[str] = []
    for briefing in briefings:
        ident = str(briefing.get("id") or "")
        index = str(briefing.get("index") or "")
        title = str(briefing.get("title") or "")
        body = str(briefing.get("html") or "")
        blocks.append(
            f'<details class="briefing" id="{attr(ident)}">'
            "<summary><span class=\"b-title\">"
            f'<span class="b-index">{esc(index)}</span> {esc(title)}</span>'
            '<span class="b-chevron" aria-hidden="true">+</span></summary>'
            f'<div class="b-body">{body}</div>'
            "</details>"
        )
    return "".join(blocks)


def map_svg(
    nodes: Sequence[MapNode],
    edges: Sequence[Mapping[str, str]],
    *,
    width: int = 1000,
    height: int = 460,
) -> str:
    """The schematic strategic map as inline SVG.

    Positions come from ``map_nodes[].x/.y``, which are schematic rather than geographic and
    are hand-set in the ledger. Nothing here computes a layout, so the map cannot drift from
    the coordinates an editor chose.
    """
    by_id = {n.id: n for n in nodes}
    lines: list[str] = []
    for edge in edges:
        source = by_id.get(str(edge.get("from") or ""))
        target = by_id.get(str(edge.get("to") or ""))
        if source is None or target is None:
            continue  # validate.py fails on this separately; the map simply omits it
        edge_type = str(edge.get("type") or "")
        dashed = "" if edge_type == "alliance" else ' stroke-dasharray="5 5"'
        colour = {
            "alliance": "var(--blue)",
            "adversarial-cooperation": "var(--coop)",
            "conflict": "var(--red)",
            "contested": "var(--purple)",
            "hemisphere": "var(--gold)",
        }.get(edge_type, "var(--hair)")
        lines.append(
            f'<line x1="{source.x}" y1="{source.y}" x2="{target.x}" y2="{target.y}" '
            f'stroke="{colour}" stroke-width="1"{dashed} opacity="0.55"><title>'
            f"{esc(edge.get('label') or edge_type)}</title></line>"
        )
    circles: list[str] = []
    for node in nodes:
        colour = CATEGORY_COLORS.get(node.cat, "var(--dim)")
        radius = 5 + max(0, min(10, node.severity)) * 1.1
        circles.append(
            f'<g class="node" data-node="{attr(node.id)}" tabindex="0" role="button" '
            f'aria-label="{attr(node.label)}">'
            f'<circle cx="{node.x}" cy="{node.y}" r="{radius:.1f}" fill="{colour}" '
            f'fill-opacity="0.75" stroke="{colour}" stroke-width="1"></circle>'
            f'<text x="{node.x}" y="{node.y + radius + 11:.1f}">{esc(node.label)}</text>'
            "</g>"
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" '
        'role="group" aria-label="Schematic strategic map">'
        f'{"".join(lines)}{"".join(circles)}</svg>'
    )


def archive_thread_strip(entry: ArchiveEntry, previous: ArchiveEntry | None) -> str:
    """The ten-code chip strip for one archive entry, marking what moved since the previous."""
    chips: list[str] = []
    prior = previous.threads if previous is not None else {}
    for code, value in entry.threads.items():
        if not (isinstance(value, (list, tuple)) and len(value) == 2):
            chips.append(f'<span class="chip">{esc(code)} ?</span>')
            continue
        intensity, direction = value
        was = prior.get(code)
        moved = bool(was) and list(was) != list(value)
        klass = "chip moved" if moved else "chip"
        title = ""
        if moved and isinstance(was, (list, tuple)) and len(was) == 2:
            title = f' title="was {was[0]}/{was[1]}"'
        chips.append(
            f'<span class="{klass}"{title} style="border-color:{direction_color(str(direction))}">'
            f"{esc(code)} {esc(intensity)}{esc(direction_arrow(str(direction)))}</span>"
        )
    return f'<div class="bc-strip">{"".join(chips)}</div>'


def cutoff_age_note(cutoff: str, *, now: datetime | None = None) -> str:
    """A plain-language age for an information cutoff, for the masthead.

    BRIEFING-PROTOCOL.md, "Lookback discipline", point 4: an interval over 48 hours has to
    say so, because the reader is getting a multi-day catch-up rather than a daily.
    """
    moment = parse_cutoff(cutoff)
    if moment is None:
        return "cutoff unparseable"
    reference = now or datetime.now(timezone.utc)
    hours = (reference - moment).total_seconds() / 3600
    if hours < 0:
        return "cutoff is in the future"
    if hours <= 48:
        return f"{hours:.0f}h old"
    return f"{hours / 24:.0f} days old — next brief is a multi-day catch-up"
