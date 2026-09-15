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
