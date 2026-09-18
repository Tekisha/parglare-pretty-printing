# Parglare Pretty Printing

Declarative pretty-printing pipeline for Parglare based  parsers.
Format arbitrary ASTs into well indented, width-aware text 
using a domain-specific formatting language and a document-algebra layout engine.

## Overview

This project turns Abstract Syntax Trees (ASTs) produced by Parglare into formatted
source code or data text. Instead of hardcoding printing logic in Python,
you describe how each AST node should be rendered in a separate formatting
DSL, which is compiled to a document algebra and then laid out optimally according to a
target line width.

The system builds on:
- **Parglare**: LR/GLR parsing library used to define grammars and construct language-specific
ASTs.
- **Document algebra**: Hughes/Wadler/Leijen-style combinators (group, next, softline, align, etc.) 
for smart line breaking and identation.

## Goals

- **Decoupling parsing and formatting**: Grammars and semantic actions build the AST,
formatting rules live in a separate .dsl file
- **Language independent formatting**: Any Parglare-based AST can be formatted by
providing a DSL rules file for its node types.
- **Demonstrate document algebra in Python**: Provide a reusable layout engine integrated
with Parglare's semantic action

## High-Level Pipeline

Conceptually, the pipeline has two tracks that meet in the formatter:
1. **Language track (syntax to AST)**
   - A Parglare grammar (*.dsl) defines the input language (eg. JSON, calculator expressions).
   - A Parglare parser and semantic actions build a langugage AST (eg. JsonObject, JsonArray, BinaryOp).

2. **Formating track (rules to DocExpr)**
    - A formatting rules file (formatting_rules.dsl) defines, per AST type, how to render that node.
    - A DSL parser builds a DSL AST of document
expressions (DocConcat, DocText, DocGroup, DocList, etc.)

These two track converge in the Doc Compiler and layout engine:
- The compiler takes a formatting rule (a DocExpr) and a concrete AST node
({"node": <Ast instance>} bindings).
- It resolves attribute paths, recursively formats child nodes and produces a Doc tree in the document algebra.
- THe layout engine renders the Doc tree to text for a given width, choosing flat vs broken layout for group and softline.

![High level pipeline](assets/pretty%20printer.png)

## Core Components

Located under `src/parglare_formatter/`:

**Document model (`document_model.py`)**
- Defines Doc constructors: `Text`, `Line`, `Concat`, `Nest`, `Group`,
`Align`, `Empty`
- Provides convenience combinators: `text()`, `line()`, `softline()`, `group()`,
`nest()`, `align()`, `concat()`, `empty()`

**Layout engine(`layout_engine.py`)**:
- Implements a Wadler/Leijen style layout algorithm:
  - Decides whether `Group(doc)` is rendered in a single flat line or broken across
multiple lines based on remaining width
  - Interprets `Softline` as either a space(flat layout) or newline(broken layout)
and applies indentation via `Nest`.

**Formatting DSL grammar and AST**
- `dsl/grammar.py`: Parglare grammar for the formatting DSL:
  - `RuleFile`, `RuleDecl` for `rule Name(params) = DocExpr;`
  - `DocExpr` with ++ concatenation and term forms:
    - `text("...")`, `line()`, `softline()`, `nest(n,doc)`, `group(doc)`,
`align(doc)`
    - `format(path)` for recursive formatting of child nodes
    - `list(path, body, separator?)`, `item` placeholder, and attribute references (`AttrPath`)
- `dsl/ast.py`: Dataclasses for DSL AST:
  - Structural nodes: `DocConcat`, `DocText`, `DocLine`, `DocSoftline`, `DocNest`,
`DocGroup`, `DocAlign`, `DocFormat`, `DocList`, `DocItem`, `DocAttrRef`.
  - Transform nodes: `DocLower`, `DocUpper`, `DocJsonEscaped` (JSON style string escaping) 
  - Rule nodes: `RuleDecl`, `RuleFile`
- `dsl/parser.py`L Parglare based DSL parser:
  - Semantic actions map grammar productions to `ast` classes
  - Public entrypoint: `parse_dsl(source: str) -> RuleFile`

**DSL compiler (`/dsl/compiler.py`)**:
- Compiles DSL document expressions (`DocExpr`) into concrete Doc trees
against a bindings environment, typically `{"nodes": ..., "item": ...}`
- Handles:
  - `DocFormat(path)`: calls `format_node(target)` to format child AST nodes.
  - `DocList(path, body, separator)`: iterates over a list attribute, applies `body` with `item` binding, inserts separators.
  - `DocLower` / `DocUpper`: transforms `str(value).lower()` / `.upper()`.
  - `DocJsonEscaped`: uses JSON escaping for string values (JSON literal body
without outer quotes).
  - `DocAttrRef`: inserts primitive values via `text(str(value))`

**Formatter API (`formatter.py`)**:
- Main user-facing entrypoint:
  ```python
   from parglare_formatter.formatter import Formatter

   formatter = Formatter.from_dsl_file("formatting_rules.dsl")
   formatted = formatter.format(ast_root, width=80)
  ```
- Responsibilities:
  - Loads and stores a `RuleFile` (parsed DSL).
  - Selects a rule by Python class name: e.g. 'JsonObject' -> `rule JsonObject(node) = ...`.
  - Invokes the DSL compiler to produce a Doc tree.
  - Runs the layout engine to obtain the final string.

## Example languages

Located under `examples/`:

**JSON example (`json_example/`)
- `json_lang_grammar.dsl`: Parlgare grammar for a JSON subset (objects, arrays, strings, numbers, 
booleans, null)
- `json_lang_ast.py`: AST classes
  - `Json`, `JsonObject`, `JsonArray`, `JsonString`, `JsonNumber`, `JsonBool`,
`JsonNull`, `JsonMember`
  - `JsonString` can decode JSON string literals to Python strings.
  - `JsonNumber` may normalize numeric representations
- `json_lang_parser.py`: Constructs the Parlgare parser and AST via semantic actions.
- `formatting_rules.dsl`: formatting rules, e.g:
```text
rule JsonObject(node) =
    text("{") ++
    nest(2,
        softline() ++
        list(node.members, item, text(",") ++ softline())
    ) ++
    softline() ++
    text("}");
```
- `test_code.py`: Demo script

**Calculator example (`calc_example/`)**
- `calc_grammar.dsl`: Parglare grammar with precedence rules
- `calc_ast.py`: AST classes
  - `Calc`, `ExprLine`, `BinaryOp`, `Number`, optionally `Paren` to preserve parentheses
- `calc_parser.py`: Parglare parser building the AST
- `formatting_rules.py`: formatting rules such as:
```text
rule BinaryOp(node) =
    group(
        format(node.left) ++ text(" ") ++ node.op ++ softline() ++ format(node.right)
    );
```
- `test_code.py`: Demo script

## DSL overview
**Rule declarations**

Each rule binds a node type to a document expression:
```text
rule BinaryOp(node) =
    format(node.left) ++ text(" ") ++ node.op ++ softline() ++ format(node.right);

rule JsonArray(node) =
    group(
        text("[") ++
        nest(2,
            softline() ++
            list(node.values, item, text(",") ++ softline())
        ) ++
        softline() ++
        text("]")
    );
```
Formatter matches rules by `type(node).__name__`

**Core combinators**:
 - `text(str)`: literal text
 - `line()`: hard line break
 - `softline()`: space if the group fits on one line, newline otherwise
 - `concat`/`++`: concatenation
 - `nest(indent, doc)`: indent nested content by indent spaces
 - `group(doc)`: try flat layout first, fall back to broken layout if width exceeded
 - `align(doc)`: align continuation lines with the first line
 - `format(path)`: recursively format `node` or child attributes
 - `list(path, item, separator)`: Iterator over a list attribute, formatting each `item` with optional separator
 - `lower(value)`, `upper(value)`, `escaped(value)`: string transformations

**Tests and how to run**
From the project root:
```bash
# Install in editable mode
python -m pip install -e .

# Run all tests
pytest

# Run JSON example
python examples/json_example/test_code.py

# Run calc example
python examples/calc_example/test_code.py
```

The tests cover:
- Document model constructors and basic combinators
- Layout behavior for `group`, `nest`, `softline`.
- DSL parsing and compilation
- Formatter behavior and integration with JSON and calc example language

**Limitations and future work**

Current limitations:
- Comments and original formatting are not preserved (one-way AST to text transformation)
- Formatting is driven by a single rule per node type (selected by class name)
- No format-preserving or incremental editing yet

Planned or possible extensions:
- Comment preservation and round-trip formatting
- Format-preserving transformations
- Rule inheritance / overrides and configuration profiles
- LSP integration for on the fly formatting from the same grammar and DSL