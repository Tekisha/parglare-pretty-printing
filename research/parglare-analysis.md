# Parglare Analysis: Grammar, AST Construction, and Integration Points

This document analyses Parglare as a LR/GLR parsing library for Python, with a focus on the aspects that matter for integrating an AST-to-text pretty-printing DSL: grammar definition, parse-tree and AST construction, semantic actions, metadata and source locations, and potential integration points for a formatter.
It is intended to serve as the dedicated "tooling" chapter for the master thesis, complementing the more general literature review.

## 1. Parglare in Brief

Parglare is a pure-Python parsing library that implements deterministic LR parsing and its generalized extension GLR, with optional scannerless operation.
It provides a grammar language (defined in `.pg` files or Python strings), integrated tokenization, conflict diagnostics, and APIs for constructing parse trees or higher-level results via semantic actions.

## 2. Grammar Definition

### 2.1 Grammar Language and `.pg` Files

Parglare uses a BNF-style grammar language with optional syntactic sugar, which can be stored in `.pg` files or embedded as strings in Python code.
A typical grammar defines nonterminals with productions and a `terminals` section with regular-expression-based token definitions, for example:

```text
Expression: Expression "+" Term {left, 1}
          | Term
          ;

Term: NUMBER ;

terminals
NUMBER: /[0-9]+/ ;
```

Grammars can be loaded using `Grammar.from_file("grammar.pg")` or `Grammar.from_str(text)`, and then passed to `Parser` to create an LR or GLR parser.

### 2.2 LR and GLR Modes

The same grammar specification can be used for LR and GLR parsing, with GLR handling ambiguity and non-LR grammars by producing parse forests.
Parglare's `pglr` command-line tool can analyze grammars, report conflicts, and visualize automata, which is useful for debugging both target languages and the formatting-DSL grammar itself.

## 3. Parse Trees, Parse Forests, and ASTs

### 3.1 Parse Trees and `build_tree`

By default, Parglare reduces input using semantic actions and returns the result of those actions; alternatively, it can be configured to build a parse tree by setting `build_tree=True` in the parser.
The resulting parse tree mirrors the grammar structure and can later be traversed or transformed into an AST.

### 3.2 GLR Parse Forests

In GLR mode, ambiguous or non-LR grammars produce a parse forest (a compact representation of multiple possible parse trees), from which a specific tree can be selected using disambiguation strategies or semantic actions.
For formatting, GLR is primarily relevant when the target language or the DSL grammar admits ambiguity that must be resolved before constructing an AST suitable for pretty printing.

### 3.3 AST Construction via Semantic Actions

Most Parglare usage patterns construct ASTs directly during parsing by attaching Python callables (semantic actions) to grammar rules or alternatives.
For example, a rule for addition might be associated with an action that builds an `Add(left, right)` node, while a terminal rule creates a `Num(value)` node.
This allows the parser to return an AST root value instead of a raw parse tree, which is ideal for an AST-centric pretty printer and its DSL.

## 4. Semantic Actions and Reduction Functions

### 4.1 Attaching Actions to Grammar Rules

Semantic actions in Parglare are functions that receive a parsing context and a list of child nodes, and return a value representing the reduced construct (e.g., an AST node).
Actions can be registered via a dictionary mapping rule names or alternatives to callables, or via decorators in Python code, depending on the chosen API style.

### 4.2 On-the-Fly vs. Post-Parsing Actions

Actions can be applied during parsing (on-the-fly reduction), or, when `build_tree=True` is used, applied afterwards by calling `parser.call_actions(tree)`, which walks the parse tree and invokes actions to produce AST nodes.
This flexibility is useful for integrating a formatter: one can choose to build a clean AST for pretty printing, or to retain a parse tree alongside an AST when format-preserving behavior requires access to original tokens and layout.

## 5. Metadata and Source Locations

### 5.1 Token Positions

Parglare's integrated scanner and token recognizers can provide positional information such as line and column numbers for tokens; these can be stored in token objects or propagated into AST nodes via semantic actions.
Such metadata is essential for later mapping AST nodes back to their locations in the original source code, for example when highlighting, refactoring, or performing layout-preserving transformations.

### 5.2 Comments and Whitespace

While Parglare does not provide first-class comment/layout preservation out of the box, its scannerless capabilities and flexible token definitions allow comments and whitespace to be tokenized and associated with surrounding constructs.
Combined with techniques from layout-preserving algorithms in the literature, this opens the door to a format-preserving or comment-aware pretty-printing layer built on top of Parglare.

## 6. Potential Integration Points for a Pretty Printer

Given Parglare's model, several integration points for an AST-to-text DSL-based pretty printer can be identified:

### 6.1 AST-Level Integration

The primary integration point is the AST produced by semantic actions: the formatter DSL can be designed to dispatch rules based on AST node types and fields (e.g., `Add`, `Mul`, `Num`), mapping each node type to a document-construction rule.
This AST-centric integration aligns with classical combinator-based pretty printing and the DSL design described elsewhere in the project.

### 6.2 Parse-Tree-Level Integration

When format-preserving behavior is important, parse trees can be retained alongside ASTs, with the formatter using parse-tree information (e.g., original token order, comments, whitespace segments) to decide when to reuse existing layout vs. reformat.
In GLR scenarios, the formatter would operate on a selected parse tree derived from the parse forest.

### 6.3 Grammar-Level Integration

Parglare's grammar language can serve as a natural anchor for formatting specifications: an extended grammar or a companion DSL can refer to nonterminals and productions when defining formatting rules, similar in spirit to AnyText's extended EBNF with embedded layout instructions.
This grammar-level integration supports a "single source of truth" approach in which parser and formatter evolve together.

### 6.4 Tooling and Command-Line Support

The `pglr` command-line tool and grammar diagnostics can be leveraged when developing the DSL grammar itself (for formatting rules), ensuring that both the target language grammar and the DSL grammar remain well-formed and free of problematic conflicts.

## 7. Summary for DSL Design

From the perspective of the planned Parglare-integrated DSL for pretty printing:

- Parglare provides a robust grammar language and LR/GLR parsing engine suitable for both the target language and the DSL itself.
- Semantic actions offer a clean way to construct ASTs with embedded metadata, which the DSL can then format according to declarative rules.
- Parse trees, token metadata, and scannerless operation offer hooks for future work on layout-preserving and comment-aware formatting.
- Grammar-level references and the possibility of extended grammars make it feasible to approach a "single source of truth" for grammar, parser, and formatter, inspired by systems like AnyText but tailored to Parglare.

This analysis justifies treating Parglare not only as a parser for the target language, but also as an enabling technology for the formatting DSL itself (parsing DSL rules, providing ASTs, and hosting the integration layer).
