"""References and rename."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_references import references, rename
from tests.fakes import at, doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (references, rename)


class TestReferencesAndRename:
    def test_an_unknown_name_has_neither(self, tmp_path) -> None:
        ls, uris = _ls(
            tmp_path,
            {"c.puml": CLASSES, "u.puml": "@startuml\nGhost --> Taza\n@enduml\n"},
        )
        pos = at(1, 1)
        ctx = types.ReferenceContext(include_declaration=True)
        assert (
            references(
                ls,
                types.ReferenceParams(
                    text_document=doc_id(uris["u.puml"]), position=pos, context=ctx
                ),
            )
            is None
        )
        assert (
            rename(
                ls,
                types.RenameParams(
                    text_document=doc_id(uris["u.puml"]), position=pos, new_name="X"
                ),
            )
            is None
        )

    def test_rename_rewrites_every_occurrence(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        edit = rename(
            ls,
            types.RenameParams(
                text_document=doc_id(uris["c.puml"]), position=at(4, 7), new_name="Vaso"
            ),
        )
        assert {e.new_text for e in edit.changes[uris["c.puml"]]} == {"Vaso"}
