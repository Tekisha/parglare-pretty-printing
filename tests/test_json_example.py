from pathlib import Path

from examples.json_example.json_lang_parser import build_parser
from parglare_formatter.formatter import Formatter
from parglare_formatter.grammar_introspection import extract_list_separators


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestJsonFormatterSuite:
    @classmethod
    def setup_class(cls):
        cls.parser = build_parser()

        explicit = (FIXTURES_DIR / "json_formatting_rules.dsl").read_text(encoding="utf-8")
        derived = (FIXTURES_DIR / "json_formatting_rules_derived.dsl").read_text(encoding="utf-8")

        cls.formatter = Formatter.from_dsl_source(explicit)
        cls.derived_formatter = Formatter.from_dsl_source(
            derived, grammar=cls.parser.grammar
        )

    def test_pretty_print_basic(self):
        ast = self.parser.parse('{"x": true, "y": [2, 3]}')
        result = self.formatter.format(ast, width=80)
        assert '"x": true' in result
        assert '"y": [' in result

    def test_all_primitive_types(self):
        ast = self.parser.parse(
            '{"s": "x", "n": 1, "b": false, "u": null, "a": [1, 2]}'
        )
        result = self.formatter.format(ast, width=80)
        assert '"s": "x"' in result
        assert '"n": 1' in result
        assert '"b": false' in result
        assert '"u": null' in result
        assert '"a": [' in result

    def test_string_escaping(self):
        ast = self.parser.parse(
            '{"msg": "He said \\"hello\\"\\nPath: C\\\\temp"}'
        )
        result = self.formatter.format(ast, width=80)
        assert '\\\"hello\\\"' in result
        assert '\\nPath: C\\\\temp' in result

    def test_array_flat_vs_broken_layout(self):
        ast = self.parser.parse('{"a": [1, 2, 3]}')

        wide = self.formatter.format(ast, width=80)
        narrow = self.formatter.format(ast, width=5)

        assert '"a": [ 1.0, 2.0, 3.0 ]' in wide
        assert '"a": [' in narrow
        assert "1.0," in narrow
        assert "\n" in narrow

    def test_extract_json_separators(self):
        assert extract_list_separators(self.parser.grammar) == {
            ("JsonObject", "members"): ",",
            ("JsonArray", "values"): ",",
        }

    def test_derived_separator_matches_explicit(self):
        ast = self.parser.parse(
            '{"s": "x", "n": 1, "a": [1, 2, 3], "o": {"k": null}}'
        )
        for width in (5, 20, 40, 80):
            assert (
                    self.derived_formatter.format(ast, width=width)
                    == self.formatter.format(ast, width=width)
            )

    def test_explicit_separator_overrides_derived(self):
        rules = (FIXTURES_DIR / "json_formatting_rules_derived.dsl").read_text(encoding="utf-8")
        rules = rules.replace(
            "list(node.values, item)",
            'list(node.values, item, text(";") ++ line())',
        )
        formatter = Formatter.from_dsl_source(rules, grammar=self.parser.grammar)
        ast = self.parser.parse("[1, 2]")
        assert ";" in formatter.format(ast, width=80)

    def test_without_grammar_falls_back_to_line(self):
        rules = (FIXTURES_DIR / "json_formatting_rules_derived.dsl").read_text(encoding="utf-8")
        formatter = Formatter.from_dsl_source(rules)
        ast = self.parser.parse("[1, 2]")
        assert "," not in formatter.format(ast, width=80)