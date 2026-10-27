"""Document symbols."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_symbols import document_symbol
from tests.fakes import doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (document_symbol,)


class TestDocumentSymbol:
    def test_answers_symbol_information(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        symbols = document_symbol(
            ls, types.DocumentSymbolParams(text_document=doc_id(uris["c.puml"]))
        )
        assert {s.name for s in symbols} == {"Cafetera", "Taza"}
