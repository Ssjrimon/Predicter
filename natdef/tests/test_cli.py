"""The command line itself — the layer where a flag can go missing without anything failing.

Both cases here were live defects. Neither produced an error message, a traceback the user
could act on, or a failing check: ``natdef check --strict`` ran the *loose* gate and printed
PASS, and ``natdef render --page`` wrote nothing into a directory that did not exist yet.
A toolchain whose stated purpose is that visible failure beats silent invention has to hold
that line in its own argument plumbing too, so these are asserted rather than assumed.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from natdef import cli, render
from natdef.ledger import Ledger
from tests.fixtures import write_ledger


class StrictFlagReachesTheGate(unittest.TestCase):
    """``--strict`` is declared on the ``check`` subparser, so it lands in the parsed
    namespace and never in the leftover argv. Reading it from the leftovers meant it was
    always ``False``."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.ledger_path = write_ledger(self.root, None)
        self.seen: list[bool] = []
        original = cli._check
        self.addCleanup(lambda: setattr(cli, "_check", original))
        cli._check = lambda ledger_path, *, strict: (self.seen.append(strict), 0)[1]

    def test_strict_is_forwarded(self) -> None:
        cli.main(["--ledger", str(self.ledger_path), "check", "--strict"])
        self.assertEqual(self.seen, [True])

    def test_absent_strict_stays_false(self) -> None:
        cli.main(["--ledger", str(self.ledger_path), "check"])
        self.assertEqual(self.seen, [False])


class SinglePageRenderCreatesItsOutputDirectory(unittest.TestCase):
    """``render_all`` mkdirs; the ``--page`` branch did not, and died on FileNotFoundError."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.ledger_path = write_ledger(self.root, None)

    def test_page_into_a_missing_directory(self) -> None:
        out = self.root / "does" / "not" / "exist"
        code = render.main(
            ["--ledger", str(self.ledger_path), "--page", "index.html", "--out", str(out)]
        )
        self.assertEqual(code, 0)
        self.assertTrue((out / "index.html").is_file())

    def test_check_still_writes_nothing(self) -> None:
        out = self.root / "dry"
        code = render.main(
            [
                "--ledger",
                str(self.ledger_path),
                "--page",
                "index.html",
                "--out",
                str(out),
                "--check",
            ]
        )
        # --check on an absent page reports it stale (exit 3) and must not create the
        # directory it was only ever asked to inspect.
        self.assertEqual(code, 3)
        self.assertFalse(out.exists())

    def test_all_pages_into_a_missing_directory_still_works(self) -> None:
        out = self.root / "all" / "of" / "them"
        ledger = Ledger.load(self.ledger_path)
        results = render.render_all(ledger, out_dir=out)
        self.assertEqual(len(results), len(render.PAGE_BUILDERS))
        for result in results:
            self.assertTrue(result.path.is_file())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
