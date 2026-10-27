"""Activity actions against the class their swimlane names."""

from pathlib import Path

from plantuml_lsp.correlation.activities import action_at, action_call_lints
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (action_at, action_call_lints)

ACT = "@startuml\n|Cafetera|\n:preparar(pedido);\n:volar();\n@enduml\n"


def _setup(tmp_path: Path):
    (tmp_path / "c.puml").write_text(
        "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\n@enduml\n"
    )
    doc = tmp_path / "a.puml"
    doc.write_text(ACT)
    ws = WorkspaceIndex(str(tmp_path))
    ws.refresh()
    return build_index(str(doc), ACT.encode()), ws


class TestActionAt:
    def test_reads_lane_and_method_on_the_row_of_an_action(
        self, tmp_path: Path
    ) -> None:
        index, _ws = _setup(tmp_path)
        assert action_at(index, 2) == ("Cafetera", "preparar")
        assert action_at(index, 1) is None


class TestActionCallLints:
    def test_an_action_the_lanes_class_does_not_declare_drifts(
        self, tmp_path: Path
    ) -> None:
        index, ws = _setup(tmp_path)
        messages = [lint[4] for lint in action_call_lints(index, ws)]
        assert any("volar" in m for m in messages) and not any(
            "preparar" in m for m in messages
        )
