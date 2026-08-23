# Wiring an editor to plantuml-lsp

The server speaks LSP over **stdio**; install it where the editor can
spawn it:

```bash
pip install plantuml-lsp \
  --index-url https://gitlab.semantiqa.dev/api/v4/groups/deriva/-/packages/pypi/simple
```

## VS Code

Install the family's own
[plantuml-vscode](https://gitlab.semantiqa.dev/deriva/plantuml/plantuml-vscode)
pack — it ships the client. Settings: `plantuml.lsp.path` (default
`plantuml-lsp`, resolved through PATH) and `plantuml.lsp.enabled`.

## Neovim (lspconfig)

```lua
vim.filetype.add({ extension = { puml = "plantuml" } })
require("lspconfig.configs").plantuml_lsp = {
  default_config = {
    cmd = { "plantuml-lsp" },
    filetypes = { "plantuml" },
    root_dir = require("lspconfig.util").root_pattern(".git"),
  },
}
require("lspconfig").plantuml_lsp.setup({})
```

## Helix

```toml
# languages.toml
[language-server.plantuml-lsp]
command = "plantuml-lsp"

[[language]]
name = "plantuml"
scope = "source.plantuml"
file-types = ["puml", "plantuml", "iuml", "wsd"]
language-servers = ["plantuml-lsp"]
```

## Capabilities (v0)

| Capability | Behaviour |
|---|---|
| diagnostics | parse errors with exact ranges, from the grammar's error-tolerant CST |
| documentSymbol | classes/interfaces/enums (namespace-qualified), packages/namespaces, sequence participants |
| definition | `!includesub file!NAME` → the `!startsub NAME` line; `!include file` → the file |
| formatting | delegates to plantuml-fmt (one style, everywhere) |

## Development notes

- pygls **2.x** (`pygls.lsp.server`; publish diagnostics via
  `text_document_publish_diagnostics(PublishDiagnosticsParams)`).
  Pinned `>=2,<3` — the 1→2 rename broke us once; a smoke test now
  imports the server module so a future rename fails in CI, not at
  runtime.
- New capabilities follow the family TDD flow: failing test → handler
  over the CST → REQ + VER.
