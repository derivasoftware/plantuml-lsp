"""Document links."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_links import document_link
from tests.fakes import doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (document_link,)


class TestDocumentLink:
    def test_a_document_without_includes_has_none(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        assert (
            document_link(
                ls, types.DocumentLinkParams(text_document=doc_id(uris["c.puml"]))
            )
            == []
        )
