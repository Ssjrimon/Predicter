"""``build_app.py`` — ledger to ``natdef-console.html``, the offline console.

BRIEFING-PROTOCOL.md, Step 6: "``build_app.py`` bakes a full copy of the ledger into
``natdef-console.html``, so unlike the dashboard it goes stale on **every** ledger write,
not only when the picture shifts — rebuild it each brief. It refuses to build on a
malformed ledger (wrong root type, a list key holding an object, a missing
``ledger_meta``), so a bad write fails at the command line rather than silently in the
browser, and ``python3 build_app.py --check`` exits 3 when the built file is behind the
ledger."

All three of those properties are implemented here. The refusal is
:meth:`natdef.ledger.Ledger.load`'s schema gate; ``--check`` compares the baked ledger
against the ledger on disk and exits 3 on any difference.

The console is one file holding every view — the command centre, the dashboard, the node
map and the archive — behind a tab bar, plus the raw ledger itself. It exists for the case
the four separate pages do not cover: a single file you can put on a USB stick, mail to
someone, or open on a machine with no network and no copy of this repository, and still
have the whole picture. Step 7 is explicit that it is never filed alongside the briefs,
precisely because it duplicates the ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from . import __version__, pages
from .errors import NatDefError
from .ledger import Ledger, default_ledger_path
from .template import attr, esc, json_literal
from .theme import CSS

__all__ = ["build_console", "console_is_current", "main", "CONSOLE_FILENAME"]

CONSOLE_FILENAME = "natdef-console.html"

#: The baked ledger's fingerprint, written into the console so ``--check`` can compare
#: without re-parsing a 400KB embedded JSON blob out of the markup.
_FINGERPRINT_RE = re.compile(r'<meta\s+name="natdef:ledger-sha256"\s+content="([0-9a-f]{64})"')

#: Tab id -> (label, page builder). Order is the tab order.
_VIEWS: tuple[tuple[str, str], ...] = (
    ("home", "Command Center"),
    ("dashboard", "Dashboard"),
    ("nodemap", "Node Map"),
    ("archive", "Archive"),
    ("ledger", "Ledger"),
)


@dataclass(frozen=True)
class BuildResult:
    path: Path
    html: str
    fingerprint: str
    was_current: bool

    @property
    def size(self) -> int:
        return len(self.html.encode("utf-8"))


def ledger_fingerprint(ledger: Ledger) -> str:
    """A stable SHA-256 over the ledger's content, independent of key order and whitespace."""
    canonical = json.dumps(ledger.data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ledger_view(ledger: Ledger) -> str:
    """The raw-ledger tab: what is baked in, and how to get it back out."""
    stats = ledger.stats()
    rows = [
        ("brief_number", stats.brief_number),
        ("last_cutoff", ledger.last_cutoff),
        ("last_updated", ledger.last_updated),
        ("revision", ledger.revision),
        ("threads", stats.threads),
        ("sources", f"{stats.total_sources} ({stats.current_sources} current)"),
        ("timeline", stats.timeline_events),
        ("timeline_additions_2026", stats.additions),
        ("horizon", stats.horizon),
        ("archive", stats.archive_entries),
        ("verification_log", stats.verification_checks),
        ("map_nodes", stats.map_nodes),
        ("node_edges", stats.node_edges),
        ("node_history entries", stats.node_history_entries),
        ("briefings", stats.briefings),
        ("revisions", stats.revisions),
        ("standing_watchlist", stats.watchlist),
    ]
    table = "".join(
        f'<tr><td class="mono">{esc(key)}</td><td><b>{esc(value)}</b></td></tr>' for key, value in rows
    )
    watchlist = "".join(f"<li>{esc(item)}</li>" for item in ledger.standing_watchlist)
    notes = "".join(
        f'<tr><td class="mono">{esc(note.get("date"))}</td><td>{esc(note.get("note"))}</td></tr>'
        for note in ledger.schema_notes
    )
    log = "".join(
        f'<tr><td class="mono">{esc(entry.get("date"))}</td>'
        f'<td><b>{esc(entry.get("claim"))}</b><br>{esc(entry.get("finding"))}</td>'
        f'<td><span class="pill tier-{attr(entry.get("class"))}">{esc(entry.get("class"))}</span>'
        f'<br>{esc(entry.get("result"))}</td></tr>'
        for entry in reversed(ledger.verification_log)
    )
    return (
        '<main class="wrap"><section><div class="sec-head">'
        '<div class="sec-eyebrow">Baked ledger</div>'
        '<h2 class="sec-title">The whole ledger, inside this file</h2>'
        '<p class="sec-desc">This console carries a complete copy of '
        "<span class=\"mono\">intel-ledger.json</span> as of the build below. That is what makes "
        "it work with no network and no repository — and also why it goes stale on every ledger "
        "write, not only when the picture shifts. Rebuild it each brief.</p></div>"
        '<div class="grid cols-2">'
        f'<div class="panel"><div class="c-eyebrow">Contents</div>'
        f'<div class="tablewrap"><table class="table"><tbody>{table}</tbody></table></div></div>'
        f'<div class="panel"><div class="c-eyebrow">Standing watchlist</div>'
        f'<ul style="margin:12px 0 0;padding-left:20px;color:var(--dim);font-size:13.5px">'
        f"{watchlist}</ul></div></div>"
        '<div class="panel" style="margin-top:16px"><div class="c-eyebrow">Schema notes</div>'
        f'<div class="tablewrap"><table class="table"><tbody>{notes}</tbody></table></div></div>'
        "</section>"
        '<section><div class="sec-head"><div class="sec-eyebrow">The record</div>'
        '<h2 class="sec-title">Verification log</h2>'
        '<p class="sec-desc">Every check run against a candidate claim, newest first — including '
        "the ones that passed, and every correction to an earlier brief. The log is part of the "
        "product.</p></div>"
        '<div class="tablewrap"><table class="table"><thead><tr><th>Date</th><th>Claim</th>'
        f"<th>Outcome</th></tr></thead><tbody>{log}</tbody></table></div></section></main>"
    )


def build_console(ledger: Ledger, *, generated_at: str | None = None) -> str:
    """Render the whole console to a single self-contained HTML string."""
    stamp = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    fingerprint = ledger_fingerprint(ledger)
    stats = ledger.stats()

    home_body, home_script, _ = pages.build_index(ledger)
    dash_body, dash_script, _ = pages.build_dashboard(ledger)
    node_body, node_script, _ = pages.build_node_map(ledger)
    arch_body, arch_script, _ = pages.build_archive(ledger)

    bodies = {
        "home": home_body,
        "dashboard": dash_body,
        "nodemap": node_body,
        "archive": arch_body,
        "ledger": _ledger_view(ledger),
    }
    # Every view's script runs at load. They are separate IIFEs scoped to their own view's
    # element ids, so tab switching only changes what is visible — no re-initialisation, and
    # no chance of one view's listeners being attached twice.
    scripts = "".join([home_script, dash_script, node_script, arch_script])

    tabs = "".join(
        f'<button class="fbtn" type="button" role="tab" data-view="{attr(view)}" '
        f'aria-pressed="{"true" if index == 0 else "false"}">{esc(label)}</button>'
        for index, (view, label) in enumerate(_VIEWS)
    )
    panels = "".join(
        f'<div class="view" data-view="{attr(view)}"{"" if index == 0 else " hidden"}>'
        f"{bodies[view]}</div>"
        for index, (view, _) in enumerate(_VIEWS)
    )

    switcher = """<script>
(function(){
  "use strict";
  var bar = document.getElementById("viewtabs");
  var views = document.querySelectorAll(".view");
  bar.addEventListener("click", function(ev){
    var btn = ev.target.closest("[data-view]");
    if (!btn) return;
    var want = btn.dataset.view;
    bar.querySelectorAll("[data-view]").forEach(function(b){
      b.setAttribute("aria-pressed", String(b === btn));
    });
    views.forEach(function(v){ v.hidden = v.dataset.view !== want; });
    window.scrollTo(0, 0);
  });
})();
</script>"""

    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Nat Def Console — brief {esc(stats.brief_number)}</title>\n"
        f'<meta name="generator" content="natdef build_app {esc(__version__)}">\n'
        f'<meta name="natdef:brief-number" content="{attr(stats.brief_number)}">\n'
        f'<meta name="natdef:cutoff" content="{attr(ledger.last_cutoff)}">\n'
        f'<meta name="natdef:generated" content="{attr(stamp)}">\n'
        f'<meta name="natdef:ledger-sha256" content="{attr(fingerprint)}">\n'
        f"<style>\n{CSS}\n.view[hidden]{{display:none!important}}\n</style>\n"
        "</head>\n<body>\n"
        '<div class="topbar"><div class="wrap">'
        '<span class="wordmark">Nat Def Console</span>'
        f'<nav id="viewtabs" role="tablist">{tabs}</nav>'
        "</div></div>\n"
        f"{panels}\n"
        '<footer class="wrap"><p>Offline console. Unclassified — open-source compilation; not an '
        "official U.S. Government product. This file contains a complete copy of the ledger and "
        "goes stale on every ledger write: rebuild it with "
        '<span class="mono">python3 -m natdef.build_app</span> after each brief.</p>'
        f'<p class="gen">natdef build_app {esc(__version__)} &middot; brief {esc(stats.brief_number)} '
        f"&middot; cutoff {esc(ledger.last_cutoff)} &middot; generated {esc(stamp)} "
        f"&middot; ledger sha256 {esc(fingerprint[:16])}…</p></footer>\n"
        # The baked ledger. Not parsed by any of the views — they were rendered server-side
        # from the same object — but present so the console is genuinely self-contained and
        # the data can be recovered from the file alone.
        f'<script type="application/json" id="natdef-ledger">{json_literal(ledger.data)}</script>\n'
        f"{scripts}\n{switcher}\n</body>\n</html>\n"
    )


def console_is_current(path: Path, ledger: Ledger) -> bool:
    """Whether the console on disk was built from this exact ledger content."""
    if not path.is_file():
        return False
    try:
        head = path.read_text(encoding="utf-8")[:4096]
    except OSError:
        return False
    match = _FINGERPRINT_RE.search(head)
    if match is None:
        return False
    return match.group(1) == ledger_fingerprint(ledger)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_app.py",
        description="Build natdef-console.html — the whole operation in one offline file.",
    )
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="output path for the console")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether the built console matches the ledger, without writing. "
        "Exits 3 if it is behind.",
    )
    args = parser.parse_args(argv)

    ledger_path = args.ledger or default_ledger_path()
    try:
        ledger = Ledger.load(ledger_path)
    except NatDefError as exc:
        print(f"build_app: {exc}", file=sys.stderr)
        return 1

    out_path = args.out or (ledger.root / CONSOLE_FILENAME)
    current = console_is_current(out_path, ledger)

    if args.check:
        if current:
            print(f"build_app: {out_path.name} is current (brief {ledger.brief_number})")
            return 0
        print(
            f"build_app: {out_path.name} is behind the ledger — run `python3 -m natdef.build_app`",
            file=sys.stderr,
        )
        return 3

    try:
        html = build_console(ledger)
    except NatDefError as exc:
        print(f"build_app: {exc}", file=sys.stderr)
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    stats = ledger.stats()
    print(
        f"build_app: wrote {out_path.name} ({len(html.encode('utf-8')) / 1024:.0f} KB) — "
        f"brief {stats.brief_number}, cutoff {ledger.last_cutoff}, "
        f"{stats.timeline_events + stats.additions} timeline events, {stats.threads} threads, "
        f"{stats.horizon} horizon items, {stats.archive_entries} archive entries"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
