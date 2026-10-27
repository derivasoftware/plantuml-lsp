"""References and rename across the closure and the workspace."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.index import identifier_at, resolve_entity
from plantuml_lsp.rename import edits_from
from plantuml_lsp.server.core import (
    index_of,
    merged_occurrences,
    range_of,
    server,
    workspace_of,
)


def _entity_reference_locations(name: str, index, ws) -> list:
    """Occurrence locations of an entity across the closure and workspace."""
    if name not in index.entities and not ws.declarations(name):
        return []
    return [
        types.Location(uri=f"file://{path}", range=range_of(row, scol, row, ecol))
        for path, row, scol, ecol in merged_occurrences(name, index, ws)
    ]


def _method_reference_locations(name: str, index, ws, results: list) -> None:
    """Extend results with a method's declarations and call sites."""
    is_method = any(
        name in e.methods for e in index.entities.values()
    ) or ws.method_declarations(name)
    if not is_method:
        return
    seen = {
        (loc.uri, loc.range.start.line, loc.range.start.character) for loc in results
    }

    def add(uri: str, row: int, scol: int, ecol: int) -> None:
        key = (uri, row, scol)
        if key not in seen:
            seen.add(key)
            results.append(
                types.Location(uri=uri, range=range_of(row, scol, row, ecol))
            )

    for entity in ws.method_declarations(name):
        row, scol, ecol, _txt = entity.methods[name]
        add(f"file://{entity.path}", row, scol, ecol)
    for path, row, scol, ecol in ws.call_sites(name):
        add(f"file://{path}", row, scol, ecol)


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def references(ls: LanguageServer, params: types.ReferenceParams):
    doc, index = index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    ws = workspace_of(ls, doc)
    name = name and (resolve_entity(name, index.entities) or name)
    if not name:
        return None
    results = _entity_reference_locations(name, index, ws)
    # a method name: add its call sites (sequence labels and activity
    # actions) and its declarations across the workspace
    _method_reference_locations(name, index, ws, results)
    return results or None


@server.feature(types.TEXT_DOCUMENT_RENAME)
def rename(ls: LanguageServer, params: types.RenameParams):
    doc, index = index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    ws = workspace_of(ls, doc)
    name = name and (resolve_entity(name, index.entities) or name)
    if not name or (name not in index.entities and not ws.declarations(name)):
        return None

    def read(path: str) -> bytes | None:
        return index.files.get(path) or ws.file_bytes(path)

    changes: dict[str, list[types.TextEdit]] = {}
    for path, row, scol, ecol, new_text in edits_from(
        merged_occurrences(name, index, ws), params.new_name, read
    ):
        changes.setdefault(f"file://{path}", []).append(
            types.TextEdit(range=range_of(row, scol, row, ecol), new_text=new_text)
        )
    return types.WorkspaceEdit(changes=changes)
