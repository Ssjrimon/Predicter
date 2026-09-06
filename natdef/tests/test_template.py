"""The strict template engine — the module whose entire job is failing loudly."""

from __future__ import annotations

import json
import unittest

from natdef.errors import TemplateNotFoundError, UnresolvedTokenError
from natdef.template import attr, esc, json_literal, render, render_file, slug


class TestRendering(unittest.TestCase):
    def test_substitutes_tokens(self) -> None:
        self.assertEqual(render("a {{X}} c", {"X": "b"}), "a b c")

    def test_unresolved_token_raises_rather_than_shipping(self) -> None:
        """BRIEFING-PROTOCOL.md Step 6: never ship {{CUTOFF}} to the reader."""
        with self.assertRaises(UnresolvedTokenError) as ctx:
            render("cutoff: {{CUTOFF}}", {})
        self.assertIn("CUTOFF", str(ctx.exception))

    def test_unused_token_raises_too(self) -> None:
        """Catches the other half of a rename: supplied here, renamed in the template."""
        with self.assertRaises(UnresolvedTokenError) as ctx:
            render("nothing here", {"CUTOFF": "x"})
        self.assertIn("CUTOFF", str(ctx.exception))

    def test_unused_can_be_allowed_explicitly(self) -> None:
        self.assertEqual(render("plain", {"X": "y"}, allow_unused=True), "plain")

    def test_a_token_introduced_by_a_value_is_caught(self) -> None:
        """A fragment built elsewhere must not smuggle an unfilled placeholder through."""
        with self.assertRaises(UnresolvedTokenError):
            render("{{BODY}}", {"BODY": "leftover {{INNER}}"})

    def test_lowercase_braces_are_not_tokens(self) -> None:
        """JS object literals and CSS in templates must survive untouched."""
        source = "function(){ return {{a:1}}; }"
        self.assertEqual(render(source, {}, allow_unused=True), source)

    def test_missing_template_file_names_the_path(self) -> None:
        with self.assertRaises(TemplateNotFoundError):
            render_file(__import__("pathlib").Path("/nonexistent/x.tmpl"), {})


class TestEscaping(unittest.TestCase):
    def test_escapes_markup(self) -> None:
        self.assertEqual(esc("<script>"), "&lt;script&gt;")

    def test_attr_escapes_quotes_and_esc_does_not(self) -> None:
        self.assertEqual(attr('a "b"'), "a &quot;b&quot;")
        self.assertEqual(esc('a "b"'), 'a "b"')

    def test_none_renders_as_nothing_not_as_none(self) -> None:
        self.assertEqual(esc(None), "")
        self.assertEqual(attr(None), "")

    def test_escaping_is_idempotent_over_pre_escaped_ledger_text(self) -> None:
        """The bug visible in the last frozen dashboard: 'Homeland &amp;amp; Hemisphere'."""
        self.assertEqual(esc("Homeland &amp; Hemisphere"), "Homeland &amp; Hemisphere")
        self.assertEqual(esc(esc("Homeland & Hemisphere")), "Homeland &amp; Hemisphere")


class TestJsonLiteral(unittest.TestCase):
    def test_round_trips_ordinary_data(self) -> None:
        payload = {"a": [1, 2], "b": "text"}
        self.assertEqual(json.loads(json_literal(payload)), payload)

    def test_cannot_close_the_script_element(self) -> None:
        """The ledger quotes hostile primary sources verbatim; this is a real input."""
        out = json_literal({"x": "</script><img onerror=alert(1)>"})
        self.assertNotIn("</script", out)

    def test_neutralises_html_comment_opener(self) -> None:
        self.assertNotIn("<!--", json_literal({"x": "<!-- hi"}))

    def test_escapes_js_line_terminators(self) -> None:
        out = json_literal({"x": "a b c"})
        self.assertNotIn(" ", out)
        self.assertNotIn(" ", out)
        self.assertIn("\\u2028", out)


class TestSlug(unittest.TestCase):
    def test_makes_anchor_safe_ids(self) -> None:
        self.assertEqual(slug("Iran / Hormuz"), "iran-hormuz")

    def test_never_returns_empty(self) -> None:
        self.assertEqual(slug("!!!"), "item")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
