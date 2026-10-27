"""Completion by cursor context."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.completion import contextual_completions
from plantuml_lsp.server.core import index_of, server, workspace_of


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=[":", ">", " ", "|"]),
)
def completion(ls: LanguageServer, params: types.CompletionParams):
    doc, index = index_of(ls, params.text_document.uri)
    kind_map = {
        "keyword": types.CompletionItemKind.Keyword,
        "interface": types.CompletionItemKind.Interface,
        "enum": types.CompletionItemKind.Enum,
        "method": types.CompletionItemKind.Method,
    }
    items = contextual_completions(
        doc.source.encode(),
        params.position.line,
        params.position.character,
        index,
        workspace_of(ls, doc),
    )
    if not items:
        return None
    return [
        types.CompletionItem(
            label=label,
            kind=kind_map.get(kind, types.CompletionItemKind.Class),
            detail=detail or kind,
        )
        for label, kind, detail in items
    ]
