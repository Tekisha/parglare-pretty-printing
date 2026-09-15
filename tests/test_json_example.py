from examples.json_example.json_lang_parser import build_parser
from parglare_formatter.formatter import Formatter
from pathlib import Path

def _load_json_rules():
    rules_path = Path(__file__).parents[1] / "examples" / "json_example" / "formatting_rules.dsl"
    return rules_path.read_text(encoding="utf-8")

def test_json_pretty_print_basic():
    parser = build_parser()
    ast = parser.parse('{"x": true, "y": [2, 3]}')
    formatter = Formatter.from_dsl_source(_load_json_rules())
    result = formatter.format(ast, width=80)
    assert '"x": true' in result
    assert '"y": [' in result

def test_json_all_primitive_types():
    parser = build_parser()
    ast = parser.parse('{"s": "x", "n": 1, "b": false, "u": null, "a": [1, 2]}')
    fmt = Formatter.from_dsl_source(_load_json_rules())
    result = fmt.format(ast, width=80)
    assert '"s": "x"' in result
    assert '"n": 1' in result
    assert '"b": false' in result
    assert '"u": null' in result
    assert '"a": [' in result

def test_json_string_escaping():
    parser = build_parser()
    ast = parser.parse('{"msg": "He said \\"hello\\"\\nPath: C\\\\temp"}')
    fmt = Formatter.from_dsl_source(_load_json_rules())
    result = fmt.format(ast, width=80)
    assert '\\\"hello\\\"' in result
    assert '\\nPath: C\\\\temp' in result