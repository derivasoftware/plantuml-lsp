"""LSP v1 pure features: completion, hover, references, rename, links, lints."""

from pathlib import Path

from plantuml_lsp.hover import hover_for
from plantuml_lsp.index import build_index

SRC = """@startuml
class Widget {
  +draw() : None
  -size : int
}
interface Drawable
Widget --> Drawable : implements-ish
@enduml
"""


def idx(tmp_path: Path, name: str = "d.puml", src: str = SRC):
    doc = tmp_path / name
    doc.write_text(src)
    return str(doc), build_index(str(doc), src.encode())


def test_hover_unknown_returns_none(tmp_path):
    _, index = idx(tmp_path)
    assert hover_for("Nope", index) is None


def test_entity_definitions_resolve_types_and_qualified_names(tmp_path):
    from plantuml_lsp.definitions import entity_definitions
    from plantuml_lsp.workspace import WorkspaceIndex

    (tmp_path / "CL_Pedido.puml").write_text(
        "@startuml\nnamespace pedidos {\n  class Pedido\n}\n@enduml\n"
    )
    doc = tmp_path / "CL_Uso.puml"
    doc.write_text(
        "@startuml\nclass Cafetera {\n  +preparar(p: Pedido) : Taza\n}\n@enduml\n"
    )
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(doc), doc.read_bytes())
    for name in ("Pedido", "pedidos.Pedido"):
        locs = entity_definitions(name, index, ws)
        assert locs, name
        assert locs[0][0].endswith("CL_Pedido.puml")


def test_word_at_reads_opaque_positions():
    from plantuml_lsp.index import word_at

    src = b"@startuml\nclass C {\n  +preparar(pedido: Pedido) : Taza\n}\n@enduml\n"
    assert word_at(src, 2, 22) == "Pedido"
    assert word_at(src, 2, 31) == "Taza"


def test_call_lint_unknown_is_information(tmp_path):
    from plantuml_lsp.lints import collect_call_lints
    from plantuml_lsp.workspace import WorkspaceIndex

    doc = tmp_path / "SEQ.puml"
    lines = [
        "@startuml",
        "actor Barista",
        "participant Cafetera",
        "Cafetera --> Barista : error(mensaje)",
        "@enduml",
        "",
    ]
    src = "\n".join(lines).encode()
    doc.write_bytes(src)
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(doc), src)
    lints = collect_call_lints(src, index, ws)
    assert len(lints) == 1
    *_span, msg, sev = lints[0]
    assert "error" in msg and sev == "information"
