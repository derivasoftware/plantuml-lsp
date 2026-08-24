"""Quick-fix builders: declaration, include path, method skeleton."""

from pathlib import Path

from plantuml_lsp.actions import declare_entity, declare_method, fix_include_path
from plantuml_lsp.workspace import WorkspaceIndex


def test_declare_entity_inserts_before_enduml(tmp_path):
    doc = tmp_path / "d.puml"
    src = b"@startuml\nclass A\nA --> Ghost\n@enduml\n"
    doc.write_bytes(src)
    fix = declare_entity("Ghost", str(doc), src)
    title, path, row, scol, ecol, text = fix
    assert "Ghost" in title and row == 3 and (scol, ecol) == (0, 0)
    assert text == "class Ghost\n"


def test_fix_include_path_suggests_the_closest_file(tmp_path):
    (tmp_path / "clases").mkdir()
    (tmp_path / "clases" / "CL_Cafetera.puml").write_text("@startuml\n@enduml\n")
    doc = tmp_path / "extra" / "L.puml"
    doc.parent.mkdir()
    doc.write_text("@startuml\n!include ../clases/CL_Cafetera.pml\n@enduml\n")
    ws = WorkspaceIndex(str(tmp_path))
    fix = fix_include_path(1, "!include ../clases/CL_Cafetera.pml", str(doc), ws)
    title, path, row, scol, ecol, text = fix
    assert text.endswith("CL_Cafetera.puml")
    assert scol == len("!include ")


def test_declare_method_inserts_the_skeleton_with_matching_indent(tmp_path):
    cl = tmp_path / "CL_M.puml"
    cl.write_text(
        "@startuml\nnamespace m {\n  class Molinillo {\n"
        "    +moler(gramos: int) : Cafe\n  }\n}\n@enduml\n"
    )
    ws = WorkspaceIndex(str(tmp_path))
    entity = ws.class_card("Molinillo")
    fix = declare_method("afilar", entity, ws)
    title, path, row, scol, ecol, text = fix
    assert "afilar" in title and "Molinillo" in title
    assert path.endswith("CL_M.puml") and row == 4
    assert text == "    +afilar() : None\n"
