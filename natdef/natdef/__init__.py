"""Nat Def — Strategic Threat & Posture briefing toolchain.

Every artifact this operation publishes is *generated* from ``intel-ledger.json``.
This package is the generator. Nothing here holds state of its own: the ledger is
the single source of truth (BRIEFING-PROTOCOL.md, Step 1), and every module in
this package either reads it, checks it, or renders it.

Module map:

==================  ====================================================
``errors``          The exception hierarchy every entry point catches.
``ledger``          The one place ``intel-ledger.json`` is parsed.
``template``        Strict token templating — fails loudly, never ships
                    an unresolved ``{{TOKEN}}`` to a reader.
``theme``           The shared design system all four pages render with.
``render``          ledger -> index / dashboard / archive / node map.
``brief``           Scaffolds ``briefs/daily-brief-YYYY-MM-DD.html``.
``build_app``       ledger -> ``natdef-console.html`` (offline console).
``server``          Serves the live ledger; never goes stale.
``validate``        The Step 6 gate. Must pass before anything is filed.
``cli``             ``python3 -m natdef <command>``.
==================  ====================================================

Standard library only, by design. This toolchain runs unattended on a schedule;
every third-party import is one more way a 15:00 run fails silently.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "2.0.0"
