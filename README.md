# plantuml-lsp

PlantUML language server, built on
[tree-sitter-plantuml](https://gitlab.semantiqa.dev/deriva/plantuml/tree-sitter-plantuml)
and [plantuml-fmt](https://gitlab.semantiqa.dev/deriva/plantuml/plantuml-fmt).
Third product of the `deriva/plantuml` toolchain family.

## Features (v1)

Workspace-aware: a symbol index over the document **plus its transitive
`!include`/`!includesub` closure** feeds everything below.

- **Diagnostics** — parse errors with exact positions, plus semantic
  lints: relation endpoints nothing declares (class mode; sequence
  stays quiet — implicit participants are idiomatic), duplicate
  declarations, and include targets or fragments that don't exist.
- **Completion** — every entity/participant in the closure plus
  statement keywords.
- **Hover** — kind, display name, members, relation lines, declaration
  site.
- **References / Rename** — CST-backed occurrences across the closure;
  renames never touch labels, comments or note bodies, and quoted
  names keep their quotes.
- **Document links** — `!include` paths are clickable.
- **Document symbols** — classes, interfaces, enums (namespace-qualified),
  packages/namespaces and sequence participants.
- **Go to definition across includes** — `!includesub file!NAME` jumps to
  the `!startsub NAME` line of the referenced file; `!include file` jumps
  to the file.
- **Formatting** — `textDocument/formatting` delegates to `plantuml-fmt`.

## Documentation

- [`doc/clients.md`](doc/clients.md) — wiring VS Code, Neovim and
  Helix; the capability table; pygls 2 notes.

## Usage

```bash
plantuml-lsp        # speaks LSP over stdio
```

Point any LSP client at it for `.puml` files. In VS Code, wire it as a
custom server (argos-vscode will ship the client side).

## Development

```bash
python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"
./.venv/bin/pytest
```

## Governance

An [argos](https://gitlab.semantiqa.dev/deriva/argos/argos) NA project:
input requirements in `input/`, requirements and verifications in
`requirements/` and `verifications/`. See `CLAUDE.md`.
