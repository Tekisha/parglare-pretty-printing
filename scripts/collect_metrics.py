import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "examples" / "c_ast_example" / "formatting_rules.dsl"
PACKAGE = ROOT / "src" / "parglare_formatter"
TESTS = ROOT / "tests"
CONTEXTS = ("statement_", "bare_")


def loc(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    return sum(
        1 for line in lines
        if line.strip() and not line.strip().startswith("#")
    )


def rule_names(path: Path):
    text = path.read_text(encoding="utf-8")
    return re.findall(r"^rule\s+(\w+)\s*=", text, flags=re.M)


def collected_tests():
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    per_file = Counter()
    for line in out.splitlines():
        if "::" in line:
            per_file[line.split("::")[0]] += 1
    return per_file


def main():
    names = rule_names(RULES)
    base = [n for n in names if not n.startswith(CONTEXTS)]
    contextual = [n for n in names if n.startswith(CONTEXTS)]

    print("## C DSL rules")
    print(f"- total rules: {len(names)}")
    print(f"- base rules (one per node class): {len(base)}")
    print(f"- contextual rules (statement_/bare_): {len(contextual)}")
    print(f"- DSL lines (non-blank): {loc(RULES)}")

    print("\n## Python implementation (lines)")
    total = 0
    for p in sorted(PACKAGE.rglob("*.py")):
        n = loc(p)
        total += n
        print(f"- {p.relative_to(PACKAGE)}: {n}")
    print(f"- total: {total}")

    print("\n## Collected tests")
    per_file = collected_tests()
    for f, n in sorted(per_file.items()):
        print(f"- {f}: {n}")
    print(f"- total: {sum(per_file.values())}")


if __name__ == "__main__":
    main()