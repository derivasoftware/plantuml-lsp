"""Hover."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_hover import hover
from tests.fakes import at, doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (hover,)


class TestHover:
    def test_nothing_under_the_cursor_is_none(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        assert (
            hover(
                ls,
                types.HoverParams(
                    text_document=doc_id(uris["c.puml"]), position=at(0, 0)
                ),
            )
            is None
        )
