"""Workspace symbols: every indexed entity of every open workspace."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.server.core import SYMBOL_KINDS, range_of, server, workspaces


@server.feature(types.WORKSPACE_SYMBOL)
def workspace_symbol(ls: LanguageServer, params: types.WorkspaceSymbolParams):
    if not workspaces:
        return None
    hits = []
    for ws in workspaces.values():
        ws.refresh_if_stale()
        hits.extend(ws.symbols(params.query))
    return [
        types.SymbolInformation(
            name=e.id,
            kind=SYMBOL_KINDS.get(e.kind, types.SymbolKind.Object),
            container_name=e.kind,
            location=types.Location(
                uri=f"file://{e.path}",
                range=range_of(e.row, e.scol, e.row, e.ecol),
            ),
        )
        for e in hits[:200]
    ]
