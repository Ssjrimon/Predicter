"""``server.py`` — serve the pages from the live ledger instead of baking a static copy.

BRIEFING-PROTOCOL.md, Step 6: "server mode (``server.py``) reads the live ledger and never
goes stale at all."

Every request re-reads ``intel-ledger.json`` from disk and re-renders the page being asked
for. That is deliberately wasteful — rendering the dashboard costs a fraction of a second
and nobody is serving this at scale — and it buys the one property that matters while
someone is editing the ledger: what the browser shows is what the file says, right now,
with no build step to forget.

This is a development and reading tool. It binds to localhost by default, serves only the
four generated pages plus the briefs directory, and has no write path of any kind. Do not
put it on a network interface: ``http.server`` is not a hardened server and this one has had
no security review beyond the path handling in :meth:`Handler.resolve`.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime, timezone
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlparse

from .errors import NatDefError
from .ledger import Ledger, default_ledger_path
from .render import PAGE_BUILDERS, render_page
from .template import esc

__all__ = ["Handler", "serve", "main"]

#: Static files the server will hand over as-is, by extension.
_STATIC_TYPES: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}

#: Directories under the repository root the server will serve static files from. Anything
#: outside these is refused even if the path resolves inside the root.
_STATIC_DIRS: tuple[str, ...] = ("briefs", "sources", "docs")


class Handler(BaseHTTPRequestHandler):
    """Renders a generated page per request, or serves a file from an allow-listed directory."""

    server_version = "natdef-server"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, ledger_path: Path, **kwargs) -> None:
        self.ledger_path = ledger_path
        super().__init__(*args, **kwargs)

    # -- helpers -----------------------------------------------------------------------

    @property
    def root(self) -> Path:
        return self.ledger_path.parent

    def resolve(self, url_path: str) -> Path | None:
        """Map a URL path to a real file inside an allow-listed directory, or ``None``.

        Rejects anything that escapes the repository root after resolution, which covers
        ``..`` traversal, absolute paths and symlinks pointing outward in one check rather
        than three string tests that each need to be right.
        """
        relative = unquote(url_path).lstrip("/")
        if not relative:
            return None
        candidate = (self.root / relative).resolve()
        try:
            inside = candidate.relative_to(self.root.resolve())
        except ValueError:
            return None
        if not inside.parts or inside.parts[0] not in _STATIC_DIRS:
            return None
        return candidate if candidate.is_file() else None

    def send_payload(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_error_page(self, status: int, title: str, detail: str) -> None:
        body = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{esc(title)}</title>"
            "<style>body{background:#0A0D11;color:#E8EDF2;font:15px/1.6 system-ui;padding:48px}"
            "h1{font-size:22px}pre{color:#93A1B0;white-space:pre-wrap;font-size:13px}"
            "a{color:#C6A15B}</style></head><body>"
            f"<h1>{esc(title)}</h1><pre>{esc(detail)}</pre>"
            "<p><a href='/'>Back to the command centre</a></p></body></html>"
        ).encode("utf-8")
        self.send_payload(body, "text/html; charset=utf-8", status)

    # -- request handling ---------------------------------------------------------------

    def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's naming
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", ""):
            path = "/index.html"
        name = path.lstrip("/")

        if name in PAGE_BUILDERS:
            self.serve_rendered(name)
            return

        target = self.resolve(path)
        if target is not None:
            self.serve_static(target)
            return

        self.send_error_page(
            HTTPStatus.NOT_FOUND,
            "404 — not here",
            f"{path} is neither a generated page nor a file under "
            f"{', '.join(_STATIC_DIRS)}/.\n\nGenerated pages: "
            + ", ".join(sorted(PAGE_BUILDERS)),
        )

    def serve_rendered(self, name: str) -> None:
        """Re-read the ledger and re-render. A ledger error becomes a visible error page.

        A broken ledger must never render as a working-looking page — the standing
        constraint is that visible failure beats silent invention — so the traceback goes to
        the browser and to stderr rather than being swallowed into a blank section.
        """
        try:
            ledger = Ledger.load(self.ledger_path)
            html, _counts = render_page(
                ledger,
                name,
                generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            )
        except NatDefError as exc:
            self.send_error_page(
                HTTPStatus.INTERNAL_SERVER_ERROR, "The ledger would not render", str(exc)
            )
            return
        except Exception:  # noqa: BLE001 - a renderer bug must be seen, not hidden
            detail = traceback.format_exc()
            print(detail, file=sys.stderr)
            self.send_error_page(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Renderer error", detail
            )
            return
        self.send_payload(html.encode("utf-8"), "text/html; charset=utf-8")

    def serve_static(self, target: Path) -> None:
        content_type = _STATIC_TYPES.get(target.suffix.lower(), "application/octet-stream")
        try:
            body = target.read_bytes()
        except OSError as exc:
            self.send_error_page(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Could not read file", str(exc)
            )
            return
        self.send_payload(body, content_type)

    def log_message(self, fmt: str, *args) -> None:
        print(f"server: {fmt % args}", file=sys.stderr)


def serve(ledger_path: Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the server until interrupted."""
    if not ledger_path.is_file():
        raise NatDefError(f"ledger not found: {ledger_path}")
    handler = partial(Handler, ledger_path=ledger_path)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(
        f"server: serving the live ledger at http://{host}:{port}/ "
        f"(ledger: {ledger_path})\nserver: every request re-reads the ledger — nothing goes "
        "stale. Ctrl-C to stop.",
        file=sys.stderr,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nserver: stopped", file=sys.stderr)
    finally:
        httpd.server_close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="server.py",
        description="Serve the generated pages from the live ledger. Localhost only.",
    )
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        serve(args.ledger or default_ledger_path(), host=args.host, port=args.port)
    except NatDefError as exc:
        print(f"server: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
