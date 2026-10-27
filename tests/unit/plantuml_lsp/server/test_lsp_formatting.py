"""Formatting."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_formatting import formatting
from tests.fakes import doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (formatting,)

OPTIONS = types.FormattingOptions(tab_size=2, insert_spaces=True)


class TestFormatting:
    def test_an_already_formatted_document_needs_no_edit(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path, {"f.puml": "@startuml\nclass A\n@enduml\n"})
        assert (
            formatting(
                ls,
                types.DocumentFormattingParams(
                    text_document=doc_id(uris["f.puml"]), options=OPTIONS
                ),
            )
            == []
        )
