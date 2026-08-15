# plantuml-lsp

PlantUML language server, built on
[tree-sitter-plantuml](https://gitlab.semantiqa.dev/deriva/plantuml/tree-sitter-plantuml)
and [plantuml-fmt](https://gitlab.semantiqa.dev/deriva/plantuml/plantuml-fmt).
Third product of the `deriva/plantuml` toolchain family.

## Features (v0)

- **Diagnostics** — parse errors with exact positions, straight from the
  grammar's error-tolerant CST.
- **Document symbols** — classes, interfaces, enums (namespace-qualified),
  packages/namespaces and sequence participants.
- **Go to definition across includes** — `!includesub file!NAME` jumps to
  the `!startsub NAME` line of the referenced file; `!include file` jumps
  to the file.
- **Formatting** — `textDocument/formatting` delegates to `plantuml-fmt`.

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
