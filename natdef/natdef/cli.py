"""``python3 -m natdef <command>`` — one entry point for the whole toolchain.

Each subcommand delegates to the module that owns it, so ``python3 -m natdef render`` and
``python3 -m natdef.render`` do exactly the same thing and neither is a wrapper that can
drift from the other.

``natdef status`` and ``natdef check`` exist for the two questions that get asked most:
"where does this stand?" and "is everything current and passing?". ``check`` runs the
Step 6 gate end to end — render freshness, console freshness, validator — and is the one
command to run before committing anything that touched the ledger.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__, brief, build_app, render, server, validate
from .errors import NatDefError
from .ledger import Ledger, default_ledger_path

__all__ = ["main"]


def _status(ledger_path: Path) -> int:
    try:
        ledger = Ledger.load(ledger_path, require_schema=False)
    except NatDefError as exc:
        print(f"status: {exc}", file=sys.stderr)
        return 2
    stats = ledger.stats()
    latest = ledger.latest_archive
    print(f"ledger        {ledger_path}")
    print(f"brief         {stats.brief_number}")
    print(f"cutoff        {ledger.last_cutoff}")
    print(f"updated       {ledger.last_updated}")
    print(f"revision      {ledger.revision}")
    print(
        f"contents      {stats.threads} threads, {stats.total_sources} sources "
        f"({stats.current_sources} current), {stats.timeline_events + stats.additions} events, "
        f"{stats.horizon} horizon, {stats.archive_entries} archive, "
        f"{stats.verification_checks} verification entries"
    )
    print(
        f"node map      {stats.map_nodes} nodes, {stats.node_edges} edges, "
        f"{stats.node_history_entries} archival entries"
    )
    if latest is not None:
        print(f"latest brief  {latest.date} ({latest.weekday}) — {latest.brief_filename}")
    briefs = ledger.brief_files_on_disk()
    print(f"briefs/       {len(briefs)} delivered brief file(s) on disk")
    pages = [name for name in render.PAGE_BUILDERS if (ledger.root / name).is_file()]
    print(f"rendered      {len(pages)}/{len(render.PAGE_BUILDERS)} page(s) present")
    console = ledger.root / build_app.CONSOLE_FILENAME
    if console.is_file():
        state = "current" if build_app.console_is_current(console, ledger) else "STALE"
        print(f"console       present, {state}")
    else:
        print("console       not built")
    return 0


def _check(ledger_path: Path, *, strict: bool) -> int:
    """Render freshness + console freshness + the full validator, in that order."""
    failures: list[str] = []

    print("== render --check ==")
    if render.main(["--ledger", str(ledger_path), "--check"]) != 0:
        failures.append("rendered pages are behind the ledger (run `natdef render`)")

    print("\n== build_app --check ==")
    if build_app.main(["--ledger", str(ledger_path), "--check"]) != 0:
        failures.append("natdef-console.html is behind the ledger (run `natdef build-app`)")

    print("\n== validate ==")
    argv = ["--ledger", str(ledger_path)]
    if strict:
        argv.append("--strict")
    if validate.main(argv) != 0:
        failures.append("validate.py reported failures")

    print()
    if failures:
        for failure in failures:
            print(f"check: FAIL — {failure}", file=sys.stderr)
        print(
            "check: do not deliver or commit. BRIEFING-PROTOCOL.md Step 6: fix the ledger "
            "and re-run.",
            file=sys.stderr,
        )
        return 1
    print("check: PASS — pages current, console current, validator clean.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="natdef",
        description="Nat Def — Strategic Threat & Posture briefing toolchain.",
    )
    parser.add_argument("--version", action="version", version=f"natdef {__version__}")
    parser.add_argument(
        "--ledger", type=Path, default=None, help="path to intel-ledger.json (default: auto-detect)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="where the operation stands right now")

    check = sub.add_parser(
        "check", help="the full Step 6 gate: render freshness, console freshness, validator"
    )
    check.add_argument("--strict", action="store_true")

    sub.add_parser("render", add_help=False, help="ledger -> the four generated pages")
    sub.add_parser("validate", add_help=False, help="the Step 6 validation gate")
    sub.add_parser("build-app", add_help=False, help="ledger -> natdef-console.html")
    sub.add_parser("brief", add_help=False, help="render a brief from its archive[] entry")
    sub.add_parser("serve", add_help=False, help="serve the pages from the live ledger")

    # Subcommands that delegate take their own flags verbatim, so parse only up to the
    # subcommand name and hand the rest to the module that owns it.
    known, rest = parser.parse_known_args(argv)
    ledger_path = known.ledger or default_ledger_path()
    forward = list(rest)
    if known.ledger is not None and known.command in {
        "render",
        "validate",
        "build-app",
        "brief",
        "serve",
    }:
        forward = ["--ledger", str(ledger_path), *forward]

    try:
        if known.command == "status":
            return _status(ledger_path)
        if known.command == "check":
            return _check(ledger_path, strict="--strict" in rest)
        if known.command == "render":
            return render.main(forward)
        if known.command == "validate":
            return validate.main(forward)
        if known.command == "build-app":
            return build_app.main(forward)
        if known.command == "brief":
            return brief.main(forward)
        if known.command == "serve":
            return server.main(forward)
    except NatDefError as exc:
        print(f"natdef: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unknown command {known.command!r}")
    return 2  # pragma: no cover - parser.error exits
