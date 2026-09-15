from pathlib import Path

from examples.json_example.json_lang_parser import build_parser
from parglare_formatter.formatter import Formatter


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestJsonFormatterSuite:
    @classmethod
    def setup_class(cls):
        cls.parser = build_parser()

        rules_path = FIXTURES_DIR / "json_formatting_rules.dsl"
        dsl_source = rules_path.read_text(encoding="utf-8")

        cls.formatter = Formatter.from_dsl_source(dsl_source)

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