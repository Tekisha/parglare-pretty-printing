"""
test_code.py

Entry point that combines:
  - json_lang_grammar.dsl  (parglare grammar for JSON, as a text file)
  - json_lang_ast.py       (AST classes)
  - json_lang_parser.py    (actions + build_parser())
  - formatting_rules.dsl   (DSL rules for pretty-printing)
  - formatter.py           (Formatter from the parglare_formatter package)

Run:
    python -m src.parglare_formatter.examples.json_example.test_code
or, if the file is in the same directory:
    python test_code.py
"""

from pathlib import Path

from json_lang_parser import build_parser
from parglare_formatter.formatter import Formatter


def main():
    parser = build_parser()
    ast = parser.parse('{"x": true, "y": [2, 3]}')
    print(f"AST: {ast}")

    rules_path = Path(__file__).parent / "formatting_rules.dsl"
    dsl_rules = rules_path.read_text(encoding="utf-8")

    formatter = Formatter.from_dsl_source(dsl_rules)
    print(formatter.format(ast, width=80))


if __name__ == "__main__":
    main()