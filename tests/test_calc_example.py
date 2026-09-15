from pathlib import Path

from examples.calc_example.calc_parser import parse_calc
from parglare_formatter.formatter import Formatter


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCalcFormatterSuite:
    @classmethod
    def setup_class(cls):
        rules_path = FIXTURES_DIR / "calc_formatting_rules.dsl"
        dsl_source = rules_path.read_text(encoding="utf-8")

        cls.formatter = Formatter.from_dsl_source(dsl_source)

    def test_basic_program(self):
        source = "1 + 2 * 3\n10 - 5\n"
        ast = parse_calc(source)
        result = self.formatter.format(ast, width=80)
        assert result == "1 + 2 * 3\n\n10 - 5\n"

    def test_operator_precedence_and_parens(self):
        source = "1 + 2 * 3\n(1 + 2) * 3\n"
        ast = parse_calc(source)
        result = self.formatter.format(ast, width=80)

        assert "1 + 2 * 3" in result
        assert "(1 + 2) * 3" in result

    def test_layout_under_small_width(self):
        source = "1 + 2 * 3\n10 - 5\n"
        ast = parse_calc(source)

        wide = self.formatter.format(ast, width=80)
        narrow = self.formatter.format(ast, width=5)

        assert "1 + 2 * 3" in wide
        assert "10 - 5" in wide

        assert "1 +\n2 * 3" in narrow
        assert "10 -\n5" in narrow