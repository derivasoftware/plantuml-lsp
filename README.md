# plantuml-lsp

<!-- folio: colophon --project plantuml-lsp --junit test-results/junit.xml --coverage_ut test-results/coverage-ut.xml -->
![powered by: argos](https://img.shields.io/badge/powered%20by-argos-1f6feb) ![traced: 100%](https://img.shields.io/badge/traced-100%25-2ea44f) ![verified: 100%](https://img.shields.io/badge/verified-100%25-2ea44f) ![tests: 100%](https://img.shields.io/badge/tests-100%25-2ea44f) ![UT: 78%](https://img.shields.io/badge/UT-78%25-dfb317) ![ST: n/a](https://img.shields.io/badge/ST-n%2Fa-lightgrey) ![diagnostics: 0](https://img.shields.io/badge/diagnostics-0-2ea44f)

> **plantuml-lsp** is powered by **argos**. **folio** generates this documentation from the repository's model: 14 requirements · 14 verifications · 0 constraints. Quality: 100% traced to code · 100% verified · 100% tests passing · 78% UT coverage.
<!-- /folio -->

PlantUML language server, built on
[tree-sitter-plantuml](https://github.com/derivasoftware/tree-sitter-plantuml)
and [plantuml-fmt](https://github.com/derivasoftware/plantuml-fmt).
Part of the `deriva/plantuml` family: grammar → formatter → LSP → editor.

## Install

Straight from git; pip resolves the grammar and formatter dependencies
itself. The block below is generated from the manifest and the latest tag:

<!-- folio: install -->
```bash
pip install git+https://github.com/derivasoftware/plantuml-lsp.git@v0.7.3
```

Or from a clone: `git clone https://github.com/derivasoftware/plantuml-lsp && pip install ./plantuml-lsp`.
<!-- /folio -->

Then run `plantuml-lsp`; it speaks LSP over stdio.

## Use cases

**Neovim**: install
[plantuml.nvim](https://github.com/derivasoftware/plantuml.nvim).
It builds the pinned grammar, wires this server and enables completion,
hover, navigation and lints with no further setup.

**Any LSP client**: point it at the `plantuml-lsp` binary (stdio) for
`.puml` and `.plantuml` files. [doc/clients.md](doc/clients.md) covers
VS Code and Helix wiring plus the capability table.

**What you get**: workspace-aware intelligence over the document, its
`!include` closure and every diagram under the root.

- Go to definition across includes, entities and method calls; sequence
  labels and activity actions are calls, and swimlanes name receivers.
- Semantic lints: undeclared endpoints, duplicate declarations, broken
  includes, and method calls no class declares (drift).
- Contextual completion, auto-triggered: receiver methods after `:`,
  participants after arrows, lane methods in activities.
- References and rename across the whole workspace, CST-backed; labels,
  comments and note bodies are never touched.
- Hover cards, workspace symbols, clickable include paths.
- Formatting delegated to plantuml-fmt: editor and pre-commit emit the
  same bytes.

## Scope

The family covers a standard-driven subset of PlantUML, never the whole
language. Class diagrams: 125 of 149 standard constructs structural;
sequence: 70 of 111, with the lifecycle verbs (activate, ref, box,
delays) still raw; activity: actions and swimlanes structural, control
flow raw. Everything else (deployment, components, state, mindmaps,
gantt) parses lossless as raw lines, never an ERROR, but gets no
structure. The language intelligence applies to the structured
subset; other diagram types get parse diagnostics only.

## Documentation

- [Client wiring](doc/clients.md): VS Code, Neovim, Helix; capability table
- [Architecture](doc/architecture.md): the model's diagrams, rendered from source
- [Requirements & status](doc/requirements.md): what was asked and the traceability matrix
- [Repo quality](doc/quality.md): artefact inventory and health metrics

*Not affiliated with or endorsed by the PlantUML project.*
