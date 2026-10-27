"""Formatting through plantuml-fmt, as one full-document edit."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_fmt.formatter import format_text

from plantuml_lsp.server.core import server


@server.feature(types.TEXT_DOCUMENT_FORMATTING)
def formatting(ls: LanguageServer, params: types.DocumentFormattingParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    formatted = format_text(doc.source)
    if formatted == doc.source:
        return []
    lines = doc.source.splitlines(keepends=True)
    return [
        types.TextEdit(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=len(lines), character=0),
            ),
            new_text=formatted,
        )
    ]
