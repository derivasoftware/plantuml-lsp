"""Go to definition: an include directive, a call label or action, an entity."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.correlation import action_at, call_at, resolve_call
from plantuml_lsp.definitions import entity_definitions, resolve_definition
from plantuml_lsp.index import identifier_at
from plantuml_lsp.server.core import index_of, range_of, server, workspace_of


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(ls: LanguageServer, params: types.DefinitionParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    lines = doc.source.splitlines()
    row = params.position.line
    if row >= len(lines):
        return None
    resolved = resolve_definition(doc.path, lines[row])
    if resolved is not None:
        path, line = resolved
        return types.Location(
            uri=f"file://{path}",
            range=types.Range(
                start=types.Position(line=line, character=0),
                end=types.Position(line=line, character=0),
            ),
        )
    # not an include directive: a call label resolves to the method
    doc2, index = index_of(ls, params.text_document.uri)
    src2 = doc2.source.encode()
    call = call_at(src2, params.position.line, params.position.character) or action_at(
        index, params.position.line
    )
    if call is not None:
        tier, entity, loc = resolve_call(
            call[0], call[1], index, workspace_of(ls, doc2)
        )
        if tier in ("declared", "homonym") and loc is not None:
            mrow, mscol, mecol, _text = loc
            return types.Location(
                uri=f"file://{entity.path}",
                range=range_of(mrow, mscol, mrow, mecol),
            )
    name = identifier_at(src2, params.position.line, params.position.character)
    if not name:
        return None
    locations = [
        types.Location(uri=f"file://{path}", range=range_of(r, sc, r, ec))
        for path, r, sc, ec in entity_definitions(name, index, workspace_of(ls, doc2))
    ]
    if not locations:
        return None
    return locations[0] if len(locations) == 1 else locations
