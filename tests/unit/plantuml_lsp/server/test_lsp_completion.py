"""Completion."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_completion import completion
from tests.fakes import at, doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (completion,)


class TestCompletion:
    def test_free_label_text_answers_nothing(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path, {"s.puml": "@startuml\nA -> B : hola que\n@enduml\n"})
        assert (
            completion(
                ls,
                types.CompletionParams(
                    text_document=doc_id(uris["s.puml"]), position=at(1, 17)
                ),
            )
            is None
        )
