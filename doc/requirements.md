# Requirements & status

## What was asked

The system requirements, with a check for implemented (its requirements
land on diagrams that resolve to code) and one per test suite: UT and ST
say whether that suite's last run covered the requirement's verification
tests with no failures. The server's system suite is the plantuml.nvim
integration harness, which runs in that repository; until its evidence
is wired across, the ST column reads unknown.

<!-- folio: sreqs --junit test-results/junit.xml -->
| SREQ | Title | Implemented | UT | ST |
| --- | --- | --- | --- | --- |
| `SREQ-00001-1` | The tool shall serve PlantUML language intelligence over the Language Server Protocol | ✓ | ✓ | ? |
| `SREQ-00002-1` | The server shall publish parse diagnostics with exact positions | ✓ | ✓ | ? |
| `SREQ-00003-1` | The server shall expose document symbols for the supported subset | ✓ | ✓ | ? |
| `SREQ-00004-1` | The server shall resolve includesub references to their startsub definitions | ✓ | ✓ | ? |
| `SREQ-00005-1` | The server shall format documents through plantuml-fmt | ✓ | ✓ | ? |
| `SREQ-00006-1` | The server shall provide workspace-aware language intelligence over the include closure | ✓ | ✓ | ? |
| `SREQ-00007-1` | The server shall correlate entities across every diagram of the workspace | ✓ | ✓ | ? |
<!-- /folio -->

## Total traceability

One system requirement per row, joined across the V: its requirements,
the diagrams they trace to, the classes or modules on those diagrams,
how many verification test ids the unit and system runs matched, and
the verifications.

<!-- folio: matrix --junit test-results/junit.xml -->
| SREQ | Requirements | Diagrams | Classes | UT | ST | Verifications |
| --- | --- | --- | --- | --- | --- | --- |
| `SREQ-00001-1` | — | `HLD_PlantumlLsp` | — | 0 | ? | — |
| `SREQ-00002-1` | `REQ-00001-1` | `CL_Diagnostics`<br>`CL_Parsing`<br>`CL_PlantumlLsp`<br>`CL_Server` | `plantuml_lsp.actions`<br>`plantuml_lsp.completion`<br>`plantuml_lsp.definitions`<br>`plantuml_lsp.diagnostics`<br>`plantuml_lsp.hover`<br>`plantuml_lsp.index`<br>`plantuml_lsp.links`<br>`plantuml_lsp.lints`<br>`plantuml_lsp.parsing`<br>`plantuml_lsp.rename`<br>`plantuml_lsp.server`<br>`plantuml_lsp.symbols`<br>`plantuml_lsp.workspace` | 2 | ? | `VER-00001-1` |
| `SREQ-00003-1` | `REQ-00002-1` | `CL_PlantumlLsp`<br>`CL_Server`<br>`CL_Symbols` | `plantuml_lsp.actions`<br>`plantuml_lsp.completion`<br>`plantuml_lsp.definitions`<br>`plantuml_lsp.diagnostics`<br>`plantuml_lsp.hover`<br>`plantuml_lsp.index`<br>`plantuml_lsp.links`<br>`plantuml_lsp.lints`<br>`plantuml_lsp.parsing`<br>`plantuml_lsp.rename`<br>`plantuml_lsp.server`<br>`plantuml_lsp.symbols`<br>`plantuml_lsp.workspace` | 2 | ? | `VER-00002-1` |
| `SREQ-00004-1` | `REQ-00003-1` | `CL_Definitions`<br>`CL_PlantumlLsp`<br>`CL_Server` | `plantuml_lsp.actions`<br>`plantuml_lsp.completion`<br>`plantuml_lsp.definitions`<br>`plantuml_lsp.diagnostics`<br>`plantuml_lsp.hover`<br>`plantuml_lsp.index`<br>`plantuml_lsp.links`<br>`plantuml_lsp.lints`<br>`plantuml_lsp.parsing`<br>`plantuml_lsp.rename`<br>`plantuml_lsp.server`<br>`plantuml_lsp.symbols`<br>`plantuml_lsp.workspace` | 3 | ? | `VER-00003-1` |
| `SREQ-00005-1` | `REQ-00004-1` | `CL_PlantumlLsp`<br>`CL_Server` | `plantuml_lsp.actions`<br>`plantuml_lsp.completion`<br>`plantuml_lsp.definitions`<br>`plantuml_lsp.diagnostics`<br>`plantuml_lsp.hover`<br>`plantuml_lsp.index`<br>`plantuml_lsp.links`<br>`plantuml_lsp.lints`<br>`plantuml_lsp.parsing`<br>`plantuml_lsp.rename`<br>`plantuml_lsp.server`<br>`plantuml_lsp.symbols`<br>`plantuml_lsp.workspace` | 1 | ? | `VER-00004-1` |
| `SREQ-00006-1` | `REQ-00005-1`<br>`REQ-00006-1`<br>`REQ-00007-1` | `CL_Completion`<br>`CL_Entity`<br>`CL_Hover`<br>`CL_Index`<br>`CL_IndexModule`<br>`CL_Links`<br>`CL_Lints`<br>`CL_PlantumlLsp`<br>`CL_Rename` | `Entity`<br>`Index`<br>`plantuml_lsp.actions`<br>`plantuml_lsp.completion`<br>`plantuml_lsp.definitions`<br>`plantuml_lsp.diagnostics`<br>`plantuml_lsp.hover`<br>`plantuml_lsp.index`<br>`plantuml_lsp.links`<br>`plantuml_lsp.lints`<br>`plantuml_lsp.parsing`<br>`plantuml_lsp.rename`<br>`plantuml_lsp.server`<br>`plantuml_lsp.symbols`<br>`plantuml_lsp.workspace` | 14 | ? | `VER-00005-1`<br>`VER-00006-2`<br>`VER-00007-1` |
| `SREQ-00007-1` | `REQ-00008-1`<br>`REQ-00009-1`<br>`REQ-00010-1`<br>`REQ-00011-2`<br>`REQ-00012-2`<br>`REQ-00013-2`<br>`REQ-00014-1` | `CL_Actions`<br>`CL_Completion`<br>`CL_Definitions`<br>`CL_Index`<br>`CL_Lints`<br>`CL_PlantumlLsp`<br>`CL_Workspace` | `Index`<br>`WorkspaceIndex`<br>`plantuml_lsp.actions`<br>`plantuml_lsp.completion`<br>`plantuml_lsp.definitions`<br>`plantuml_lsp.diagnostics`<br>`plantuml_lsp.hover`<br>`plantuml_lsp.index`<br>`plantuml_lsp.links`<br>`plantuml_lsp.lints`<br>`plantuml_lsp.parsing`<br>`plantuml_lsp.rename`<br>`plantuml_lsp.server`<br>`plantuml_lsp.symbols`<br>`plantuml_lsp.workspace` | 21 | ? | `VER-00008-1`<br>`VER-00009-1`<br>`VER-00010-1`<br>`VER-00011-1`<br>`VER-00012-1`<br>`VER-00013-1`<br>`VER-00014-1` |
<!-- /folio -->
