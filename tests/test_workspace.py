"""Workspace index: correlation of entities across every diagram of the
workspace — the class that a sequence participant choreographs, and back."""

from pathlib import Path

from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (WorkspaceIndex,)

CL = """@startuml
namespace toolkit {
  class Widget {
    +draw() : None
    -size : int
  }
}
class Helper
@enduml
"""

SEQ = """@startuml
participant Widget
participant "Helper" as H
actor User
User -> Widget : click
Widget -> H : delegate
Widget -> Ghost : lost
@enduml
"""


def make_workspace(tmp_path: Path) -> Path:
    (tmp_path / "design").mkdir()
    (tmp_path / "design" / "CL_Widget.puml").write_text(CL)
    (tmp_path / "design" / "SEQ_Flow.puml").write_text(SEQ)
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignored.puml").write_text("@startuml\nclass Nope\n@enduml\n")
    return tmp_path


def test_scans_the_tree_and_skips_vendored_dirs(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    names = {e.id for e in ws.entities()}
    assert {"Widget", "Helper", "H", "User"} <= names
    assert "Nope" not in names


def test_symbols_query_matches_substrings_case_insensitively(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    hits = ws.symbols("widg")
    assert any(e.id == "Widget" and e.kind == "class" for e in hits)


def test_correlates_a_class_with_its_sequence_participants(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    decls = ws.declarations("Widget")
    kinds = {(e.kind, Path(e.path).name) for e in decls}
    assert ("class", "CL_Widget.puml") in kinds
    assert ("participant", "SEQ_Flow.puml") in kinds


def test_correlates_by_display_name_through_aliases(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    decls = ws.declarations("Helper")
    assert any(e.kind == "participant" and e.id == "H" for e in decls)


def test_occurrences_span_the_workspace(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    files = {Path(p).name for p, _r, _s, _e in ws.occurrences("Widget")}
    assert files == {"CL_Widget.puml", "SEQ_Flow.puml"}


def test_class_card_for_a_participant(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    card = ws.class_card("Widget")
    assert card is not None
    assert card.kind == "class"
    assert "+draw() : None" in card.members
    # a participant-only name has no card
    assert ws.class_card("User") is None


def test_unmatched_participants_reports_only_plain_participants(tmp_path):
    ws = WorkspaceIndex(str(make_workspace(tmp_path)))
    seq = str(tmp_path / "design" / "SEQ_Flow.puml")
    unmatched = {e.id for e in ws.unmatched_participants(seq)}
    assert unmatched == set()  # Ghost is implicit (no declaration), not declared
    # declare a participant with no class anywhere
    (tmp_path / "design" / "SEQ_Flow.puml").write_text(
        SEQ.replace("actor User", "actor User\nparticipant Orphan\nparticipant daemon")
    )
    ws.refresh()
    unmatched = {e.id for e in ws.unmatched_participants(seq)}
    # actor User and lowercase conceptual participants stay exempt
    assert unmatched == {"Orphan"}


def test_refresh_picks_up_edits_and_deletions(tmp_path):
    root = make_workspace(tmp_path)
    ws = WorkspaceIndex(str(root))
    assert ws.declarations("Widget")
    (root / "design" / "CL_Widget.puml").write_text(
        CL.replace("class Widget", "class Gadget")
    )
    ws.refresh()
    assert not any(e.kind == "class" for e in ws.declarations("Widget"))
    assert any(e.kind == "class" for e in ws.declarations("Gadget"))
    (root / "design" / "SEQ_Flow.puml").unlink()
    ws.refresh()
    assert not any(e.kind == "participant" for e in ws.declarations("Widget"))
