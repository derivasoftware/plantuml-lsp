"""Quick fixes: declare an endpoint, correct an include path, declare a method."""

from pathlib import Path

from plantuml_lsp.actions import declare_entity, declare_method, fix_include_path
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (declare_entity, fix_include_path, declare_method)


class TestDeclareEntity:
    def test_inserts_the_declaration_before_enduml(self) -> None:
        title, path, row, scol, ecol, text = declare_entity(
            "Ghost", "d.puml", b"@startuml\nA --> Ghost\n@enduml\n"
        )
        assert (path, row, scol, ecol, text) == ("d.puml", 2, 0, 0, "class Ghost\n")
        assert "Ghost" in title

    def test_without_enduml_there_is_nothing_to_do(self) -> None:
        assert declare_entity("Ghost", "d.puml", b"@startuml\n") is None


class TestFixIncludePath:
    def test_points_a_broken_path_at_the_closest_file(self, tmp_path: Path) -> None:
        (tmp_path / "lib").mkdir()
        (tmp_path / "lib" / "shapes.iuml").write_text("@startuml\nclass S\n@enduml\n")
        doc = tmp_path / "main.puml"
        doc.write_text("@startuml\n!include shape.iuml\n@enduml\n")
        ws = WorkspaceIndex(str(tmp_path))
        ws.refresh()
        fix = fix_include_path(1, "!include shape.iuml", str(doc), ws)
        assert fix is not None and fix[5] == "./lib/shapes.iuml"

    def test_a_line_that_is_no_include_is_left_alone(self, tmp_path: Path) -> None:
        ws = WorkspaceIndex(str(tmp_path))
        assert fix_include_path(0, "class A", str(tmp_path / "d.puml"), ws) is None


class TestDeclareMethod:
    def test_adds_the_skeleton_before_the_closing_brace(self, tmp_path: Path) -> None:
        (tmp_path / "c.puml").write_text(
            "@startuml\nclass Cafetera {\n    +encender() : None\n}\n@enduml\n"
        )
        ws = WorkspaceIndex(str(tmp_path))
        ws.refresh()
        entity = ws.class_card("Cafetera")
        title, path, row, _s, _e, text = declare_method("preparar", entity, ws)
        assert (row, text) == (3, "    +preparar() : None\n")
        assert "Cafetera" in title
