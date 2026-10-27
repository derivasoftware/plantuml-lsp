"""Sequence participants against the workspace's classes."""

from pathlib import Path

from plantuml_lsp.correlation.participants import unmatched_participants
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (unmatched_participants,)


class TestUnmatchedParticipants:
    def test_only_class_cased_plain_participants_no_class_explains(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "c.puml").write_text("@startuml\nclass Cafetera\n@enduml\n")
        seq = tmp_path / "s.puml"
        seq.write_text(
            "@startuml\nparticipant Cafetera\nparticipant Molinillo\nparticipant cli\nactor Barista\n@enduml\n"
        )
        ws = WorkspaceIndex(str(tmp_path))
        ws.refresh()
        assert {e.id for e in unmatched_participants(ws, str(seq))} == {"Molinillo"}

    def test_a_document_the_workspace_never_indexed_has_none(
        self, tmp_path: Path
    ) -> None:
        ws = WorkspaceIndex(str(tmp_path))
        assert unmatched_participants(ws, str(tmp_path / "nope.puml")) == []
