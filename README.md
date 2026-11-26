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
1. **Language track (source to AST)**
   - A parser (a Parglare grammar for JSON, `pycparser` for C) produces the
     AST of the input language.

2. **Formatting track (rules to DocExpr)**
   - A rules file (`formatting_rules.dsl`) defines, per AST node class (and
     optionally per context), how to render that node.
   - The DSL parser builds a DSL AST of document expressions (`DocConcat`,
     `DocText`, `DocGroup`, `DocList`, `DocOptional`, `DocWhen`, etc.).

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

**Layout engine (`layout_engine.py`)**
- Wadler/Leijen-style renderer.
- A `Group` is rendered flat if it fits in the remaining width, otherwise
  broken.
- A soft line becomes a space in a flat group and a newline in a broken
  group. Outside any group it is rendered as a newline.
- A hard line (`line()`) is always a newline, even inside a flat group.
- `Nest` adds indentation after line breaks, and `Align` aligns
  continuation lines with the current column.

**Formatting DSL grammar and AST**
- `dsl/grammar.py`: Parglare grammar for the formatting DSL:
  - `RuleFile`, `RuleDecl` for `rule Name = DocExpr;`
  - `DocExpr` with ++ concatenation and term forms:
    - `text("...")`, `line()`, `softline()`, `nest(n,doc)`, `group(doc)`,
`align(doc)`
    - `format(path)` for recursive formatting of child nodes
    - `list(path, body, separator?)`, `item` placeholder, and attribute references (`AttrPath`)
- `dsl/ast.py`: Dataclasses for DSL AST:
  - Structural nodes: `DocConcat`, `DocText`, `DocLine`, `DocSoftline`, `DocNest`,
`DocGroup`, `DocAlign`, `DocFormat`, `DocList`, `DocItem`, `DocAttrRef`, `DocOptional`, `DocWhen`.
  - Transform nodes: `DocLower`, `DocUpper`, `DocJsonEscaped` (JSON style string escaping) 
  - Rule nodes: `RuleDecl`, `RuleFile`
- `dsl/parser.py`L Parglare based DSL parser:
  - Semantic actions map grammar productions to `ast` classes
  - Public entrypoint: `parse_dsl(source: str) -> RuleFile`
- `compiler.py`: `compile_doc_expr(expr, bindings, format_node,
  list_separators)` evaluates a `DocExpr` over concrete AST nodes and
  returns a `Doc`. Evaluation errors raise `CompileError`.

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

**Grammar introspection (`grammar_introspection.py`)**
- `extract_list_separators(grammar)` reads separator literals from a
  Parglare grammar, so that `list(...)` can use the language's own
  separator (for example `,`) without repeating it in the rules.

**Formatter API (`formatter.py`)**:
- Main user-facing entrypoint:
  ```python
   from parglare_formatter.formatter import Formatter

   formatter = Formatter.from_dsl_file("formatting_rules.dsl")
   formatted = formatter.format(ast_root, width=80)
  ```
- Responsibilities:
  - Loads a `RuleFile` and, optionally, separator information from a
    Parglare grammar (`Formatter.from_dsl_file(path, grammar=grammar)`).
  - Selects a rule by the node's Python class name.
  - Compiles the rule to a `Doc` and renders it with the layout engine.
  - Errors are reported as `FormatterError`.
  - A one-call helper is also available:
    `format_ast(node, dsl_source, width=80)`.

## DSL Reference

A rules file is a sequence of rules:

```text
rule ClassName =
    ;
```

The node being formatted is bound implicitly as `node`. Rules have no
parameter list.


### Document expressions

| Construct | Meaning |
|---|---|
| `text("...")` | Literal text |
| `a ++ b` | Concatenation (left-associative) |
| `line()` | Hard line break |
| `softline()` | Space in a flat group, newline in a broken group (newline outside groups) |
| `nest(n, doc)` | Indent line breaks inside `doc` by `n` |
| `group(doc)` | Try a flat layout, otherwise break |
| `align(doc)` | Align continuation lines with the current column |
| `format(path)` | Format the node at `path` with its default rule |
| `format(path, context)` | Format with the rule `context_ClassName` if it exists, otherwise the default rule |
| `list(path, body)` | Format each element of a list using `body` |
| `list(path, body, sep)` | Same, with `sep` between elements |
| `item` | Current element inside `list(...)`, formatted recursively |
| `optional(path, body)` | `body` unless the value at `path` is `None` (otherwise nothing) |
| `when(path, "lit", a)` | `a` if the value at `path` is the string `lit`, otherwise nothing |
| `when(path, "lit", a, b)` | `a` if the value equals `lit`, otherwise `b` |
| `lower(path)`, `upper(path)` | Lower-/upper-cased text of an attribute |
| `escaped(path)` | JSON-style escaping of a string attribute (without outer quotes) |
| `node.attr` | Attribute value inserted as text |


### Semantics worth knowing

- **Rule selection**: by `type(node).__name__`. Primitive values (`str`,
  `int`, `float`, `bool`) without a rule are emitted as text. `None` is not
  formatted silently, so use `optional(...)` for optional fields.
- **Contexts**: `format(child, ctx)` looks up the rule `ctx_ClassName` first
  and falls back to `ClassName`. A context applies to that single call and
  is not inherited by the child's own `format(...)` calls. Context names
  are chosen by the rule author and have no built-in meaning. The C example
  uses `statement` (add `;`) and `bare` (no outer parentheses).
- **List separators**: an explicit separator is used if given. Otherwise,
  if the grammar defines one for that list, the separator is that literal
  followed by a soft line. Otherwise elements are separated by a hard line.
  An empty list produces nothing.
- **`optional`** only treats `None` as absent. Values such as `0`, `False`,
  `""` and `[]` are formatted normally. The body of an absent value is not
  evaluated.
- **`when`** compares strings only. Non-string values never match.
  The branch that is not selected is not evaluated.
- A missing attribute is always an error (`CompileError`), including inside
  `optional` and `when`.

## Example languages

Located under `examples/`:

**C (`c_ast_example/`)**

A subset of C, parsed with [`pycparser`](https://github.com/eliben/pycparser)
and formatted by DSL rules only. The pycparser code generator is not used.

- `formatting_rules.dsl`: rules for pycparser node classes.
- `ast_utils.py`: `ast_signature(...)`, a structural AST signature that
  ignores source coordinates. It is used by the roundtrip tests.

Supported subset:

| Group | pycparser nodes |
|---|---|
| Structure | `FileAST`, `FuncDef`, `Compound` |
| Declarations | `Decl`, `TypeDecl`, `IdentifierType`, `Typename`, `FuncDecl`, `ParamList`, `DeclList` (single declaration) |
| Expressions | `ID`, `Constant`, `BinaryOp`, `UnaryOp`, `Assignment`, `FuncCall`, `ExprList` |
| Statements | `Return`, `If` / `else`, `While`, `For` |

Conventions of the C rules:

- Expression nodes (`BinaryOp`, `UnaryOp`, `Assignment`) are parenthesized
  to preserve structure. Contexts `statement_` and `bare_` produce the
  statement form (with `;`) and the unparenthesized form (for conditions
  and `for` headers).
- Initializers, parameters, `else` branches, `return` values and `for`
  header parts are optional (`optional`).
- Unary operators that are written after the operand (`x++`) are selected
  with `when` on the operator.

**JSON example (`json_example/`)**
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
rule JsonObject =
    text("{") ++
    nest(2, softline() ++ list(node.members, item)) ++
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
rule BinaryOp = 
    format(node.left) ++ 
    text(" ") ++ node.op ++ text(" ") ++ 
    format(node.right);
```
- `test_code.py`: Demo script

**Tests and how to run**
From the project root:
```bash
# Install in editable mode
python -m pip install -e .

# The C tests requires 'pycparser'
python -m pip install pycparser

# Run all tests
pytest

# Run JSON example
python examples/json_example/test_code.py

# Run calc example
python examples/calc_example/test_code.py
```

The C example requires `pycparser`:

```bash
python -m pip install pycparser
```

The tests cover:

- Document model constructors and combinators.
- Layout behavior for `group`, `nest` and `softline`.
- DSL parsing and compilation, including `optional`, `when` and contextual
  `format`.
- Formatter behavior with the JSON example.
- C roundtrip tests: each source is formatted at widths from 1 to 200,
  re-parsed, and compared structurally with the original AST. A second
  formatting pass must produce identical text (idempotence). Exact-layout
  tests check representative outputs.

Roundtrip tests show that formatting preserves the structure of the
supported subset. They do not prove correctness for all of C.

## Limitations

- One-way AST to text. Comments and original formatting are not preserved.
  `pycparser` does not keep comments or preprocessor directives.
- A node class has one default rule, plus optional contextual variants.
- Nodes without a rule raise `FormatterError`. This is not guaranteed for
  all unsupported constructs: a rule that ignores fields (for example
  qualifiers and storage classes in the C `Decl` rule) drops them silently.
- Not supported in the C example: pointers and arrays, `struct`/`union`/
  `enum`/`typedef`, `switch`, `do`/`while`, `break`/`continue`/`goto`,
  ternary and cast expressions, initializer lists, qualifiers and storage
  classes (`const`, `static`, ...), several declarations in one `for` init,
  and `sizeof(type)`.

## Possible Extensions

- Comment preservation and format-preserving transformations.
- Rule inheritance, overrides and configuration profiles.
- Minimal-parentheses printing based on operator precedence.
- LSP integration for on the fly formatting from the same grammar and DSL