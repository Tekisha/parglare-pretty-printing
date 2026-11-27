import re
import sys
from pathlib import Path

from parglare_formatter.dsl.parser import parse_dsl

path = Path(sys.argv[1])
original = path.read_text(encoding="utf-8")

pattern = re.compile(r'text\(\s*("(?:\\.|[^"\\])*")\s*\)')
converted = pattern.sub(r"\1", original)

assert parse_dsl(original) == parse_dsl(converted), "AST changed, aborting"

path.write_text(converted, encoding="utf-8")
print(f"Rewrote {path}")