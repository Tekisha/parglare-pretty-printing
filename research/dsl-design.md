# DSL Design: Declarative AST-to-Text Formatting Integrated with Parglare

This document specifies the design of a domain-specific language (DSL) for declarative AST-to-text formatting rules, integrated with the Parglare LR/GLR parser for Python.
It builds on classical document algebra (Hughes/Wadler/Leijen), recent work on expressive and optimal pretty printers (PrettyExpressive), grammar-directed and layout-declaration approaches (De Jonge, Van den Brand, AnyText, Declarative Indentation), and machine-learning formatters (CODEBUFF), while focusing the scope on a Parglare-centric, AST-based pretty-printing DSL suitable for a master's thesis.

## 1. Goals and Constraints

### 1.1 Goals

The DSL aims to:

- Provide **declarative formatting rules** that map AST node types to document-construction expressions ("node-to-doc" rules).
- Support a **document algebra** with primitives for literal text, concatenation, hard and soft line breaks, nesting/indentation, grouping, alignment, and lists with separators.
- Capture **context-sensitive formatting** decisions, such as different layouts depending on parent node type, position in a list, or current line width.
- Integrate cleanly with **Parglare's grammar and AST model**, without requiring changes to Parglare itself.
- Be **deterministic and well-defined**, with clear error handling for missing rules or invalid constructs.

### 1.2 Constraints (Master Thesis Scope)

To keep the project within a realistic master's thesis scope, the DSL design adopts the following constraints:

- Focus on an **AST-centric pretty printer** for a small expression language (mini-language inspired by Parglare examples), rather than full support for large general-purpose languages.
- Implement a **simplified layout engine** based on Wadler/Leijen-style algorithms, rather than a fully general PrettyExpressive-style cost factory and optimality proofs.
- Provide hooks for **future format-preserving and grammar-embedded extensions** (e.g., AnyText-style single source of truth, layout-preserving algorithms) but not fully realize them in the MVP.
- Leave **machine-learning integration** (e.g., CODEBUFF-style learned formatting) as future work beyond the core DSL design, acknowledging its orthogonality to Parglare integration.

## 2. Syntax Variants and Choice

Two main syntax variants were considered for specifying formatting rules:

1. A **structured JSON/YAML format**, where rules are represented as nested objects/arrays.
2. A **textual DSL with its own grammar**, parsed by Parglare.

### 2.1 JSON/YAML Variant

A JSON/YAML-style DSL could represent rules as nested data, for example:

```yaml
rules:
  BinaryExpr:
    doc:
      - node: left
      - text: " + "
      - line: soft
      - node: right

  Block:
    doc:
      - text: "{"
      - group:
          - nest: 4
            doc:
              - line: hard
              - nodes: statements
                separator:
                  line: hard
      - line: hard
      - text: "}"
```

Advantages:

- Easy to parse with off-the-shelf JSON/YAML parsers.
- Naturally structured and friendly to configuration-like usage.

Disadvantages:

- Limited **syntactic expressiveness** for more complex constructs (e.g., conditionals, inline combinators) without introducing custom conventions.
- Less convenient for specifying **document algebra expressions** in a concise, compositional style.
- Harder to connect directly to **formal grammars and parsing tools** in the Parglare ecosystem.

### 2.2 Textual DSL Variant

The textual DSL variant defines its own grammar and is parsed by Parglare, using a syntax reminiscent of functional/combinator languages:

```text
RuleFile: RuleDecl* ;

RuleDecl: "rule" Ident "(" ParamList? ")" "=" DocExpr ";" ;

ParamList: Param ("," Param)* ;
Param: Ident ;

DocExpr: DocExpr "++" DocTerm
       | DocTerm
       ;

DocTerm: "text" "(" StringLiteral ")"
       | "line" "(" ")"
       | "softline" "(" ")"
       | "nest" "(" IntLiteral "," DocExpr ")"
       | "group" "(" DocExpr ")"
       | "align" "(" DocExpr ")"
       | "format" "(" Ident ")"
       | "list" "(" Ident "," DocExpr ")"
       | "if" CondExpr "then" DocExpr "else" DocExpr
       | "(" DocExpr ")"
       ;

CondExpr: Ident "==" StringLiteral
        | Ident "is_first"
        | Ident "is_last"
        | "width" "<" IntLiteral
        | CondExpr "&&" CondExpr
        | "(" CondExpr ")"
        ;
```

Advantages:

- Naturally expresses **combinator-based document algebra** (e.g., `text("+") ++ softline() ++ format(right)`).
- Fits directly into Parglare's **grammar + semantic actions** ecosystem: the DSL itself is parsed by Parglare, enabling reuse of tooling and diagnostics.
- Easier to reason about **semantics and correctness**, as the DSL has a well-defined grammar and AST.

Disadvantages:

- Requires a custom parser (implemented via Parglare), rather than relying on JSON/YAML tooling.
- Slightly higher entry barrier for users unfamiliar with textual DSLs.

### 2.3 Chosen Variant

For the master thesis, the **textual DSL** variant is chosen, for the following reasons:

- It better reflects the **research focus on language design** and document algebra, rather than mere configuration.
- It leverages **Parglare directly** as both the parser for the target language and the parser for the formatting DSL, strengthening the "single ecosystem" narrative.
- It enables more expressive constructs (conditionals, context-sensitive predicates) in a way that is easier to specify and implement.

## 3. DSL Semantics

The semantics of the DSL map rule declarations and document expressions to an internal representation used by the document model and layout engine.

### 3.1 Rule Semantics

Each `rule Name(params) = DocExpr;` declaration defines a **formatting rule** for one AST node type (or group of types), with parameters corresponding to the node's fields.

- `Name` is an identifier matching an AST node type (e.g., `Add`, `Mul`, `Num`).
- `params` are formal parameters such as `left`, `right`, `value`, corresponding to child nodes or values.
- `DocExpr` is a document expression describing how to construct the formatted document for this node.

At runtime, the formatter dispatches on the AST node's type (e.g., instance of `Add`) and applies the corresponding rule by binding parameters to the node's fields and evaluating `DocExpr`.

### 3.2 Document Expression Semantics

`DocExpr` and `DocTerm` expressions denote **document-construction computations** in a Hughes/Wadler/Leijen-style algebra:

- `text(s)` constructs a document representing the literal string `s`.
- `line()` represents a **hard line break**, always rendered as `"\n"`.
- `softline()` represents a **soft line break**, rendered as either space or `"\n"` depending on available width and grouping.
- `nest(k, d)` increases indentation by `k` spaces for all lines in the subdocument `d` (except possibly the first, depending on implementation).
- `group(d)` considers both the **flat** layout (softlines as spaces) and the **broken** layout (softlines as `"\n"`) for document `d`, allowing the layout engine to choose whichever fits.
- `align(d)` adjusts indentation to align subsequent lines with the current column, useful for certain alignment patterns.
- `format(x)` recursively formats parameter `x` (expected to be an AST child node or list of nodes) using the appropriate rule.
- `list(xs, sep_doc)` formats a list `xs` of AST nodes or values, inserting `sep_doc` between elements.
- `if CondExpr then d1 else d2` chooses between documents `d1` and `d2` based on a context-sensitive condition.

### 3.3 Condition Semantics

`CondExpr` expressions provide **context-sensitive predicates**:

- `Ident == StringLiteral` compares a parameter or context field to a string (e.g., operator name).
- `Ident is_first` / `Ident is_last` check whether an element is the first or last in a list (useful for separators and trailing commas).
- `width < IntLiteral` tests whether the current line width (or remaining width) is below a threshold, enabling width-dependent formatting.
- Conjunction `&&` combines conditions.

These predicates are interpreted relative to a **formatting context** that includes the current AST node, its parent, its position in lists, and the current layout state (e.g., column, remaining width).

## 4. Document Model

The internal document model is a direct implementation of a pretty-printing algebra inspired by Hughes, Wadler, Leijen, and PrettyExpressive:

### 4.1 Core Types

The core type is `Doc`, representing a structured document with potential line breaks and indentation. It can be implemented as a tagged union or class hierarchy with constructors such as:

- `Empty`
- `Text(s)`
- `Line`
- `SoftLine`
- `Concat(d1, d2)`
- `Nest(k, d)`
- `Group(d)`
- `Align(d)`
- `List(doc_list, sep_doc)`

### 4.2 Combinators

The document model exposes combinators corresponding to DSL constructs:

- `text :: String -> Doc`
- `line :: Doc`
- `softline :: Doc`
- `nest :: Int -> Doc -> Doc`
- `group :: Doc -> Doc`
- `align :: Doc -> Doc`
- `(<>) :: Doc -> Doc -> Doc` (concatenation)
- `list :: [Doc] -> Doc -> Doc`

These combinators are used internally; the DSL compiler translates `DocExpr` ASTs into calls to these combinators in Python.

## 5. Layout Engine (MVP)

The layout engine is responsible for converting a `Doc` into a concrete layout (sequence of lines and indentation) given a maximum line width.

### 5.1 Design Goals

- Respect **hard vs soft line breaks** and indentation.
- Choose between **flat and broken** layouts for `group` when possible.
- Operate in **linear or near-linear time** for typical documents.

### 5.2 Algorithm Sketch

The MVP layout algorithm can follow a simplified Wadler/Leijen strategy:

1. Traverse the `Doc` structure, maintaining a **buffer** of pending document elements and the current column.
2. For `Group(d)`, attempt a **flat rendering** (softlines as spaces); if this fits within the remaining width, use it; otherwise, use a **broken rendering** (softlines as `"\n"`).
3. For `Nest(k, d)`, increase indentation by `k` for lines produced by `d`.
4. For `Align(d)`, recompute indentation based on the current column.

The algorithm produces an intermediate **layout structure** (e.g., list of lines with indentation) which is then rendered to a final string.

### 5.3 Scope Limitations

- The MVP does not implement advanced features such as arbitrary cost functions or global optimality proofs (PrettyExpressive); instead, it focuses on **good-enough near-optimal layouts**.
- Alignment features may be limited to simple patterns (e.g., aligning binary operators), with more complex alignment left to future work.

## 6. Error Handling and Determinism

The DSL and its runtime are designed to behave deterministically:

- Missing rules for AST node types result in a **clear error** (e.g., `UnknownNodeTypeError`), possibly with a configurable default rule.
- Type mismatches in parameters (e.g., passing a list where a single node is expected) are detected and reported.
- Conditions in `CondExpr` that reference unavailable context fields are treated as errors rather than silently failing.

This deterministic behavior is important for debugging and for making formal reasoning about formatting predictable.

## 7. MVP Scope and Example Rules

### 7.1 MVP Feature Set

The minimum viable product (MVP) for the DSL and formatter includes:

- `text`, `line`, `softline`, `nest`, `group`, basic concatenation (`++`).
- `format` for AST node dispatch.
- `list` with a simple separator document.
- Fixed maximum line width parameter.

This set suffices to format a small expression language with binary operators and blocks.

### 7.2 Mini Expression Language Example

Consider a mini expression language with AST node types:

- `Add(left, right)`
- `Mul(left, right)`
- `Num(value)`

The DSL can define rules:

```text
rule Add(left, right) =
  group(
    format(left) ++ text(" + ") ++ softline() ++ format(right)
  );

rule Mul(left, right) =
  group(
    format(left) ++ text(" * ") ++ softline() ++ format(right)
  );

rule Num(value) =
  text(value);
```

These rules express how to pretty-print binary addition and multiplication using grouping and soft line breaks so that expressions can either stay on one line or be broken across lines depending on width.

## 8. Parglare Integration Layer

The integration layer connects Parglare's ASTs to the DSL and document model:

- Parglare parses the **target language** and constructs AST nodes via semantic actions (e.g., `Add`, `Mul`, `Num`).
- Parglare parses the **DSL** (formatter rules) to produce a rule AST (e.g., `RuleDecl`, `DocExpr`).
- A **DSL compiler** translates rule ASTs into Python functions or data structures that build `Doc` values for given AST nodes.
- A **formatter function** (e.g., `format(ast_root, rules, max_width)`) drives the process: dispatching on AST node types, building `Doc` values, invoking the layout engine, and producing the final string.

This layered integration ensures that grammar, parser, AST, and formatter coexist coherently within the Parglare ecosystem.