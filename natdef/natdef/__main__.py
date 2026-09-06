"""Entry point for ``python3 -m natdef``.

Wraps the CLI so that piping output into a command that closes early — ``| head``, ``| less``
and quitting, a killed pager — exits quietly instead of printing a ``BrokenPipeError``
traceback. Every command here is a reporting command someone will pipe sooner or later.
"""

from __future__ import annotations

import os
import sys

from .cli import main


def _run() -> int:
    try:
        return main()
    except BrokenPipeError:
        # The reader went away. Point stdout at devnull so the interpreter's own flush at
        # shutdown does not raise a second time, then report the conventional SIGPIPE status.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 128 + 13
    except KeyboardInterrupt:
        print("\nnatdef: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(_run())
