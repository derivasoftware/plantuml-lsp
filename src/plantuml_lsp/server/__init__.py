"""The language server: the core and one module per LSP request. Importing
the package registers every handler on the core's instance."""

from plantuml_lsp.server import (  # noqa: F401  (each registers its handlers)
    lsp_code_actions,
    lsp_completion,
    lsp_definition,
    lsp_diagnostics,
    lsp_formatting,
    lsp_hover,
    lsp_links,
    lsp_references,
    lsp_symbols,
    lsp_workspace_symbols,
)
from plantuml_lsp.server.core import main, server

__all__ = ["main", "server"]
