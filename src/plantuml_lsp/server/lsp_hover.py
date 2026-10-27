"""Hover: the entity's card, or the declared method a call names."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.correlation import action_at, call_at, resolve_call
from plantuml_lsp.hover import hover_for
from plantuml_lsp.index import identifier_at
from plantuml_lsp.server.core import index_of, server, workspace_of


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams):
    doc, index = index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    text = hover_for(name, index, workspace_of(ls, doc)) if name else None
    if text is None:
        call = call_at(
            doc.source.encode(), params.position.line, params.position.character
        ) or action_at(index, params.position.line)
        if call is not None:
            tier, entity, loc = resolve_call(
                call[0], call[1], index, workspace_of(ls, doc)
            )
            if tier == "declared" and loc is not None:
                _r, _s, _e, member_text = loc
                text = f"**{entity.kind}** `{entity.id}`\n\n```\n{member_text}\n```"
    if text is None:
        return None
    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=text)
    )
