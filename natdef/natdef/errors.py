"""Exception hierarchy for the Nat Def toolchain.

BRIEFING-PROTOCOL.md's standing constraint — "a run that cannot reach the ledger will
fabricate one and produce a confident, sourceless brief. Visible failure beats silent
invention" — is why every failure mode here is a distinct, catchable type rather than a
bare ``Exception`` or, worse, a ``None`` return that a caller can ignore by accident.

Entry points catch :class:`NatDefError` and exit non-zero with the message. Anything that
escapes as another exception type is a bug in this package, not a data problem, and is
allowed to produce a traceback so it gets fixed rather than absorbed.
"""

from __future__ import annotations

__all__ = [
    "NatDefError",
    "LedgerError",
    "LedgerNotFoundError",
    "LedgerParseError",
    "LedgerSchemaError",
    "TemplateError",
    "UnresolvedTokenError",
    "TemplateNotFoundError",
    "RenderError",
]


class NatDefError(Exception):
    """Base class for every error this toolchain raises deliberately."""


class LedgerError(NatDefError):
    """The ledger could not be read, parsed, or trusted."""


class LedgerNotFoundError(LedgerError):
    """No ledger at the given path. Never fall back to a default or an empty ledger."""


class LedgerParseError(LedgerError):
    """The ledger is not valid JSON."""


class LedgerSchemaError(LedgerError):
    """The ledger parsed but is missing a required key or holds the wrong container type.

    ``render.py`` "refuses to run on a ledger missing required keys (including
    ``archive``)" — BRIEFING-PROTOCOL.md, Step 6. This is that refusal.
    """


class TemplateError(NatDefError):
    """A template could not be loaded or filled."""


class TemplateNotFoundError(TemplateError):
    """A template file referenced by the renderer does not exist on disk."""


class UnresolvedTokenError(TemplateError):
    """A ``{{TOKEN}}`` survived rendering.

    BRIEFING-PROTOCOL.md, Step 6: the renderer "fails loudly on an unresolved template
    token in either template rather than shipping ``{{CUTOFF}}`` or ``{{ARCHIVE_COUNT}}``
    to the reader." Shipping the literal token is the failure this exception exists to
    make impossible.
    """


class RenderError(NatDefError):
    """Rendering failed for a reason the ledger and templates alone explain."""
