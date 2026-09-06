"""The four generated pages.

BRIEFING-PROTOCOL.md, "The standing job", defines what each one is for, and those
definitions are the spec these functions implement:

``index.html``
    The **front door** — "the one link worth bookmarking. Today's bottom line, the
    ten-thread movement strip, and three cards into the other pages, each carrying a live
    stat pulled from the ledger at render time."

``strategic-threat-briefing.html``
    The **standing picture** — the map, the chronology, the thirteen actor/theatre
    briefings, and the primary documents behind them.

``brief-archive.html``
    **Every brief, browsable by date**, "with a built-in catch-up digest — pick a window
    (yesterday, 3 days, 7 days, a custom date, all of it) and get the net thread movement
    and every item across that window, rather than a stack of individual briefs to open."

``node-map.html``
    **Every region/actor as a force-directed graph**, with a per-node deep dive whose
    history / recent / horizon timelines are *computed* from ``timeline[]``,
    ``timeline_additions_2026[]`` and ``horizon[]`` through ``node_topics`` — only
    ``node_edges[]`` and ``node_history[]`` are hand-curated (Step 6).

Each function returns ``(html, counts)``. ``counts`` is written into the page's own
``natdef:counts`` meta tag and is what :mod:`natdef.validate` diffs the rendered page
against — so the freshness checks compare a page to the ledger through one declared
contract, rather than by scraping markup and hoping the scrape keeps working.

All page JavaScript is inlined and dependency-free. These files are opened straight off
disk, frequently with no network at all; a CDN import would make the archive unreadable in
exactly the situation it exists for.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import components as C
from .ledger import Ledger
from .template import attr, esc, json_literal
from .theme import CATEGORY_COLORS, EDGE_COLORS, direction_color

__all__ = ["build_index", "build_dashboard", "build_archive", "build_node_map"]


def _thread_label_map(ledger: Ledger) -> dict[str, str]:
    """``timeline`` rows key threads by ``id``; the board keys them by ``code``."""
    return {t.id: t.label for t in ledger.threads}


# ======================================================================================
# index.html — the command centre
# ======================================================================================


def build_index(ledger: Ledger) -> tuple[str, str, dict[str, Any]]:
    stats = ledger.stats()
    latest = ledger.latest_archive
    threads = ledger.threads

    line = latest.bottom_line if latest is not None else ""
    line_date = latest.date if latest is not None else ledger.last_updated
    correction = (
        f'<div class="notice"><div class="n-label">Correction carried in this brief</div>'
        f"{esc(latest.headline_correction)}</div>"
        if latest is not None and latest.headline_correction
        else ""
    )

    cards = [
        (
            "strategic-threat-briefing.html",
            "01 — Standing picture",
            "Dashboard",
            "The map, the full chronology from 2016 forward, thirteen actor and theatre "
            "briefings, and every primary document behind them.",
            str(stats.timeline_events + stats.additions),
            "events on the timeline",
        ),
        (
            "node-map.html",
            "02 — Relationships",
            "Node Map",
            "Every region and actor as a graph. Click a node for its history, what has "
            "moved since the founding documents, and what is dated ahead.",
            str(stats.node_edges),
            "tracked connections between actors",
        ),
        (
            "brief-archive.html",
            "03 — The run of briefs",
            "Archive",
            "Every brief, browsable by date, with a catch-up digest that collapses any "
            "window down to net thread movement and the items that caused it.",
            str(stats.archive_entries),
            "briefs filed to date",
        ),
    ]
    card_html = "".join(
        f'<a class="card" href="{attr(href)}">'
        f'<div class="c-eyebrow">{esc(eyebrow)}</div>'
        f'<div class="c-title">{esc(title)}</div>'
        f'<p class="c-desc">{esc(desc)}</p>'
        f'<div class="c-stat"><span class="c-statnum">{esc(num)}</span>'
        f'<span class="c-statlabel">{esc(label)}</span></div></a>'
        for href, eyebrow, title, desc, num, label in cards
    )

    moved = _threads_moved(ledger)
    moved_note = (
        "Moved in the latest brief: " + ", ".join(moved) if moved else "No thread moved in the latest brief."
    )

    body = (
        C.masthead(
            eyebrow="Command centre",
            title_html='Strategic Threat<br><span class="accent">&amp; Posture</span>',
            subtitle=(
                "The front door. Today's bottom line, where all ten threads stand, and a way "
                "into everything else. If you read one page, read this one."
            ),
            byline=[
                ("Brief", str(stats.brief_number)),
                ("Information cutoff", ledger.last_cutoff),
                ("Cutoff age", C.cutoff_age_note(ledger.last_cutoff)),
                ("Ledger updated", ledger.last_updated),
                ("Revision", ledger.revision),
            ],
        )
        + C.stat_strip(
            [
                (str(stats.brief_number), "Briefs filed"),
                (str(stats.threads), "Threads tracked daily"),
                (str(stats.current_sources), "Current primary documents"),
                (str(stats.verification_checks), "Verification checks logged"),
                (str(stats.horizon), "Dated items on the horizon"),
            ]
        )
        + '<main class="wrap">'
        + f'<section id="bottom-line">{C.bottom_line(f"Bottom line — brief {stats.brief_number}, {line_date}", line)}'
        + (f"<div style=\"margin-top:14px\">{correction}</div>" if correction else "")
        + "</section>"
        + f'<section id="board">{C.movement_board(threads)}'
        + f'<p class="sec-desc" style="margin-top:14px">{esc(moved_note)}</p></section>'
        + f'<section id="ways-in"><div class="grid cols-3">{card_html}</div></section>'
        + "</main>"
    )
    counts = {
        "brief_number": stats.brief_number,
        "threads": stats.threads,
        "archive_entries": stats.archive_entries,
    }
    return body, "", counts


def _threads_moved(ledger: Ledger) -> list[str]:
    """Codes whose intensity or direction differs between the last two archive entries."""
    entries = ledger.archive_sorted(newest_first=True)
    if len(entries) < 2:
        return []
    latest, previous = entries[0], entries[1]
    moved: list[str] = []
    for code, value in latest.threads.items():
        was = previous.threads.get(code)
        if was is not None and list(was) != list(value):
            moved.append(f"{code} {was[0]}/{was[1]} → {value[0]}/{value[1]}")
    return moved


# ======================================================================================
# strategic-threat-briefing.html — the dashboard
# ======================================================================================


def build_dashboard(ledger: Ledger) -> tuple[str, str, dict[str, Any]]:
    stats = ledger.stats()
    events = ledger.all_events()
    labels = _thread_label_map(ledger)

    filter_buttons = "".join(
        f'<button class="fbtn" type="button" data-filter="{attr(t.id)}" '
        f'aria-pressed="false">{esc(t.code)} &middot; {esc(t.label)}</button>'
        for t in ledger.threads
    )
    legend = "".join(
        f'<span class="lg"><span class="dot" style="background:{CATEGORY_COLORS.get(cat, "var(--dim)")}">'
        f"</span>{esc(cat)}</span>"
        for cat in sorted({n.cat for n in ledger.map_nodes})
    )
    node_lookup = {
        n.id: {"label": n.label, "cat": n.cat, "brief": n.brief, "link": n.link, "severity": n.severity}
        for n in ledger.map_nodes
    }

    body = (
        C.masthead(
            eyebrow="Standing picture",
            title_html='Strategic Threat<br><span class="accent">&amp; Posture Briefing</span>',
            subtitle=(
                "A compiled global map, chronological timeline, and set of detailed briefings "
                "synthesised from the current U.S. strategy and intelligence documents — built "
                "for one continuous read of where things stand and where they are heading."
            ),
            byline=[
                ("Brief", str(stats.brief_number)),
                ("Information cutoff", ledger.last_cutoff),
                ("Sources", f"{stats.current_sources} current primary documents"),
                ("Threads", f"{stats.threads} tracked daily"),
                ("Ledger updated", ledger.last_updated),
            ],
        )
        + C.stat_strip(
            [
                (str(stats.current_sources), "Current primary documents in the ledger"),
                (str(stats.threads), "Threads tracked daily"),
                (str(stats.timeline_events + stats.additions), "Events on the timeline"),
                (str(stats.verification_checks), "Verification checks logged"),
                (str(stats.revisions), "Judgments revised by a newer document"),
                (str(stats.horizon), "Dated items on the horizon"),
            ]
        )
        + '<main class="wrap">'
        # --- movement board
        + f'<section id="board">{C.movement_board(ledger.threads)}'
        + f'<div style="margin-top:22px">{C.thread_rows(ledger.threads)}</div></section>'
        # --- map
        + '<section id="map"><div class="sec-head">'
        '<div class="sec-eyebrow">01 — Global posture</div>'
        '<h2 class="sec-title">The strategic map</h2>'
        '<p class="sec-desc">A schematic — not geographic — layout of the regions and actors '
        "this operation tracks. Line colour is the kind of relationship; solid lines are "
        "alliance ties, dashed lines everything else. Click any node for its summary.</p></div>"
        f'<div class="maplegend">{legend}</div>'
        f'<div class="mapbox" id="mapbox">{C.map_svg(ledger.map_nodes, [e.raw for e in ledger.node_edges])}</div>'
        '<div class="mappanel" id="mappanel">'
        '<div class="mp-label" id="mp-cat">Select a node</div>'
        '<h4 id="mp-title">The strategic map</h4>'
        '<p id="mp-brief">Click or tab to any node above for a one-paragraph summary and a jump '
        "into its full briefing below.</p>"
        '<a class="jump" id="mp-jump" href="#briefings" hidden>Read the full briefing &darr;</a>'
        "</div></section>"
        # --- timeline
        + '<section id="timeline"><div class="sec-head">'
        '<div class="sec-eyebrow">02 — Chronology</div>'
        "<h2 class=\"sec-title\">What's happened, what's next</h2>"
        '<p class="sec-desc">Confirmed events run oldest first. Items marked '
        "<em>projected</em> are the documents' own stated goals, milestones and forecasts — "
        "not certainties. Filter by thread, or switch projected items off to see only what has "
        "already occurred.</p></div>"
        f'<div class="filterbar" id="filterbar">'
        f'<button class="fbtn" type="button" data-filter="*" aria-pressed="true">All threads</button>'
        f"{filter_buttons}</div>"
        '<div class="togglewrap">'
        '<div class="switch" id="futureToggle" role="switch" aria-pressed="true" tabindex="0">'
        '<div class="knob"></div></div><span>Show projected / forecast items</span></div>'
        f'<div class="rail" id="rail">{C.timeline_events(ledger, events, thread_labels=labels)}</div>'
        "</section>"
        # --- briefings
        + '<section id="briefings"><div class="sec-head">'
        '<div class="sec-eyebrow">03 — Detailed briefings</div>'
        '<h2 class="sec-title">Actor &amp; theatre briefings</h2>'
        f'<p class="sec-desc">{esc(str(stats.briefings))} briefings, synthesised and paraphrased '
        "from the source documents, each closing with a forward-looking assessment of likely "
        "near-term trajectory.</p></div>"
        f"{C.briefings_accordion(ledger.briefings)}</section>"
        # --- revisions
        + '<section id="revisions"><div class="sec-head">'
        '<div class="sec-eyebrow">04 — Changed judgments</div>'
        '<h2 class="sec-title">Where a newer document changed an older one</h2>'
        '<p class="sec-desc">The diff between an old and a new assessment is frequently more '
        "informative than the current snapshot, which is why superseded material is kept rather "
        "than deleted.</p></div>"
        f"{_revisions_table(ledger)}</section>"
        # --- horizon
        + '<section id="horizon"><div class="sec-head">'
        '<div class="sec-eyebrow">05 — Horizon</div>'
        '<h2 class="sec-title">Dated things ahead</h2>'
        '<p class="sec-desc">Nearest first. Every forward-looking item carries a confidence tag: '
        "a stated goal is not a prediction and a projection is not a plan.</p></div>"
        f"{_horizon_table(ledger)}</section>"
        # --- sources
        + '<section id="sources"><div class="sec-head">'
        '<div class="sec-eyebrow">06 — Primary documents</div>'
        '<h2 class="sec-title">Everything this is built on</h2>'
        '<p class="sec-desc">Superseded documents are retained deliberately and marked with what '
        "replaced them.</p></div>"
        f"{C.sources_table(ledger.sources)}</section>"
        + "</main>"
    )

    script = f"""<script>
(function(){{
  "use strict";
  var NODES = {json_literal(node_lookup)};
  var rail = document.getElementById("rail");
  var filterbar = document.getElementById("filterbar");
  var toggle = document.getElementById("futureToggle");
  var state = {{ thread: "*", future: true }};

  function apply(){{
    var rows = rail.querySelectorAll(".event");
    var shown = 0;
    for (var i = 0; i < rows.length; i++) {{
      var row = rows[i];
      var okThread = state.thread === "*" || row.dataset.thread === state.thread;
      var okFuture = state.future || row.dataset.future !== "1";
      var visible = okThread && okFuture;
      row.hidden = !visible;
      if (visible) shown++;
    }}
    var empty = document.getElementById("rail-empty");
    if (!empty) {{
      empty = document.createElement("div");
      empty.id = "rail-empty";
      empty.className = "emptystate";
      empty.textContent = "No events match the current filter.";
      rail.appendChild(empty);
    }}
    empty.hidden = shown !== 0;
  }}

  filterbar.addEventListener("click", function(ev){{
    var btn = ev.target.closest("[data-filter]");
    if (!btn) return;
    state.thread = btn.dataset.filter;
    var all = filterbar.querySelectorAll("[data-filter]");
    for (var i = 0; i < all.length; i++) {{
      all[i].setAttribute("aria-pressed", String(all[i] === btn));
    }}
    apply();
  }});

  function flipFuture(){{
    state.future = !state.future;
    toggle.setAttribute("aria-pressed", String(state.future));
    apply();
  }}
  toggle.addEventListener("click", flipFuture);
  toggle.addEventListener("keydown", function(ev){{
    if (ev.key === " " || ev.key === "Enter") {{ ev.preventDefault(); flipFuture(); }}
  }});

  var mapbox = document.getElementById("mapbox");
  var mpCat = document.getElementById("mp-cat");
  var mpTitle = document.getElementById("mp-title");
  var mpBrief = document.getElementById("mp-brief");
  var mpJump = document.getElementById("mp-jump");

  function selectNode(id){{
    var node = NODES[id];
    if (!node) return;
    var groups = mapbox.querySelectorAll(".node");
    for (var i = 0; i < groups.length; i++) {{
      groups[i].setAttribute("aria-current", String(groups[i].dataset.node === id));
    }}
    mpCat.textContent = node.cat + " \\u00b7 severity " + node.severity + "/10";
    mpTitle.textContent = node.label;
    mpBrief.textContent = node.brief;
    if (node.link) {{ mpJump.href = node.link; mpJump.hidden = false; }}
    else {{ mpJump.hidden = true; }}
  }}

  mapbox.addEventListener("click", function(ev){{
    var g = ev.target.closest(".node");
    if (g) selectNode(g.dataset.node);
  }});
  mapbox.addEventListener("keydown", function(ev){{
    var g = ev.target.closest(".node");
    if (g && (ev.key === "Enter" || ev.key === " ")) {{ ev.preventDefault(); selectNode(g.dataset.node); }}
  }});

  apply();
}})();
</script>"""

    counts = {
        "brief_number": stats.brief_number,
        "threads": stats.threads,
        "timeline_events": stats.timeline_events + stats.additions,
        "sources": stats.total_sources,
        "briefings": stats.briefings,
        "map_nodes": stats.map_nodes,
        "node_edges": stats.node_edges,
        "horizon": stats.horizon,
        "revisions": stats.revisions,
    }
    return body, script, counts


def _revisions_table(ledger: Ledger) -> str:
    rows: list[str] = []
    for revision in ledger.revisions:
        was = str(revision.get("was") or revision.get("supersedes") or "")
        now = str(revision.get("now") or revision.get("revision") or "")
        basis = str(revision.get("basis") or revision.get("why_it_changed") or "")
        significance = str(revision.get("significance") or revision.get("attribution_class") or "")
        rows.append(
            "<tr>"
            f'<td class="mono">{esc(revision.get("date"))}</td>'
            f'<td><b>{esc(revision.get("topic") or revision.get("thread"))}</b></td>'
            f"<td>{esc(was)}</td>"
            f"<td><b>{esc(now)}</b>{'<br>' + esc(basis) if basis else ''}</td>"
            f'<td><span class="pill">{esc(significance)}</span></td>'
            "</tr>"
        )
    return (
        '<div class="tablewrap"><table class="table">'
        "<thead><tr><th>Date</th><th>Topic</th><th>Was</th><th>Now</th><th>Weight</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _horizon_table(ledger: Ledger) -> str:
    labels = _thread_label_map(ledger)
    rows: list[str] = []
    for item in ledger.horizon_sorted():
        rows.append(
            "<tr>"
            f'<td class="mono">{esc(item.when)}</td>'
            f"<td>{esc(labels.get(item.thread, item.thread))}</td>"
            f"<td><b>{esc(item.item)}</b>{'<br>' + esc(item.note) if item.note else ''}</td>"
            f'<td><span class="pill">{esc(item.confidence)}</span></td>'
            "</tr>"
        )
    return (
        '<div class="tablewrap"><table class="table">'
        "<thead><tr><th>When</th><th>Thread</th><th>Item</th><th>Confidence</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


# ======================================================================================
# brief-archive.html
# ======================================================================================


def build_archive(ledger: Ledger) -> tuple[str, str, dict[str, Any]]:
    stats = ledger.stats()
    entries = ledger.archive_sorted(newest_first=True)
    by_number = {e.number: e for e in entries}

    cards: list[str] = []
    digest_payload: list[dict[str, Any]] = []
    for entry in entries:
        previous = by_number.get(entry.number - 1)
        resolved = entry.resolve_file(ledger.root)
        href = (
            f'briefs/{entry.brief_filename}'
            if resolved is not None
            else ""
        )
        title = (
            f'<a href="{attr(href)}">{esc(entry.date)} &middot; {esc(entry.weekday)}</a>'
            if href
            else f"{esc(entry.date)} &middot; {esc(entry.weekday)}"
        )
        items_html: list[str] = []
        for item in entry.sorted_items():
            late = '<span class="pill late">late file</span> ' if item.is_late_file else ""
            items_html.append(
                '<div class="bc-item"><div class="bi-head">'
                f'<span class="bi-n">{esc(item.n)}</span>'
                f'<span class="chip">{esc(item.thread)}</span>'
                f'<span class="bi-title">{late}{esc(item.head)}</span></div>'
                f'<div class="bi-sowhat"><b>So what</b> &mdash; {esc(item.sowhat)}</div></div>'
            )
        correction = (
            f'<div class="notice" style="margin-top:14px">'
            f'<div class="n-label">Correction</div>{esc(entry.headline_correction)}</div>'
            if entry.headline_correction
            else ""
        )
        verification = ", ".join(
            f"{esc(k)}: {esc(v)}" for k, v in entry.verification.items()
        )
        cards.append(
            f'<article class="briefcard" id="brief-{entry.number:03d}" data-number="{entry.number}" '
            f'data-date="{attr(entry.date)}">'
            '<div class="bc-head">'
            f'<span class="bc-num">Brief {entry.number:03d}</span>'
            f'<span class="bc-date">{title}</span>'
            f'<span class="bc-cutoff">cutoff {esc(entry.cutoff)}</span></div>'
            f'<p class="bc-bl">{esc(entry.bottom_line)}</p>'
            f"{C.archive_thread_strip(entry, previous)}"
            f'<div class="bc-items">{"".join(items_html)}</div>'
            f"{correction}"
            + (
                f'<p class="bc-bl" style="font-size:12.5px;color:var(--faint);margin-top:12px">'
                f"Verification &mdash; {verification}</p>"
                if verification
                else ""
            )
            + "</article>"
        )
        digest_payload.append(
            {
                "number": entry.number,
                "date": entry.date,
                "cutoff": entry.cutoff,
                "bottom_line": entry.bottom_line,
                "threads": {k: list(v) for k, v in entry.threads.items()},
                "items": [
                    {"n": i.n, "thread": i.thread, "head": i.head, "sowhat": i.sowhat}
                    for i in entry.sorted_items()
                ],
            }
        )

    retracted = sorted((ledger.root / "briefs").glob("RETRACTED-*.html")) if (
        ledger.root / "briefs"
    ).is_dir() else []
    retracted_html = ""
    if retracted:
        links = ", ".join(
            f'<a href="briefs/{attr(p.name)}">{esc(p.name)}</a>' for p in retracted
        )
        retracted_html = (
            '<div class="notice" style="margin-bottom:22px">'
            '<div class="n-label">Retracted, preserved, never deleted</div>'
            f"A brief produced against a stale ledger copy during the 16 August 2026 fork is kept "
            f"here with its own retraction notice rather than removed: {links}. "
            "A brief revised after the fact stops being evidence of what was known when.</div>"
        )

    body = (
        C.masthead(
            eyebrow="The run of briefs",
            title_html='Brief <span class="accent">Archive</span>',
            subtitle=(
                "Every brief filed, newest first — and a catch-up digest that collapses any "
                "window down to the net thread movement across it and the items that caused it. "
                "Reading one brief a day does not scale to someone who missed four."
            ),
            byline=[
                ("Briefs filed", str(stats.archive_entries)),
                ("Latest", entries[0].date if entries else "—"),
                ("Information cutoff", ledger.last_cutoff),
                ("Ledger updated", ledger.last_updated),
            ],
        )
        + '<main class="wrap"><section id="digest">'
        '<div class="sec-head"><div class="sec-eyebrow">Catch-up</div>'
        '<h2 class="sec-title">What did I miss?</h2>'
        '<p class="sec-desc">Pick a window. The digest reports net thread movement across it — '
        "start state to end state — and every item filed inside it, in one read.</p></div>"
        '<div class="digestbar">'
        '<div class="field"><label for="digest-window">Window</label>'
        '<select id="digest-window">'
        '<option value="1">Since yesterday</option>'
        '<option value="3" selected>Last 3 briefs</option>'
        '<option value="7">Last 7 briefs</option>'
        '<option value="all">Everything</option>'
        '<option value="since">Since a date…</option>'
        "</select></div>"
        '<div class="field" id="since-field" hidden><label for="digest-since">From date</label>'
        '<input type="date" id="digest-since"></div>'
        "</div>"
        '<div class="digestout" id="digest-out"></div></section>'
        f'<section id="briefs">{retracted_html}'
        '<div class="sec-head"><div class="sec-eyebrow">Full run</div>'
        '<h2 class="sec-title">Every brief, newest first</h2></div>'
        f'{"".join(cards)}</section></main>'
    )

    script = f"""<script>
(function(){{
  "use strict";
  var BRIEFS = {json_literal(digest_payload)};
  var sel = document.getElementById("digest-window");
  var sinceField = document.getElementById("since-field");
  var sinceInput = document.getElementById("digest-since");
  var out = document.getElementById("digest-out");
  var ARROWS = {json_literal(C.ARROWS)};

  function esc(s){{
    return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){{
      return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c];
    }});
  }}

  function selected(){{
    var v = sel.value;
    if (v === "all") return BRIEFS.slice();
    if (v === "since") {{
      var from = sinceInput.value;
      if (!from) return [];
      return BRIEFS.filter(function(b){{ return b.date >= from; }});
    }}
    return BRIEFS.slice(0, parseInt(v, 10));
  }}

  function render(){{
    sinceField.hidden = sel.value !== "since";
    var window_ = selected();
    if (!window_.length) {{
      out.innerHTML = '<div class="emptystate">No briefs in that window.</div>';
      return;
    }}
    // BRIEFS is newest-first, so the window's start state is its last element's
    // predecessor-facing snapshot and the end state is its first element's.
    var newest = window_[0];
    var oldest = window_[window_.length - 1];
    var baseIndex = BRIEFS.indexOf(oldest) + 1;
    var base = baseIndex < BRIEFS.length ? BRIEFS[baseIndex] : null;

    var moved = [];
    var held = [];
    Object.keys(newest.threads).forEach(function(code){{
      var end = newest.threads[code];
      var start = base ? base.threads[code] : null;
      if (start && (start[0] !== end[0] || start[1] !== end[1])) {{
        moved.push(
          '<span class="chip moved">' + esc(code) + " " +
          esc(start[0]) + esc(ARROWS[start[1]] || "?") + " \\u2192 " +
          esc(end[0]) + esc(ARROWS[end[1]] || "?") + "</span>"
        );
      }} else {{
        held.push('<span class="chip">' + esc(code) + " " + esc(end[0]) +
          esc(ARROWS[end[1]] || "?") + "</span>");
      }}
    }});

    var items = [];
    window_.forEach(function(b){{
      b.items.forEach(function(it){{
        items.push(
          '<div class="bc-item"><div class="bi-head">' +
          '<span class="bi-n">' + esc(b.date) + " / " + esc(it.n) + "</span>" +
          '<span class="chip">' + esc(it.thread) + "</span>" +
          '<span class="bi-title">' + esc(it.head) + "</span></div>" +
          '<div class="bi-sowhat"><b>So what</b> \\u2014 ' + esc(it.sowhat) + "</div></div>"
        );
      }});
    }});

    out.innerHTML =
      '<div class="panel"><div class="c-eyebrow">' +
      esc(window_.length) + " brief" + (window_.length === 1 ? "" : "s") + " \\u00b7 " +
      esc(oldest.date) + " \\u2192 " + esc(newest.date) +
      "</div>" +
      '<p class="bc-bl" style="margin-top:12px">' + esc(newest.bottom_line) + "</p>" +
      '<div class="c-eyebrow" style="margin-top:18px">Net movement across the window</div>' +
      '<div class="bc-strip">' + (moved.length ? moved.join("") :
        '<span class="chip">no thread changed</span>') + "</div>" +
      '<div class="c-eyebrow" style="margin-top:14px">Held</div>' +
      '<div class="bc-strip">' + held.join("") + "</div>" +
      '<div class="c-eyebrow" style="margin-top:18px">' + esc(items.length) +
      " item" + (items.length === 1 ? "" : "s") + " filed in this window</div>" +
      '<div class="bc-items">' + items.join("") + "</div></div>";
  }}

  sel.addEventListener("change", render);
  sinceInput.addEventListener("change", render);
  render();
}})();
</script>"""

    counts = {
        "brief_number": stats.brief_number,
        "archive_entries": stats.archive_entries,
        "threads": stats.threads,
    }
    return body, script, counts


# ======================================================================================
# node-map.html
# ======================================================================================


def build_node_map(ledger: Ledger) -> tuple[str, str, dict[str, Any]]:
    stats = ledger.stats()
    now = datetime.now(timezone.utc)
    history = ledger.node_history

    payload: dict[str, Any] = {}
    for node in ledger.map_nodes:
        events = ledger.events_for_node(node.id)
        recent = [e for e in events if not e.future]
        payload[node.id] = {
            "label": node.label,
            "cat": node.cat,
            "brief": node.brief,
            "severity": node.severity,
            "x": node.x,
            "y": node.y,
            "history": [
                {
                    "date": h.date,
                    "ago": C.humanize_ago(h.date, now=now),
                    "title": h.title,
                    "text": h.text,
                    "tier": h.tier,
                    "source_title": h.source_title,
                    "source_url": h.source_url,
                }
                for h in history.get(node.id, [])
            ],
            "recent": [
                {
                    "date": e.date,
                    "ago": C.humanize_ago(e.date, now=now),
                    "title": e.title,
                    "text": e.text,
                    "tier": e.attribution_class or "",
                }
                for e in sorted(recent, key=lambda e: e.sort_key, reverse=True)[:14]
            ],
            "future": [
                {
                    "date": h.when,
                    "ago": "",
                    "title": h.item,
                    "text": h.note,
                    "tier": h.confidence,
                }
                for h in ledger.horizon_for_node(node.id)
            ],
        }

    edges_payload = [
        {"from": e.frm, "to": e.to, "type": e.type, "label": e.label}
        for e in ledger.node_edges
        if e.frm in ledger.node_ids and e.to in ledger.node_ids
    ]

    legend = "".join(
        f'<span class="lg"><span class="dot" style="background:{EDGE_COLORS.get(t, "var(--dim)")}">'
        f"</span>{esc(t)}</span>"
        for t in sorted({e.type for e in ledger.node_edges})
    )

    body = (
        C.masthead(
            eyebrow="Relationships",
            title_html='Node <span class="accent">Map</span>',
            subtitle=(
                "Every region and actor as a force-directed graph — sized and coloured by "
                "severity, connected by how they actually relate. Click a node for its full "
                "deep dive, so a region's present posture is never read apart from how it got "
                "there and where it is heading."
            ),
            byline=[
                ("Nodes", str(stats.map_nodes)),
                ("Connections", str(stats.node_edges)),
                ("Archival entries", str(stats.node_history_entries)),
                ("Information cutoff", ledger.last_cutoff),
            ],
        )
        + '<main class="wrap"><section id="graph">'
        f'<div class="maplegend">{legend}</div>'
        '<div class="mapbox" id="graphbox">'
        '<svg id="graphsvg" viewBox="0 0 1000 560" preserveAspectRatio="xMidYMid meet" '
        'role="group" aria-label="Force-directed graph of tracked actors"></svg></div>'
        '<p class="sec-desc" style="margin-top:12px">Drag a node to reposition it; the layout '
        "settles around wherever you leave it. Positions are seeded from the schematic map so the "
        "graph opens in a recognisable arrangement rather than a random one.</p>"
        "</section>"
        '<section id="dive"><div class="sec-head">'
        '<div class="sec-eyebrow">Deep dive</div>'
        '<h2 class="sec-title" id="dive-title">Select a node</h2>'
        '<p class="sec-desc" id="dive-brief">Every timeline shown below is computed from the '
        "ledger through <span class=\"mono\">node_topics</span> — history, what has moved since "
        "the founding documents, and what is dated ahead. Only the archival background and the "
        "connections themselves are hand-curated.</p></div>"
        '<div class="dive" id="dive-body"></div></section></main>'
    )

    script = f"""<script>
(function(){{
  "use strict";
  var NODES = {json_literal(payload)};
  var EDGES = {json_literal(edges_payload)};
  var EDGE_COLORS = {json_literal({k: v for k, v in EDGE_COLORS.items()})};
  var CAT_COLORS = {json_literal({k: v for k, v in CATEGORY_COLORS.items()})};
  var svg = document.getElementById("graphsvg");
  var NS = "http://www.w3.org/2000/svg";
  var W = 1000, H = 560;

  var ids = Object.keys(NODES);
  // Seed from the schematic map coordinates (0-1000 x 0-460) scaled into this viewBox, so
  // the simulation refines a recognisable arrangement instead of inventing a new one.
  var sim = ids.map(function(id){{
    var n = NODES[id];
    return {{ id: id, x: n.x, y: n.y * (H / 460) * 0.9 + 30, vx: 0, vy: 0, r: 6 + n.severity * 1.4 }};
  }});
  var index = {{}};
  sim.forEach(function(p){{ index[p.id] = p; }});
  var links = EDGES.map(function(e){{
    return {{ s: index[e.from], t: index[e.to], type: e.type, label: e.label }};
  }}).filter(function(l){{ return l.s && l.t; }});

  var gLinks = document.createElementNS(NS, "g");
  var gNodes = document.createElementNS(NS, "g");
  svg.appendChild(gLinks); svg.appendChild(gNodes);

  var lineEls = links.map(function(l){{
    var el = document.createElementNS(NS, "line");
    el.setAttribute("stroke", EDGE_COLORS[l.type] || "var(--hair)");
    el.setAttribute("stroke-width", "1");
    el.setAttribute("opacity", "0.5");
    if (l.type !== "alliance") el.setAttribute("stroke-dasharray", "5 5");
    var title = document.createElementNS(NS, "title");
    title.textContent = l.label || l.type;
    el.appendChild(title);
    gLinks.appendChild(el);
    return el;
  }});

  var nodeEls = sim.map(function(p){{
    var n = NODES[p.id];
    var g = document.createElementNS(NS, "g");
    g.setAttribute("class", "node");
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "button");
    g.setAttribute("aria-label", n.label);
    g.dataset.node = p.id;
    var c = document.createElementNS(NS, "circle");
    c.setAttribute("r", String(p.r));
    c.setAttribute("fill", CAT_COLORS[n.cat] || "var(--dim)");
    c.setAttribute("fill-opacity", "0.75");
    c.setAttribute("stroke", CAT_COLORS[n.cat] || "var(--dim)");
    var t = document.createElementNS(NS, "text");
    t.setAttribute("dy", String(p.r + 11));
    t.textContent = n.label;
    g.appendChild(c); g.appendChild(t);
    gNodes.appendChild(g);
    return g;
  }});

  var dragging = null;

  function tick(){{
    // Repulsion between every pair, spring along every edge, weak pull to centre.
    for (var i = 0; i < sim.length; i++) {{
      for (var j = i + 1; j < sim.length; j++) {{
        var a = sim[i], b = sim[j];
        var dx = b.x - a.x, dy = b.y - a.y;
        var d2 = dx * dx + dy * dy || 0.01;
        var d = Math.sqrt(d2);
        var force = 2600 / d2;
        var fx = (dx / d) * force, fy = (dy / d) * force;
        a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy;
      }}
    }}
    links.forEach(function(l){{
      var dx = l.t.x - l.s.x, dy = l.t.y - l.s.y;
      var d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      var force = (d - 150) * 0.008;
      var fx = (dx / d) * force, fy = (dy / d) * force;
      l.s.vx += fx; l.s.vy += fy; l.t.vx -= fx; l.t.vy -= fy;
    }});
    sim.forEach(function(p){{
      p.vx += (W / 2 - p.x) * 0.0012;
      p.vy += (H / 2 - p.y) * 0.0012;
      if (p === dragging) {{ p.vx = 0; p.vy = 0; return; }}
      p.vx *= 0.82; p.vy *= 0.82;
      p.x = Math.max(p.r + 30, Math.min(W - p.r - 30, p.x + p.vx));
      p.y = Math.max(p.r + 14, Math.min(H - p.r - 20, p.y + p.vy));
    }});
    for (var k = 0; k < lineEls.length; k++) {{
      lineEls[k].setAttribute("x1", links[k].s.x); lineEls[k].setAttribute("y1", links[k].s.y);
      lineEls[k].setAttribute("x2", links[k].t.x); lineEls[k].setAttribute("y2", links[k].t.y);
    }}
    for (var m = 0; m < nodeEls.length; m++) {{
      nodeEls[m].setAttribute("transform", "translate(" + sim[m].x + "," + sim[m].y + ")");
    }}
  }}

  var frames = 0;
  function loop(){{
    tick();
    // Settle, then stop: an animation that never ends burns battery on a page people leave
    // open all day. Dragging restarts it.
    if (++frames < 600 || dragging) requestAnimationFrame(loop);
  }}
  requestAnimationFrame(loop);

  function svgPoint(ev){{
    var rect = svg.getBoundingClientRect();
    return {{
      x: (ev.clientX - rect.left) / rect.width * W,
      y: (ev.clientY - rect.top) / rect.height * H
    }};
  }}

  svg.addEventListener("pointerdown", function(ev){{
    var g = ev.target.closest(".node");
    if (!g) return;
    dragging = index[g.dataset.node];
    svg.setPointerCapture(ev.pointerId);
    frames = 0; requestAnimationFrame(loop);
  }});
  svg.addEventListener("pointermove", function(ev){{
    if (!dragging) return;
    var p = svgPoint(ev);
    dragging.x = p.x; dragging.y = p.y;
  }});
  svg.addEventListener("pointerup", function(ev){{
    if (dragging) {{ svg.releasePointerCapture(ev.pointerId); dragging = null; frames = 0; requestAnimationFrame(loop); }}
  }});

  var diveTitle = document.getElementById("dive-title");
  var diveBrief = document.getElementById("dive-brief");
  var diveBody = document.getElementById("dive-body");

  function esc(s){{
    return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){{
      return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c];
    }});
  }}

  function columnInner(heading, rows, emptyText){{
    if (!rows.length) {{
      return "<h5>" + esc(heading) + "</h5>" +
        '<div class="emptystate">' + esc(emptyText) + "</div>";
    }}
    var body = rows.map(function(r){{
      var src = "";
      if (r.source_url) {{
        src = '<div class="di-src"><a href="' + esc(r.source_url) +
          '" rel="noopener noreferrer" target="_blank">' + esc(r.source_title || r.source_url) + "</a></div>";
      }} else if (r.source_title) {{
        src = '<div class="di-src">' + esc(r.source_title) + "</div>";
      }}
      var tier = r.tier ? '<span class="pill tier-' + esc(r.tier) + '">' + esc(r.tier) + "</span>" : "";
      return '<div class="diveitem"><div class="di-date">' + esc(r.date) +
        (r.ago ? '<span class="di-ago">' + esc(r.ago) + "</span>" : "") + "</div>" +
        '<div class="di-title">' + esc(r.title) + "</div>" +
        (r.text ? '<div class="di-text">' + esc(r.text) + "</div>" : "") +
        (tier ? '<div class="di-src">' + tier + "</div>" : "") + src + "</div>";
    }}).join("");
    return "<h5>" + esc(heading) + "</h5>" + body;
  }}

  function column(heading, rows, emptyText){{
    return '<div class="divecol">' + columnInner(heading, rows, emptyText) + "</div>";
  }}

  function select(id){{
    var n = NODES[id];
    if (!n) return;
    nodeEls.forEach(function(g){{ g.setAttribute("aria-current", String(g.dataset.node === id)); }});
    diveTitle.textContent = n.label;
    diveBrief.textContent = n.brief;
    // Left column is the hand-curated archival background; right column stacks the two
    // derived timelines (what has moved, what is dated ahead) under one another.
    diveBody.innerHTML =
      column("Archival background", n.history, "No archival background curated for this node yet.") +
      '<div class="divecol">' +
      columnInner("Since the founding documents", n.recent, "Nothing on the timeline maps to this node.") +
      '<div style="margin-top:22px"></div>' +
      columnInner("Dated ahead", n.future, "Nothing dated ahead for this node.") +
      "</div>";
    if (history.replaceState) history.replaceState(null, "", "#node-" + id);
  }}

  svg.addEventListener("click", function(ev){{
    var g = ev.target.closest(".node");
    if (g) select(g.dataset.node);
  }});
  svg.addEventListener("keydown", function(ev){{
    var g = ev.target.closest(".node");
    if (g && (ev.key === "Enter" || ev.key === " ")) {{ ev.preventDefault(); select(g.dataset.node); }}
  }});

  var fromHash = (location.hash || "").replace(/^#node-/, "");
  select(NODES[fromHash] ? fromHash : ids[0]);
}})();
</script>"""

    counts = {
        "brief_number": stats.brief_number,
        "map_nodes": stats.map_nodes,
        "node_edges": stats.node_edges,
        "node_history_entries": stats.node_history_entries,
    }
    return body, script, counts
