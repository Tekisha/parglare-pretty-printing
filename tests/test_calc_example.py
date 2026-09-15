from examples.calc_example.calc_parser import parse_calc
from parglare_formatter.formatter import Formatter
from pathlib import Path

def _load_calc_rules():
    rules_path = Path(__file__).parents[1] / "examples" / "calc_example" / "formatting_rules.dsl"
    return rules_path.read_text(encoding="utf-8")

def test_calc_basic_program():
    source = "1 + 2 * 3\n10 - 5\n"
    ast = parse_calc(source)
    formatter = Formatter.from_dsl_source(_load_calc_rules())
    result = formatter.format(ast, width=80)
    assert result == "1 + 2 * 3\n\n10 - 5\n"

def test_calc_operator_precedence_and_associativity():
    source = "1 + 2 * 3\n(1 + 2) * 3\n"
    ast = parse_calc(source)
    fmt = Formatter.from_dsl_source(_load_calc_rules())
    result = fmt.format(ast, width=80)
    assert "1 + 2 * 3" in result
    assert "(1 + 2) * 3" in result