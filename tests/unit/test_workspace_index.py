"""Unit tests of WorkspaceIndex: the index over an empty root, with no
language server and no other file involved."""

from pathlib import Path

from plantuml_lsp.workspace import WorkspaceIndex

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
