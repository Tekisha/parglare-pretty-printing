# Literature Review: Pretty Printing, AST-to-Text Transformations, and Formatter Architectures

## 1. Overview

This document collects and structures the literature relevant to AST-to-text pretty printing and formatter design, with a focus on foundations (document algebra), grammar-directed and context-sensitive formatting, round-trip and layout-preserving transformations, machine-learning-based formatters, and parser–AST–printer integration.
It serves as the "related work" backbone for the master thesis on a Parglare-integrated DSL for declarative formatting rules.

## 2. Classical Document Algebra and Combinator-Based Pretty Printing

Early work on pretty printing in functional programming introduced the idea of a document algebra, where structured documents are constructed via combinators and later rendered to text under line-width constraints.
Hughes's design of a pretty-printing library and Wadler's "A Prettier Printer" established the key primitives: text, line breaks, indentation (nesting), and composition, along with algorithms that choose between different layouts to minimize height or overflow under a given width.

Leijen's `wl-pprint` library, described in its documentation, extends Wadler’s original set of combinators with additional primitives such as `align`, `fill`, and `fillBreak`, and provides dedicated renderers (`renderPretty` and `renderCompact`). These extensions made the combinator-based approach practical for pretty-printing source code and other structured data in real-world languages.

## 3. Core Concepts

### 3.1 Abstract Syntax Trees (AST) and Parse Trees

Parsing source code typically produces a parse tree that mirrors the grammar's productions, and from this, a more compact abstract syntax tree (AST) is derived by removing syntactic sugar and irrelevant nonterminals.
ASTs are used as the primary representation for analysis and transformation, while parse trees and token streams (including comments and whitespace) are retained only when layout and original source positions must be preserved.

### 3.2 Unparsing vs. Pretty Printing

Unparsing is the mechanical transformation from AST (or parse tree) back to text based on the grammar, aiming primarily for syntactic correctness rather than human-friendly layout.

Pretty printing, in contrast, is an AST-to-text process that applies formatting conventions such as indentation, grouping, and controlled line breaking to produce readable and stylistically consistent source code under constraints such as maximum line width.

In many compiler toolchains and language workbenches, unparser specifications are attached to grammar productions, whereas pretty printers use richer layout combinators or separate specification languages to encode formatting rules that are not inherent in the grammar.

### 3.3 Document, Layout, and Line Breaking

Document models represent structured text with potential line breaks, indentation, and alternative layouts, abstracting away from concrete strings.

Rendering a document involves two main steps. First, a layout is chosen by assigning line breaks and spaces. This assignment follows an objective, such as minimizing the total height of the output or avoiding overflow beyond a given line width. Second, the chosen layout is converted into a final string.

Line breaking is controlled by primitives such as hard line breaks (always emit `\n`) and soft line breaks (either space or `\n` depending on available width), combined with grouping constructs that consider flat vs. broken layouts.

Indentation and nesting combinators adjust the column position for subsequent lines, ensuring that the visual structure of the output reflects the underlying tree structure.

### 3.4 Grouping, Indentation, and Optimal Layout

Grouping allows a document to be considered in multiple layouts (e.g., all soft breaks as spaces vs. as newlines), enabling pretty printers to choose the best arrangement given width constraints.

Indentation (nesting) specifies how far to shift lines under a subdocument, often expressed as a fixed number of spaces or tabs, and is crucial for properly formatting blocks, nested expressions, and aligned constructs.

Classical Hughes/Wadler/Leijen printers generally seek near-optimal layouts in linear or near-linear time, while newer work such as PrettyExpressive formalizes expressiveness and optimality, using cost factories and formal proofs to guarantee that chosen layouts minimize the specified objective.

## 4. Classification of Existing Approaches

Existing work on pretty printing and formatting can be grouped into several broad families, differing in how they express rules, relate to grammars, and integrate with parsers and ASTs.

### 4.1 Imperative Visitor-Based Printers

A common approach in compilers and interpreters is to implement pretty printing imperatively, using the Visitor pattern over AST nodes.

Each node type defines or is associated with a print/visit method that emits text, manually managing indentation levels, line breaks, and spacing, often with helper classes for indentation and buffering.

This style is straightforward and flexible, and is frequently used with Oppen-style pretty printers where a visitor emits formatting tokens into a language-independent backend.

However, it typically lacks a formal document algebra or declarative rule language, making reasoning about expressiveness, optimality, and cross-language reuse more difficult.

### 4.2 Combinator-Based Pretty Printers

Combinator-based systems define a small set of document constructors (e.g., text, line, softline, nest, group) and combinators that build structured documents, which are then rendered under width constraints.

Hughes, Wadler, and Leijen’s libraries are archetypal: they operate over Doc values, providing algorithms that choose between alternative layouts (flat vs broken) to minimize overflow or height.

Recent work such as the Final Pretty Printer and PrettyExpressive refines this algebraic approach, introducing monadic or cost-based frameworks that increase expressiveness and support formal reasoning about layout quality.

These systems are typically grammar-agnostic and language-independent, serving as reusable libraries that can be applied to arbitrary ASTs or structured data.

### 4.3 Grammar-Directed Printers

Grammar-directed formatters derive printing rules directly from or in close relation to the language grammar.

Early work on generating formatters for context-free languages showed how typeset documentation could be produced automatically from annotated grammars, and De Jonge’s generic pretty printer (GPP) introduced BOX terms and pretty-print tables that map productions to formatting rules.

In these systems, formatting specifications are often stored alongside grammars, enabling reuse of grammar-based specifications for parsing, transformation, and pretty printing in software reengineering and documentation generation.

AnyText extends this idea by using a single extended EBNF grammar with embedded formatting instructions, from which both parser and pretty printer are generated.

### 4.4 Declarative Formatters and Layout Declarations

Declarative formatting systems specify indentation and layout rules at a higher level of abstraction, often via dedicated DSLs or annotations.

Declarative Indentation Rules, for example, introduce layout declarations for indentation-sensitive languages and separate pp-layout declarations for language-agnostic pretty printing, enabling generation of parsers and formatters that respect indentation syntax.

PGF (Pretty Good Formatting Pipeline) adopts a pipeline architecture where ASTs are converted into token streams and processed by configurable stages for spacing, line breaking, and indentation, allowing declarative configuration of each stage.

These approaches emphasize clarity of specification and language independence, though they may not expose a full document algebra to end users.

### 4.5 Machine-Learning Formatters

Machine-learning formatters such as CODEBUFF learn formatting rules from a corpus of example code, using parse trees and a feature set describing local syntactic context.

They aim to reproduce project-specific coding styles automatically, reducing manual configuration and rule writing.

CODEBUFF uses ANTLR grammars and parse trees, trains models to predict spaces, newlines, and indentation decisions, and demonstrates high accuracy and grammar invariance for a given language.

These systems, however, encode rules implicitly in trained models rather than explicit DSLs, complicating formal reasoning about layout optimality, round-trip properties, or integration with grammar-level declarations.

### 4.6 Bidirectional and Round-Trip Systems

Bidirectional systems and round-trip-oriented pretty printers focus on ensuring that parsing and printing are mutually consistent and that layout and comments are preserved where possible.

BiYacc presents a bidirectional DSL where a single specification denotes both a parser (“get”) and a reflective printer (“putback”), providing syntactic round-trip guarantees between ASTs and textual representations.

Correct-by-construction pretty printing uses dependent types and document combinators to enforce that pretty-printed text, when parsed, yields the original value, emphasizing value-level round-trip correctness.

Layout-preserving refactoring algorithms (De Jonge, Vinju) define strategies for preserving comments and whitespace in unchanged subtrees during source-to-source transformations, supporting conservative reformatting.

## 5. Detailed Analysis of Key Systems

This section briefly summarizes representative systems that inform the design of the Parglare-integrated DSL.

### 5.1 De Jonge – Generic Pretty Printer (GPP) for Software Reengineering

De Jonge’s work on pretty printing for software reengineering introduces a generic pretty printer (GPP) that separates language-dependent front-ends from language-independent back-ends using BOX terms.

Programs are parsed into parse trees, converted to BOX structures via pretty-print tables that map grammar productions to formatting rules, and then rendered to multiple output formats such as plain text, HTML, and LaTeX.

The system emphasizes language independence, extensibility, customization via user profiles, comment preservation, and incremental and conservative pretty printing, making it suitable for reengineering pipelines over large legacy codebases.

For this thesis, GPP demonstrates how grammar-related formatting rules and intermediate document representations (BOX) can support layout-preserving transformations and multi-format output, inspiring the design of an AST-centric but grammar-aware DSL for Parglare.

### 5.2 Van den Brand et al. – Context-Sensitive Formatting Framework

Van den Brand and co-authors propose a language-independent framework for context-sensitive formatting, targeting industrial languages such as COBOL with complex and non-standard formatting conventions.

The framework uses formatting specifications and multi-stage processing to support context-sensitive rules, enabling tailorable formatters for software maintenance and reengineering.

Their evaluation on large legacy code bases (~80k LOC) shows that the framework can handle diverse layout conventions and support customization for different customers and dialects.

For the Parglare-based DSL, this work illustrates the importance of context-sensitive formatting (depending on syntactic and semantic context) and multi-stage architectures, suggesting that the DSL and layout engine should accommodate context-based rules and possibly staged processing.

### 5.3 PGF – A Pretty Good Formatting Pipeline

The Pretty Good Formatting Pipeline (PGF) by Bagge and Hasu adopts a pipeline architecture where ASTs are transformed into token streams and then passed through successive stages handling spacing, line breaking, and indentation.

Each stage can be configured and extended, allowing experimentation with different heuristics and algorithms, including novel line-breaking strategies.

PGF demonstrates that an imperative, pipeline-based approach can be modular and extensible, separating concerns such as spacing and line breaking while retaining configurability.

In this thesis, PGF serves as a conceptual model for how a Parglare-integrated DSL might interact with staged processing, even though the proposed DSL focuses on document algebra and AST-based rules rather than explicit token pipelines.

### 5.4 AnyText – Single Grammar for Parsing, Formatting, and LSP

AnyText is a language workbench that uses a scannerless, incremental packrat parser with support for left recursion, based on an extended EBNF grammar that includes formatting instructions.

From this single grammar, AnyText derives a parser, a pretty printer, and additional tooling such as model construction and LSP-based editor services (semantic tokens, completions, folding).

Formatting instructions embedded in the grammar provide a unified source of truth for parsing and pretty printing, evaluated on multiple DSLs with benchmarks measuring performance and manual effort.

AnyText is directly relevant for a Parglare-centric DSL: it shows that embedding formatting information in or alongside grammars can yield coherent systems where grammar, parser, and formatter evolve together, motivating grammar-level references in the proposed DSL while keeping the implementation in Python.

### 5.5 PrettyExpressive – Expressiveness and Optimality

“A Pretty Expressive Printer” introduces a pretty printer that is strictly more expressive than existing systems and minimizes a user-defined cost function for layout selection.

The work formalizes a framework for comparing the expressiveness of pretty-printing languages and analyzes existing printers in terms of expressiveness, optimality, complexity, and practical performance.

PrettyExpressive is implemented in OCaml and Racket, and serves as the basis for Racket’s code formatter, demonstrating that high expressiveness and provably optimal layout can be practical in production toolchains.

For the thesis, PrettyExpressive provides conceptual guidance for the layout engine: the MVP adopts a simplified Wadler/Leijen-style algorithm but is designed with awareness of more expressive and optimal frameworks that could inform future extensions.

### 5.6 CODEBUFF – Machine-Learning Code Formatter

CODEBUFF is a machine-learning-based code formatter that learns spacing, newline, and indentation decisions from a representative corpus of code using ANTLR grammars and parse trees.

It constructs feature vectors describing local parse context and trains models to predict formatting actions, achieving high accuracy and grammar invariance for each target language.

Experiments on Java, SQL, and ANTLR grammars show that CODEBUFF can reproduce project-specific formatting styles with minimal manual configuration.

Although CODEBUFF does not offer a declarative formatting DSL or formal layout guarantees, it highlights the potential for ML-assisted formatting; in this thesis, ML integration is recognized as future work that could complement the Parglare-integrated DSL by generating or refining rules from examples.


## 6. Parser–AST–Printer Integration

Different systems integrate parsers, ASTs, and pretty printers at different levels, which informs how a Parglare-based DSL should position itself.

### 6.1 Grammar-Level Integration

Grammar-directed and layout-declaration systems embed formatting information in or near the grammar specification.

De Jonge’s GPP uses pretty-print tables keyed by productions, BOX terms, and generic front-ends to connect parse trees to formatting, while AnyText uses an extended EBNF grammar with formatting instructions to derive both parser and pretty printer from a single source.

Declarative Indentation Rules similarly attach indentation and layout declarations to grammars, enabling generalized parsers and pretty printers for indentation-sensitive languages.

These approaches suggest that formatting specifications can be tightly coupled with grammars, providing a pathway towards “single source of truth” designs where grammar and formatter are co-evolved.

### 6.2 AST-Level Integration

Combinator-based libraries and many imperative visitors operate at the AST level, treating grammars and parsers as separate concerns.

Parsing produces an AST, and the pretty printer consumes that AST using document algebra or explicit visitor methods, often without direct references to grammar productions.

PrettyExpressive and correct-by-construction pretty printers exemplify AST-level integration: they operate over structured values or AST nodes, focusing on expressiveness and correctness of document construction rather than grammar-level annotations.

For the Parglare-integrated DSL, AST-level integration is central: rules dispatch on AST node types constructed by Parglare’s semantic actions, while grammar-level information remains available as context where needed.

### 6.3 Token/Layout-Level Integration

Systems concerned with layout preservation and comment handling often operate at the token or layout level.

PGF’s pipeline processes token streams derived from ASTs, with stages that adjust spacing, line breaks, and indentation; layout-preserving refactoring algorithms track comments and whitespace segments to retain existing layout for unchanged code regions.

These approaches highlight the importance of token-level and layout-segment information for format-preserving transformations and comment-aware formatting.

In the proposed Parglare-based architecture, such integration is viewed as future work: Parglare’s scannerless capabilities and token metadata offer hooks for incorporating token-level and layout-preserving techniques on top of the AST-centric DSL.

### 6.4 Implications for the Parglare-Integrated DSL

The literature indicates that an effective formatting system should:

Support AST-level declarative rules (for clarity and reuse).

Be aware of grammar-level structures when needed (for single-source designs).

Provide hooks to integrate token/layout-level information for format-preserving behavior.

The Parglare-integrated DSL is therefore designed to be AST-centric with grammar-aware references and a path towards future token/layout integration, leveraging Parglare’s grammar language, semantic actions, and metadata facilities.

