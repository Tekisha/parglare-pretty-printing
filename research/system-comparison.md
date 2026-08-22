# Systems Comparison: Pretty Printers and Formatting Frameworks

This document compares existing pretty-printing libraries and formatting frameworks along criteria relevant to the design of a Parglare-integrated DSL for AST-to-text formatting.[^1][^2]
It is intended to complement `literature-review.md` by providing a more structured, tabular view of the landscape.

## 1. Comparison Criteria

We compare systems along the following axes:

- **Rule definition style**: imperative visitors, combinators, grammar-embedded rules, declarative layouts, learned models.
- **Relation to grammar**: independent of grammar, loosely related, directly derived from grammar, single-source grammar+formatter.
- **AST support**: formatting over AST, parse trees, or token streams.
- **Context-sensitive rules**: ability to express formatting decisions depending on syntactic/semantic context (e.g., parent node, position in list).
- **Line width handling**: explicit max width parameter, heuristics, or none.
- **Layout optimization**: greedy, near-optimal, provably optimal under a cost function.
- **Comment preservation**: support for preserving comments and original whitespace/layout for unchanged subtrees.
- **Round-trip guarantees**: guarantees that pretty-printed text parses back to the same AST or value.
- **Extensibility**: ease of extending formatting rules or integrating new languages.
- **Integration potential with Parglare**: how naturally the system could be adapted or emulated in a Parglare+DSL setting.

These criteria will be refined as the design of the Parglare-integrated DSL solidifies.

## 2. High-Level Comparison Table

Below is an initial, high-level comparison of representative systems. Cells are intentionally concise; detailed explanations are maintained in `literature-review.md`.

| System                | Rule definition style                | Relation to grammar                | AST / parse / tokens        | Context-sensitive rules      | Line width handling                 | Layout optimization                    | Comment preservation              | Round-trip guarantees                | Extensibility                     | Integration potential with Parglare |
|-----------------------|--------------------------------------|------------------------------------|-----------------------------|------------------------------|--------------------------------------|----------------------------------------|-----------------------------------|-------------------------------------|------------------------------------|-------------------------------------|
| Hughes/Wadler/Leijen | Combinators over `Doc`               | Independent of grammar             | AST or abstract documents   | Limited (local structure)    | Explicit `width` parameter           | Near-optimal, efficient algorithms      | None built-in                    | No formal round-trip focus          | High for document-style tasks      | High (document algebra can be re-used in DSL) |
| PrettyExpressive (Π_e)| Combinators + cost factories          | Independent of grammar             | AST or structured values    | Via cost function/context    | Explicit, flexible width handling    | Provably optimal under user-defined cost| None built-in                    | Round-trip not central focus        | High; used in OCaml/Racket         | Very high (inspiration for layout engine) |
| De Jonge/Vinju       | Grammar-related, framework-based      | Closely tied to grammar & reengineering tools | AST + layout segments      | Yes (layout-preserving alg.) | Heuristic, framework-specific        | Layout-preserving rather than optimality | Strong for unchanged subtrees    | Strong for reengineering pipelines  | Medium–high within their ecosystem | Medium (concepts can inspire DSL integration) |
| Van den Brand et al. | Context-sensitive formatting framework | Grammar-related, language-independent specs   | AST + token streams        | Yes, rich context-sensitive rules | Heuristic, multi-stage pipeline       | Focus on flexibility over formal optimality | Supports complex legacy layouts   | Not primary goal                    | High for industrial languages      | Medium (ideas for multi-stage pipeline) |
| PGF (Pretty Good Formatting Pipeline) | Imperative pipeline with configurable stages | Loosely related to grammar            | Token streams derived from AST | Limited, encoded per stage     | Heuristic, stage-specific algorithms | Near-optimal heuristics in practice        | Limited explicit support         | No strict guarantees                | High (modular pipeline)           | Medium–high (pipeline pattern can be mirrored) |
| AnyText              | Extended EBNF with embedded formatting | Single-source grammar+formatter     | AST + incremental parse results | Yes (via grammar annotations) | Explicit layout declarations        | Depends on layout rules; not primarily optimality-focused | Potential for comment/layout preservation | Designed for editor round-trips    | High for DSLs in its ecosystem    | High conceptual relevance (single source of truth) |
| CODEBUFF             | Learned rules from corpus             | Uses ANTLR parse trees              | Parse trees + feature vectors | Yes (local parse context)    | Implicit via learned decisions      | Empirical; no formal optimality proofs     | Implicit (depends on training data) | No formal guarantees; empirical quality | High (minimal manual configuration)| Low–medium (ML approach orthogonal to Parglare DSL) |
| BiYacc               | Bidirectional DSL (parser + printer)  | Single specification for parse/print| AST + textual representation | Limited, via spec structure   | Not central; focuses on correctness | Focus on correctness, not optimal layout   | Depends on implementation         | Strong syntactic round-trip guarantees | Medium (requires bespoke DSL)     | Medium (ideas for bidirectional specs) |
| 

---

*This file is a living document: as the thesis work progresses, new systems may be added, and existing entries refined or split into multiple rows.*