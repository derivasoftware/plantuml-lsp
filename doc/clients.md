# Wiring an editor to plantuml-lsp

The server speaks LSP over **stdio**; install it where the editor can
spawn it:

```bash
pip install git+https://github.com/derivasoftware/plantuml-lsp.git@v0.8.6
```

## VS Code

Install the family's own
[plantuml-vscode](https://github.com/derivasoftware/plantuml-vscode)
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

## Capabilities

| Capability | Behaviour |
|---|---|
| diagnostics | parse errors + semantic lints (unknown endpoints in class mode, duplicates, broken includes, class-cased participants no workspace class or HLD box explains, method calls a correlated class does not declare) |
| completion | contextual: receiver methods after a message colon (signatures as detail), participants after arrows, lane methods in actions, keywords only at statement heads |
| hover | kind, display name, members, relation lines, declaration site; participants add the card of the class or HLD box they play; a call to a receiver no class correlates with shows the homonymous method, marked as such |
| references | CST-backed occurrences across the closure and the whole workspace |
| rename | closure- and workspace-wide (editor previews every edit), never touches labels/comments/note bodies; quoted names keep quotes |
| workspace/symbol | jump to any entity of any diagram under the root |
| documentLink | clickable `!include`/`!includesub` paths |
| codeAction | quick fixes: declare the missing entity, fix the include path to the closest file, declare the drifting method in the receiver's class |
| documentSymbol | classes/interfaces/enums (namespace-qualified), packages/namespaces, sequence participants |
| definition | `!includesub file!NAME` → the `!startsub NAME` line; `!include file` → the file; an entity, participant or HLD box name → its declaration across the workspace; a call label or activity action → the declared method (best effort for a classless receiver) |
| formatting | delegates to plantuml-fmt (one style, everywhere) |

Semantic tokens are deliberately absent: VS Code highlights via the
pack's TextMate grammar and native tree-sitter editors highlight from
the grammar itself.

## Development notes

- pygls **2.x** (`pygls.lsp.server`; publish diagnostics via
  `text_document_publish_diagnostics(PublishDiagnosticsParams)`).
  Pinned `>=2,<3` — the 1→2 rename broke us once; a smoke test now
  imports the server module so a future rename fails in CI, not at
  runtime.
- New capabilities follow the family TDD flow: failing test → handler
  over the CST → REQ + VER.
