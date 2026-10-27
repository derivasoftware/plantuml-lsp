"""Unit tests of WorkspaceIndex: the index over an empty root, with no
language server and no other file involved."""

from pathlib import Path

from plantuml_lsp.workspace.WorkspaceIndex import WorkspaceIndex

__covers__ = (WorkspaceIndex,)

__covers__ = (WorkspaceIndex,)


def test_an_empty_root_indexes_nothing(tmp_path: Path) -> None:
    index = WorkspaceIndex(str(tmp_path))
    assert index.entities() == []
    assert index.symbols("") == []
    assert index.occurrences("Anything") == []
    assert index.class_card("Anything") is None


def test_a_refresh_over_an_unchanged_tree_keeps_the_index(tmp_path: Path) -> None:
    (tmp_path / "a.puml").write_text("@startuml\nclass Widget\n@enduml\n")
    index = WorkspaceIndex(str(tmp_path))
    before = [e.name for e in index.entities()]
    index.refresh()
    assert [e.name for e in index.entities()] == before == ["Widget"]


def test_a_box_card_finds_the_box_a_name_denotes(tmp_path: Path) -> None:
    (tmp_path / "HLD.puml").write_text(
        "@startuml\nnamespace argos.cli <<package>> {\n}\nclass Widget\n@enduml\n"
    )
    ws = WorkspaceIndex(str(tmp_path))
    assert ws.box_card("argos.cli").kind == "package"
    assert ws.box_card("Widget") is None
