"""``render.py`` — ledger to dashboard, archive, node map and command centre.

This is the script BRIEFING-PROTOCOL.md Step 6 has always specified and that no copy of
ever survived into any session of this operation. The migration of 6 September 2026
deliberately did not guess at it from the single rendered sample it had, and said so
plainly rather than shipping a fabricated "recovered original"
(``docs/MIGRATION-NOTES.md``). This is a fresh implementation written against the
protocol's own description of what the script must do, not a reconstruction claiming to be
the lost one.

The contract, verbatim from Step 6:

* ledger -> ``strategic-threat-briefing.html`` + ``brief-archive.html`` + ``node-map.html``
  + ``index.html``
* "refuses to run on a ledger missing required keys (including ``archive``)"
* "fails loudly on an unresolved template token in either template rather than shipping
  ``{{CUTOFF}}`` or ``{{ARCHIVE_COUNT}}`` to the reader"

The first is :meth:`natdef.ledger.Ledger.load`'s schema gate; the second is
:mod:`natdef.template`'s. Neither is optional and neither can be turned off from here.

Every page carries a ``natdef:counts`` meta tag holding the counts it was built from.
:mod:`natdef.validate` diffs that against the ledger to implement the four freshness checks
Step 6 requires — event counts, archive-entry counts, node/edge counts, and index.html's
displayed brief number. Publishing the numbers the page was built from, rather than making
the validator scrape rendered markup for them, is what lets those checks be exact instead
of approximate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from . import __version__, pages
from .components import PAGES
from .errors import NatDefError
from .ledger import Ledger, default_ledger_path
from .template import attr, render_file
from .theme import CSS

__all__ = ["RenderedPage", "render_all", "main", "TEMPLATE_DIR", "PAGE_BUILDERS"]

#: Where ``page.html.tmpl`` lives, relative to the repository root this package sits in.
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

#: filename -> (builder, page description). Order matters only for console output.
PAGE_BUILDERS: dict[str, tuple[Callable[[Ledger], tuple[str, str, dict[str, Any]]], str]] = {
    "index.html": (
        pages.build_index,
        "Command centre — today's bottom line, the movement strip, and the way into everything else.",
    ),
    "strategic-threat-briefing.html": (
        pages.build_dashboard,
        "The standing picture — map, chronology, actor and theatre briefings, primary documents.",
    ),
    "node-map.html": (
        pages.build_node_map,
        "Every tracked actor as a graph, each with a computed history / recent / horizon deep dive.",
    ),
    "brief-archive.html": (
        pages.build_archive,
        "Every brief, browsable by date, with a catch-up digest across any window.",
    ),
}


@dataclass(frozen=True)
class RenderedPage:
    """One page that was written, and the counts it was written from."""

    filename: str
    path: Path
    html: str
    counts: dict[str, Any]
    changed: bool

    @property
    def size(self) -> int:
        return len(self.html.encode("utf-8"))


def _generator_stamp() -> str:
    return f"natdef render {__version__}"


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def render_page(
    ledger: Ledger,
    filename: str,
    *,
    template_dir: Path = TEMPLATE_DIR,
    generated_at: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Build one page's complete HTML. Raises rather than returning partial output."""
    if filename not in PAGE_BUILDERS:
        raise NatDefError(
            f"unknown page {filename!r}; known pages: {', '.join(sorted(PAGE_BUILDERS))}"
        )
    builder, description = PAGE_BUILDERS[filename]
    # Builders return body and scripts separately rather than one concatenated string: the
    # dashboard interpolates `briefings[].html` straight from the ledger, so searching the
    # body for a `<script>` boundary would be a boundary the ledger's own content could move.
    body_html, scripts, counts = builder(ledger)

    label = dict(PAGES).get(filename, filename)
    tokens = {
        "PAGE_TITLE": f"{label} — Strategic Threat & Posture",
        "PAGE_DESCRIPTION": description,
        "GENERATOR": _generator_stamp(),
        "BRIEF_NUMBER": str(ledger.brief_number),
        "CUTOFF": ledger.last_cutoff,
        "GENERATED_AT": generated_at or _now_stamp(),
        # Must be attribute-escaped, not content-escaped: this JSON is full of double
        # quotes and would otherwise terminate the meta tag's attribute early.
        "COUNTS_JSON": attr(json.dumps(counts, sort_keys=True, separators=(",", ":"))),
        "CSS": CSS,
        "NAV": _nav_for(filename),
        "BODY": body_html,
        "SCRIPTS": scripts,
    }
    html = render_file(template_dir / "page.html.tmpl", tokens)
    return html, counts


def _nav_for(filename: str) -> str:
    from .components import nav  # local import keeps the module import graph acyclic

    return nav(filename)


def render_all(
    ledger: Ledger,
    *,
    out_dir: Path | None = None,
    template_dir: Path = TEMPLATE_DIR,
    dry_run: bool = False,
    generated_at: str | None = None,
) -> list[RenderedPage]:
    """Render all four pages.

    Every page is built completely *before* any file is written, so a failure partway
    through leaves the previous render intact rather than a half-updated set of pages that
    disagree with each other about the brief number.

    :param dry_run: build and check everything, write nothing. Used by ``--check``.
    """
    target = out_dir or ledger.root
    stamp = generated_at or _now_stamp()

    built: list[tuple[str, str, dict[str, Any]]] = []
    for filename in PAGE_BUILDERS:
        html, counts = render_page(
            ledger, filename, template_dir=template_dir, generated_at=stamp
        )
        built.append((filename, html, counts))

    results: list[RenderedPage] = []
    for filename, html, counts in built:
        path = target / filename
        previous = path.read_text(encoding="utf-8") if path.is_file() else None
        # The generated-at stamp changes on every run, so comparing whole files would
        # report every page as changed every time. Compare with the stamp neutralised.
        changed = previous is None or _without_stamp(previous) != _without_stamp(html)
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
        results.append(
            RenderedPage(filename=filename, path=path, html=html, counts=counts, changed=changed)
        )
    return results


#: The page's own declaration of when it was generated. Used to neutralise that one value
#: before comparing two renders — see :func:`_without_stamp`.
_GENERATED_META_RE = re.compile(r'<meta\s+name="natdef:generated"\s+content="([^"]*)"')


def _without_stamp(html: str) -> str:
    """Neutralise the generated-at timestamp so two renders of one ledger compare equal.

    The stamp appears twice — in the ``natdef:generated`` meta tag and in the footer's
    human-readable line — so masking only the meta tag reports every page as changed on
    every run, which makes ``--check`` useless. Rather than pattern-match timestamps
    generally (which would also mask a genuine change to ``last_cutoff``, since cutoffs share
    the format), this reads the page's own declared stamp and replaces exactly that string.
    """
    match = _GENERATED_META_RE.search(html)
    if match is None or not match.group(1):
        return html
    return html.replace(match.group(1), "\x00STAMP\x00")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="render.py",
        description="Generate index.html, the dashboard, the node map and the brief archive "
        "from intel-ledger.json.",
    )
    parser.add_argument(
        "--ledger", type=Path, default=None, help="path to intel-ledger.json (default: auto-detect)"
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="output directory (default: beside the ledger)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="build everything and report whether the files on disk are current, without "
        "writing. Exits 3 if any page is stale.",
    )
    parser.add_argument(
        "--page",
        action="append",
        choices=sorted(PAGE_BUILDERS),
        help="render only this page (repeatable). Default: all four.",
    )
    args = parser.parse_args(argv)

    ledger_path = args.ledger or default_ledger_path()
    try:
        ledger = Ledger.load(ledger_path)
    except NatDefError as exc:
        print(f"render: {exc}", file=sys.stderr)
        return 1

    selected = args.page or list(PAGE_BUILDERS)
    try:
        if set(selected) == set(PAGE_BUILDERS):
            results = render_all(ledger, out_dir=args.out, dry_run=args.check)
        else:
            results = []
            stamp = _now_stamp()
            target = args.out or ledger.root
            for filename in selected:
                html, counts = render_page(ledger, filename, generated_at=stamp)
                path = target / filename
                previous = path.read_text(encoding="utf-8") if path.is_file() else None
                changed = previous is None or _without_stamp(previous) != _without_stamp(html)
                if not args.check:
                    path.write_text(html, encoding="utf-8")
                results.append(RenderedPage(filename, path, html, counts, changed))
    except NatDefError as exc:
        print(f"render: {exc}", file=sys.stderr)
        return 1

    stale = [r for r in results if r.changed]
    for result in results:
        if args.check:
            verb = "stale" if result.changed else "current"
        else:
            verb = "wrote" if result.changed else "unchanged"
        print(f"render: {verb:10} {result.filename:34} {result.size / 1024:7.1f} KB")

    print(
        f"render: brief {ledger.brief_number}, cutoff {ledger.last_cutoff}, "
        f"{len(results)} page(s)"
    )

    if args.check and stale:
        print(
            f"render: {len(stale)} page(s) behind the ledger — run render.py",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
