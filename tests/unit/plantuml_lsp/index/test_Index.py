"""The closure index: declarations, relations, call sites and actions,
built across the document and its transitive include closure."""

from pathlib import Path

from plantuml_lsp.index.Index import Index, build_index, walk_tree
from plantuml_lsp.parsing import parse

__covers__ = (Index, build_index, walk_tree)

MAIN = """@startuml
!includesub lib.iuml!Base
class Widget {
  +draw() : None
}
class "Fancy Name" as FN
Widget --> FN : draw()
@enduml
"""

LIB = """@startuml
!startsub Base
interface Drawable
!endsub
@enduml
"""


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "main.puml").write_text(MAIN)
    (tmp_path / "lib.iuml").write_text(LIB)
    return tmp_path / "main.puml"


class TestBuildIndex:
    def test_indexes_the_document_and_its_include_closure(self, tmp_path) -> None:
        doc = _workspace(tmp_path)
        index = build_index(str(doc), doc.read_bytes())
        assert {"Widget", "FN", "Drawable"} <= set(index.entities)
        assert len(index.files) == 2

    def test_an_alias_is_the_id_and_the_name_is_kept(self, tmp_path) -> None:
        doc = _workspace(tmp_path)
        entity = build_index(str(doc), doc.read_bytes()).entities["FN"]
        assert entity.name == "Fancy Name"

    def test_a_second_declaration_is_kept_as_a_duplicate(self, tmp_path) -> None:
        doc = tmp_path / "d.puml"
        src = b"@startuml\nclass A\nclass A\n@enduml\n"
        doc.write_bytes(src)
        index = build_index(str(doc), src)
        assert len(index.duplicates) == 1

    def test_an_include_cycle_terminates(self, tmp_path) -> None:
        (tmp_path / "a.puml").write_text(
            "@startuml\n!include b.puml\nclass A\n@enduml\n"
        )
        (tmp_path / "b.puml").write_text(
            "@startuml\n!include a.puml\nclass B\n@enduml\n"
        )
        doc = tmp_path / "a.puml"
        assert {"A", "B"} <= set(build_index(str(doc), doc.read_bytes()).entities)


class TestWalkTree:
    def test_records_relations_and_the_call_in_a_label(self) -> None:
        src = MAIN.encode()
        index = Index(doc_path="m.puml")
        walk_tree(parse(src).root_node, src, "m.puml", index)
        assert index.relations["Widget"]
        assert "draw" in index.calls

    def test_records_activity_actions_with_their_swimlane(self) -> None:
        src = b"@startuml\n|Cocina|\n:preparar(pedido);\n@enduml\n"
        index = Index(doc_path="a.puml")
        walk_tree(parse(src).root_node, src, "a.puml", index)
        assert [(name, lane) for name, lane, *_ in index.actions] == [
            ("preparar", "Cocina")
        ]


class TestOccurrences:
    def test_qualified_uses_report_the_tail_span(self, tmp_path) -> None:
        doc = tmp_path / "agg.puml"
        src = b"@startuml\nclass Widget\nmaquina.Widget --> Otro\n@enduml\n"
        doc.write_bytes(src)
        occs = build_index(str(doc), src).occurrences("Widget")
        assert len(occs) == 2
        _p, row, scol, ecol = occs[1]
        assert (row, ecol - scol, scol) == (2, len("Widget"), len("maquina."))
