"""The server core: one pygls instance, the helpers every handler shares,
and the entry point. The handlers live one module per LSP request and
register themselves on this instance (BOK-00321-2: the core is a unit of
its own; each handler belongs to the feature it serves)."""

from __future__ import annotations

import os

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

SYMBOL_KINDS = {
    "class": types.SymbolKind.Class,
    "interface": types.SymbolKind.Interface,
    "enum": types.SymbolKind.Enum,
    "namespace": types.SymbolKind.Namespace,
    "package": types.SymbolKind.Package,
    "participant": types.SymbolKind.Object,
}

server = LanguageServer("plantuml-lsp", "0.3.0")

SEVERITIES = {
    "error": types.DiagnosticSeverity.Error,
    "warning": types.DiagnosticSeverity.Warning,
    "information": types.DiagnosticSeverity.Information,
}


def range_of(sr: int, sc: int, er: int, ec: int) -> types.Range:
    return types.Range(
        start=types.Position(line=sr, character=sc),
        end=types.Position(line=er, character=ec),
    )


def index_of(ls: LanguageServer, uri: str):
    doc = ls.workspace.get_text_document(uri)
    return doc, build_index(doc.path, doc.source.encode())


workspaces: dict[str, WorkspaceIndex] = {}


def workspace_of(ls: LanguageServer, doc) -> WorkspaceIndex:
    root = getattr(ls.workspace, "root_path", None) or os.path.dirname(doc.path)
    ws = workspaces.get(root)
    if ws is None:
        ws = workspaces[root] = WorkspaceIndex(root)
    else:
        ws.refresh_if_stale()
    return ws


def merged_occurrences(name: str, index, ws: WorkspaceIndex):
    seen = set()
    merged = []
    for occ in index.occurrences(name) + ws.occurrences(name):
        if occ not in seen:
            seen.add(occ)
            merged.append(occ)
    return merged


def main() -> None:
    server.start_io()
