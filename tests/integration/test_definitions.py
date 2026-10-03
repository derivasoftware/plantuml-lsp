"""Definition resolution across !includesub / !include directives."""

from plantuml_lsp.definitions import resolve_definition

LEAF = """@startuml
!startsub Kernel
class Kernel
!endsub
!startsub Aux
class Aux
!endsub
@enduml
"""


def test_includesub_resolves_to_startsub_line(tmp_path):
    (tmp_path / "CL_Kernel.puml").write_text(LEAF)
    agg = tmp_path / "CL_All.puml"
    agg.write_text("@startuml\n!includesub ./CL_Kernel.puml!Aux\n@enduml\n")

    resolved = resolve_definition(str(agg), "!includesub ./CL_Kernel.puml!Aux")
    assert resolved is not None
    path, line = resolved
    assert path.endswith("CL_Kernel.puml")
    assert line == 4


def test_include_resolves_to_file_top(tmp_path):
    (tmp_path / "style.iuml").write_text("' style\n")
    doc = tmp_path / "HLD.puml"
    doc.write_text("@startuml\n!include style.iuml\n@enduml\n")

    resolved = resolve_definition(str(doc), "!include style.iuml")
    assert resolved is not None
    assert resolved[0].endswith("style.iuml")
    assert resolved[1] == 0


def test_unresolvable_targets_return_none(tmp_path):
    doc = tmp_path / "x.puml"
    assert resolve_definition(str(doc), "!includesub ./missing.puml!X") is None
    assert resolve_definition(str(doc), "class Foo") is None
