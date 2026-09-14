from pathlib import Path

from calc_parser import parse_calc
from parglare_formatter.formatter import Formatter


def main():
    source = "1 + 2 * 3\n10 - 5\n"
    ast = parse_calc(source)
    print(f"AST: {ast}")

    rules_path = Path(__file__).parent / "formatting_rules.dsl"
    dsl_rules = rules_path.read_text(encoding="utf-8")

    formatter = Formatter.from_dsl_source(dsl_rules)
    print(formatter.format(ast, width=80))


if __name__ == "__main__":
    main()