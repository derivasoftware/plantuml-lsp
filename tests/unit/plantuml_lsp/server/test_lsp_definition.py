"""Go to definition."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_definition import definition
from tests.fakes import at, doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (definition,)


class TestDefinition:
    def test_an_entity_resolves_to_its_declaration(self, tmp_path) -> None:
        ls, uris = _ls(
            tmp_path,
            {"c.puml": CLASSES, "u.puml": "@startuml\nTaza --> Cafetera\n@enduml\n"},
        )
        loc = definition(
            ls,
            types.DefinitionParams(
                text_document=doc_id(uris["u.puml"]), position=at(1, 1)
            ),
        )
        assert loc.uri.endswith("c.puml")

    def test_a_row_past_the_end_is_none(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        assert (
            definition(
                ls,
                types.DefinitionParams(
                    text_document=doc_id(uris["c.puml"]), position=at(99, 0)
                ),
            )
            is None
        )
