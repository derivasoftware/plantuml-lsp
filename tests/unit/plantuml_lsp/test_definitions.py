"""Go to definition: includes and their sub-blocks, entities, calls and actions."""

from pathlib import Path

from plantuml_lsp.definitions import (
    action_at,
    call_at,
    entity_definitions,
    resolve_call,
    resolve_definition,
)
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (call_at, action_at, resolve_call, entity_definitions, resolve_definition)

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\n@enduml\n"
SEQ = "@startuml\nparticipant Cafetera\nCafetera -> Cafetera : preparar(leche)\nCafetera -> Cafetera : moler()\n@enduml\n"


def _setup(tmp_path: Path):
    (tmp_path / "c.puml").write_text(CLASSES)
    doc = tmp_path / "s.puml"
    doc.write_text(SEQ)
    ws = WorkspaceIndex(str(tmp_path))
    ws.refresh()
    return build_index(str(doc), SEQ.encode()), ws


class TestCallAt:
    def test_reads_receiver_and_method_on_a_call_shaped_label(self) -> None:
        assert call_at(SEQ.encode(), 2, len("Cafetera -> Cafetera : pre")) == (
            "Cafetera",
            "preparar",
        )

    def test_is_none_off_a_label(self) -> None:
        assert call_at(SEQ.encode(), 1, 3) is None


class TestActionAt:
    def test_reads_lane_and_method_on_the_row_of_an_action(
        self, tmp_path: Path
    ) -> None:
        src = "@startuml\n|Cafetera|\n:preparar(pedido);\n@enduml\n"
        doc = tmp_path / "a.puml"
        doc.write_text(src)
        index = build_index(str(doc), src.encode())
        assert action_at(index, 2) == ("Cafetera", "preparar")
        assert action_at(index, 1) is None


class TestResolveCall:
    def test_declared_drift_and_unknown(self, tmp_path: Path) -> None:
        index, ws = _setup(tmp_path)
        assert resolve_call("Cafetera", "preparar", index, ws)[0] == "declared"
        assert resolve_call("Cafetera", "moler", index, ws)[0] == "drift"
        assert resolve_call("Nadie", "volar", index, ws)[0] == "unknown"


class TestEntityDefinitions:
    def test_the_closure_first_then_the_workspace(self, tmp_path: Path) -> None:
        index, ws = _setup(tmp_path)
        paths = [p for p, *_ in entity_definitions("Cafetera", index, ws)]
        assert paths[0] == str((tmp_path / "s.puml").resolve()) or paths[0].endswith(
            "s.puml"
        )
        assert any(p.endswith("c.puml") for p in paths)

    def test_a_qualified_name_resolves_by_its_tail(self, tmp_path: Path) -> None:
        index, ws = _setup(tmp_path)
        assert any(
            p.endswith("c.puml")
            for p, *_ in entity_definitions("maquina.Cafetera", index, ws)
        )


class TestResolveDefinition:
    def test_an_includesub_lands_on_its_startsub(self, tmp_path: Path) -> None:
        (tmp_path / "lib.iuml").write_text(
            "@startuml\n!startsub Base\nclass B\n!endsub\n@enduml\n"
        )
        target = resolve_definition(
            str(tmp_path / "m.puml"), "!includesub lib.iuml!Base"
        )
        assert target == (str((tmp_path / "lib.iuml").resolve()), 1)

    def test_an_include_lands_on_the_file(self, tmp_path: Path) -> None:
        (tmp_path / "lib.iuml").write_text("@startuml\n@enduml\n")
        assert resolve_definition(str(tmp_path / "m.puml"), "!include lib.iuml") == (
            str((tmp_path / "lib.iuml").resolve()),
            0,
        )

    def test_a_missing_target_or_another_line_is_none(self, tmp_path: Path) -> None:
        assert (
            resolve_definition(str(tmp_path / "m.puml"), "!include nope.iuml") is None
        )
        assert resolve_definition(str(tmp_path / "m.puml"), "class A") is None
