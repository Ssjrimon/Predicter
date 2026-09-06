"""A deliberately small, deliberately strict token templating engine.

BRIEFING-PROTOCOL.md, Step 6 states the renderer "fails loudly on an unresolved template
token in either template rather than shipping ``{{CUTOFF}}`` or ``{{ARCHIVE_COUNT}}`` to
the reader." That single sentence is the entire specification for this module, and it is
the reason this package does not use Jinja2 or any other general-purpose engine: the
default behaviour of most of them is to render an undefined name as empty string, which is
exactly the silent failure the protocol forbids. Here, an unresolved token is an exception.

The engine does one thing: replace ``{{TOKEN}}`` with a string. There are no loops, no
conditionals, and no expression evaluation in templates — all structure is built in Python,
where it can be typed and tested, and templates hold only the page chrome. That keeps the
templates readable as HTML and keeps logic out of files nothing can lint.

Escaping is the caller's job and is explicit: :func:`esc`, :func:`attr` and
:func:`json_literal` are provided, and a token value is inserted verbatim. This is a
conscious trade — auto-escaping would corrupt the pre-built HTML fragments that make up
most of a page — so treat every ``esc()``-free interpolation of ledger text as a bug.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Mapping

from .errors import TemplateNotFoundError, UnresolvedTokenError

__all__ = [
    "TOKEN_RE",
    "esc",
    "attr",
    "json_literal",
    "render",
    "render_file",
    "load_template",
    "slug",
]

#: A template token. Upper snake case only, so that a stray ``{{`` in prose or in a
#: JavaScript object literal inside a template is not mistaken for one.
TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

#: Sequences that must never survive into a ``<script>`` block. ``</script`` would close the
#: element early; ``<!--`` opens an HTML comment that swallows the rest of the script.
_SCRIPT_BREAKERS = {
    "</": "<\\/",
    "<!--": "\\u003c!--",
    " ": "\\u2028",  # LINE SEPARATOR is a literal newline in JS string context
    " ": "\\u2029",
}


def _normalise(value: Any) -> str:
    """Bring a ledger value to plain text before it is escaped.

    Parts of the ledger were authored by hand straight into HTML and carry entities in
    fields that are otherwise plain text: ``map_nodes[].label`` holds
    ``"ISRAEL &amp; GULF PARTNERS"``, ``categories[].label`` holds
    ``"Homeland &amp; Hemisphere"``, and several ``timeline[].t`` titles do the same. Escaping
    those a second time renders a literal ``&amp;`` to the reader — a defect visible in the
    last dashboard this operation produced, which shows ``Homeland &amp;amp; Western
    Hemisphere`` in its briefings accordion.

    Unescaping first makes escaping idempotent, so a field renders identically whether or
    not whoever wrote it pre-escaped it. The trade is that a ledger value genuinely meaning
    the seven literal characters ``&amp;`` would come out as ``&`` — which does not occur in
    this data, and is a far smaller failure than the one it prevents.
    """
    if value is None:
        return ""
    return html.unescape(str(value))


def esc(value: Any) -> str:
    """HTML-escape a value for insertion into element content.

    ``None`` becomes an empty string rather than the text "None" — a missing optional field
    should render as nothing, not as a Python repr leaking onto the page.
    """
    if value is None:
        return ""
    return html.escape(_normalise(value), quote=False)


def attr(value: Any) -> str:
    """HTML-escape a value for insertion inside a double-quoted attribute."""
    if value is None:
        return ""
    return html.escape(_normalise(value), quote=True)


def json_literal(value: Any) -> str:
    """Serialise ``value`` for embedding directly inside a ``<script>`` element.

    ``json.dumps`` alone is not safe here: a string containing ``</script>`` anywhere in the
    ledger would terminate the script element and dump the rest of the payload into the
    document as markup. The ledger holds prose written by and about hostile actors and
    quotes primary documents verbatim, so this is a realistic input, not a theoretical one.
    """
    text = json.dumps(value, ensure_ascii=False, indent=None, separators=(",", ":"))
    for needle, replacement in _SCRIPT_BREAKERS.items():
        text = text.replace(needle, replacement)
    return text


def slug(value: str) -> str:
    """A conservative id/anchor-safe slug. Empty input yields ``item``, never ``""``."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return cleaned or "item"


def load_template(path: Path) -> str:
    """Read a template file, failing with a clear message rather than an ``OSError``."""
    if not path.is_file():
        raise TemplateNotFoundError(f"template not found: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem-level failure
        raise TemplateNotFoundError(f"template at {path} could not be read: {exc}") from exc


def render(
    template: str,
    tokens: Mapping[str, Any],
    *,
    name: str = "<string>",
    allow_unused: bool = False,
) -> str:
    """Fill ``template`` from ``tokens``.

    :param allow_unused: by default, supplying a token the template does not use is an
        error too. That catches the other half of the same mistake an unresolved token
        catches — a token renamed in the template but not in the renderer, or vice versa —
        at build time instead of leaving a silently blank region on the page.
    :raises UnresolvedTokenError: if the template references a token that was not supplied,
        or (unless ``allow_unused``) if a supplied token is never referenced.
    """
    used: set[str] = set()
    missing: list[str] = []

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in tokens:
            missing.append(key)
            return match.group(0)
        used.add(key)
        value = tokens[key]
        return "" if value is None else str(value)

    output = TOKEN_RE.sub(substitute, template)

    if missing:
        unique = sorted(set(missing))
        raise UnresolvedTokenError(
            f"{name}: {len(unique)} unresolved template token(s): "
            + ", ".join(f"{{{{{k}}}}}" for k in unique)
            + ". Refusing to render — an unresolved token would ship to the reader."
        )

    if not allow_unused:
        unused = sorted(set(tokens) - used)
        if unused:
            raise UnresolvedTokenError(
                f"{name}: {len(unused)} token(s) supplied but never used by the template: "
                + ", ".join(unused)
                + ". This usually means a token was renamed on one side only."
            )

    # A second pass catches a token that was *introduced by a substituted value* — a
    # fragment built elsewhere that itself still carries an unfilled placeholder.
    leftover = sorted({m.group(1) for m in TOKEN_RE.finditer(output)})
    if leftover:
        raise UnresolvedTokenError(
            f"{name}: token(s) survived rendering inside substituted content: "
            + ", ".join(f"{{{{{k}}}}}" for k in leftover)
        )
    return output


def render_file(
    path: Path,
    tokens: Mapping[str, Any],
    *,
    allow_unused: bool = False,
) -> str:
    """Load a template from disk and render it. Errors name the file."""
    return render(load_template(path), tokens, name=str(path), allow_unused=allow_unused)
