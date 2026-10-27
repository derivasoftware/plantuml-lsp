"""Hover: the entity's card, enriched with the workspace class a participant names."""

from pathlib import Path

from plantuml_lsp.hover import hover_for
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (hover_for,)


def _index(tmp_path: Path, name: str, text: str):
    doc = tmp_path / name
    doc.write_text(text)
    return build_index(str(doc), text.encode())


class TestHoverFor:
    def test_shows_kind_members_and_relations(self, tmp_path: Path) -> None:
        index = _index(
            tmp_path,
            "c.puml",
            "@startuml\nclass Widget {\n  +draw() : None\n}\nWidget --> B\n@enduml\n",
        )
        text = hover_for("Widget", index)
        assert (
            "**class** `Widget`" in text
            and "+draw() : None" in text
            and "Widget --> B" in text
        )

    def test_an_unknown_name_without_a_workspace_is_none(self, tmp_path: Path) -> None:
        assert (
            hover_for("Ghost", _index(tmp_path, "d.puml", "@startuml\n@enduml\n"))
            is None
        )

    def test_a_participant_shows_the_card_of_its_workspace_class(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "c.puml").write_text(
            "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\n@enduml\n"
        )
        index = _index(
            tmp_path,
            "s.puml",
            "@startuml\nparticipant Cafetera\nCafetera -> Cafetera : preparar()\n@enduml\n",
        )
        ws = WorkspaceIndex(str(tmp_path))
        ws.refresh()
        assert "+preparar() : Taza" in hover_for("Cafetera", index, ws)
