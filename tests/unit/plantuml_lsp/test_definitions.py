"""Go to definition: includes and their sub-blocks, and entities across the workspace."""

from pathlib import Path

from plantuml_lsp.definitions import entity_definitions, resolve_definition
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (entity_definitions, resolve_definition)

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\n@enduml\n"
SEQ = "@startuml\nparticipant Cafetera\nCafetera -> Cafetera : preparar(leche)\nCafetera -> Cafetera : moler()\n@enduml\n"


def _setup(tmp_path: Path):
    (tmp_path / "c.puml").write_text(CLASSES)
    doc = tmp_path / "s.puml"
    doc.write_text(SEQ)
    ws = WorkspaceIndex(str(tmp_path))
    ws.refresh()
    return build_index(str(doc), SEQ.encode()), ws


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
