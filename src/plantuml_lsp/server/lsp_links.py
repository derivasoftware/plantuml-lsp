"""Document links."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.links import collect_links
from plantuml_lsp.server.core import range_of, server


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_LINK)
def document_link(ls: LanguageServer, params: types.DocumentLinkParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return [
        types.DocumentLink(
            range=range_of(row, scol, row, ecol), target=f"file://{target}"
        )
        for row, scol, ecol, target in collect_links(doc.path, doc.source.encode())
    ]
