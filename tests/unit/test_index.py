"""The symbol index: entities across the document and its include closure."""

from pathlib import Path

from plantuml_lsp.index import build_index

MAIN = """@startuml
!includesub lib.iuml!Base
class Widget {
  +draw() : None
}
class "Fancy Name" as FN
Widget --> FN : uses
Widget --> Ghost
@enduml
"""

LIB = """@startuml
!startsub Base
interface Drawable
!endsub
@enduml
"""


def make_workspace(tmp_path: Path) -> Path:
    (tmp_path / "main.puml").write_text(MAIN)
    (tmp_path / "lib.iuml").write_text(LIB)
    return tmp_path / "main.puml"


def test_occurrences_match_qualified_tails(tmp_path):
    doc = tmp_path / "agg.puml"
    src = b"@startuml\nclass Widget\nmaquina.Widget --> Otro\n@enduml\n"
    doc.write_bytes(src)
    index = build_index(str(doc), src)
    occs = index.occurrences("Widget")
    assert len(occs) == 2
    # the qualified use reports the tail span only
    _p, row, scol, ecol = occs[1]
    assert (row, ecol - scol) == (2, len("Widget"))
    assert scol == len("maquina.")


def test_resolve_entity_falls_back_to_the_tail():
    from plantuml_lsp.index import resolve_entity

    entities = {"Widget": object()}
    assert resolve_entity("Widget", entities) == "Widget"
    assert resolve_entity("maquina.Widget", entities) == "Widget"
    assert resolve_entity("otra.Cosa", entities) is None
