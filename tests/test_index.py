"""The symbol index: entities across the document and its include closure."""

from pathlib import Path

from plantuml_lsp.index import build_index, identifier_at

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


def test_index_collects_document_and_closure_entities(tmp_path):
    doc = make_workspace(tmp_path)
    index = build_index(str(doc), MAIN.encode())
    assert index.entities["Widget"].kind == "class"
    assert index.entities["Widget"].members == ["+draw() : None"]
    assert index.entities["FN"].name == "Fancy Name"
    assert index.entities["Drawable"].kind == "interface"
    assert index.entities["Drawable"].path.endswith("lib.iuml")
    assert "Ghost" not in index.entities


def test_participants_index_by_alias(tmp_path):
    doc = tmp_path / "seq.puml"
    src = b'@startuml\nparticipant "Front End" as FE\nactor User\nUser -> FE\n@enduml\n'
    doc.write_bytes(src)
    index = build_index(str(doc), src)
    assert index.entities["FE"].kind == "participant"
    assert index.entities["FE"].name == "Front End"
    assert index.entities["User"].kind == "actor"


def test_occurrences_span_the_closure(tmp_path):
    doc = make_workspace(tmp_path)
    index = build_index(str(doc), MAIN.encode())
    occs = index.occurrences("Widget")
    rows = [(Path(p).name, row) for p, row, _, _ in occs]
    assert (("main.puml", 2)) in rows  # declaration
    assert (("main.puml", 6)) in rows and (("main.puml", 7)) in rows  # relations


def test_identifier_at_reads_the_token_under_the_cursor():
    src = b"@startuml\nWidget --> FN : uses\n@enduml\n"
    assert identifier_at(src, 1, 2) == "Widget"
    assert identifier_at(src, 1, 12) == "FN"
    assert identifier_at(src, 1, 8) is None  # on the operator
