"""Semantic lints: unknown endpoints, duplicates, broken includes, drifting calls."""

from pathlib import Path

from plantuml_lsp.index import build_index
from plantuml_lsp.lints import collect_call_lints, collect_lints
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (collect_lints, collect_call_lints)


def _lints(tmp_path: Path, text: str):
    doc = tmp_path / "d.puml"
    doc.write_text(text)
    return collect_lints(str(doc), text.encode(), build_index(str(doc), text.encode()))


def _messages(lints) -> str:
    return "\n".join(lint[4] for lint in lints)


class TestCollectLints:
    def test_an_endpoint_nothing_declares_in_a_class_diagram(
        self, tmp_path: Path
    ) -> None:
        assert "Ghost" in _messages(
            _lints(tmp_path, "@startuml\nclass A\nA --> Ghost\n@enduml\n")
        )

    def test_a_sequence_diagram_has_no_unknown_endpoint_lint(
        self, tmp_path: Path
    ) -> None:
        assert "Ghost" not in _messages(
            _lints(tmp_path, "@startuml\nparticipant A\nA -> Ghost : hi\n@enduml\n")
        )

    def test_a_duplicate_declaration(self, tmp_path: Path) -> None:
        assert _lints(tmp_path, "@startuml\nclass A\nclass A\n@enduml\n")

    def test_a_broken_include(self, tmp_path: Path) -> None:
        assert "nope.iuml" in _messages(
            _lints(tmp_path, "@startuml\n!include nope.iuml\n@enduml\n")
        )


class TestCollectCallLints:
    def test_a_call_the_receivers_class_does_not_declare_drifts(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "c.puml").write_text(
            "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\n@enduml\n"
        )
        seq = "@startuml\nparticipant Cafetera\nCafetera -> Cafetera : moler()\nCafetera -> Cafetera : preparar()\n@enduml\n"
        doc = tmp_path / "s.puml"
        doc.write_text(seq)
        ws = WorkspaceIndex(str(tmp_path))
        ws.refresh()
        lints = collect_call_lints(
            seq.encode(), build_index(str(doc), seq.encode()), ws
        )
        assert "moler" in _messages(lints) and "preparar" not in _messages(lints)
