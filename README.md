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
- 
