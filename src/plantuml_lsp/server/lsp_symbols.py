"""Document symbols."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.server.core import SYMBOL_KINDS, server
from plantuml_lsp.symbols import collect_symbols


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: LanguageServer, params: types.DocumentSymbolParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return [
        types.SymbolInformation(
            name=name,
            kind=SYMBOL_KINDS.get(kind, types.SymbolKind.Object),
            location=types.Location(
                uri=params.text_document.uri,
                range=types.Range(
                    start=types.Position(line=sr, character=sc),
                    end=types.Position(line=er, character=ec),
                ),
            ),
        )
        for name, kind, sr, sc, er, ec in collect_symbols(doc.source.encode())
    ]
