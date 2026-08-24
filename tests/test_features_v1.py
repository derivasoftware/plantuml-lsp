"""LSP v1 pure features: completion, hover, references, rename, links, lints."""

from pathlib import Path

from plantuml_lsp.completion import collect_completions
from plantuml_lsp.hover import hover_for
from plantuml_lsp.index import build_index
from plantuml_lsp.links import collect_links
from plantuml_lsp.lints import collect_lints
from plantuml_lsp.rename import rename_edits

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


def test_completion_offers_entities_and_keywords(tmp_path):
    _, index = idx(tmp_path)
    items = collect_completions(index)
    labels = {label for label, _kind in items}
    assert {"Widget", "Drawable", "class", "note", "participant"} <= labels
    kinds = dict(items)
    assert kinds["Widget"] == "class"
    assert kinds["class"] == "keyword"


def test_hover_summarizes_an_entity(tmp_path):
    _, index = idx(tmp_path)
    text = hover_for("Widget", index)
    assert text is not None
    assert "**class** `Widget`" in text
    assert "+draw() : None" in text
    assert "Widget --> Drawable" in text


def test_hover_unknown_returns_none(tmp_path):
    _, index = idx(tmp_path)
    assert hover_for("Nope", index) is None


def test_references_and_rename_cover_declaration_and_uses(tmp_path):
    _, index = idx(tmp_path)
    occs = index.occurrences("Widget")
    assert len(occs) == 2  # declaration + relation
    edits = rename_edits("Widget", "Gadget", index)
    assert len(edits) == 2
    for _path, row, scol, ecol, new in edits:
        assert new == "Gadget"
        assert ecol - scol == len("Widget")


def test_links_resolve_include_targets(tmp_path):
    (tmp_path / "lib.iuml").write_text("@startuml\n!startsub S\n!endsub\n@enduml\n")
    src = "@startuml\n!include lib.iuml\n!includesub lib.iuml!S\n@enduml\n"
    doc = tmp_path / "main.puml"
    doc.write_text(src)
    links = collect_links(str(doc), src.encode())
    assert len(links) == 2
    for row, scol, ecol, target in links:
        assert target.endswith("lib.iuml")
        assert src.splitlines()[row][scol:ecol] == "lib.iuml"


def test_lints_flag_unknown_endpoints_in_class_mode(tmp_path):
    src = "@startuml\nclass A\nA --> Ghost\n@enduml\n"
    doc, index = idx(tmp_path, "c.puml", src)
    lints = collect_lints(doc, src.encode(), index)
    assert any("Ghost" in msg for _r, _s, _e, _ec, msg, _sev in lints)


def test_lints_stay_quiet_for_sequence_implicit_participants(tmp_path):
    src = "@startuml\nparticipant A\nA -> Ghost : hi\n@enduml\n"
    doc, index = idx(tmp_path, "s.puml", src)
    assert collect_lints(doc, src.encode(), index) == []


def test_lints_flag_broken_includes(tmp_path):
    src = "@startuml\n!include missing.iuml\n!includesub lib.iuml!Nope\n@enduml\n"
    (tmp_path / "lib.iuml").write_text("@startuml\n!startsub Real\n!endsub\n@enduml\n")
    doc, index = idx(tmp_path, "b.puml", src)
    msgs = [
        msg for _r, _s, _e, _ec, msg, _sev in collect_lints(doc, src.encode(), index)
    ]
    assert any("missing.iuml" in m for m in msgs)
    assert any("Nope" in m for m in msgs)


def test_lints_flag_duplicate_declarations(tmp_path):
    src = "@startuml\nclass A\ninterface A\n@enduml\n"
    doc, index = idx(tmp_path, "dup.puml", src)
    msgs = [
        msg for _r, _s, _e, _ec, msg, _sev in collect_lints(doc, src.encode(), index)
    ]
    assert any("A" in m and "declared" in m for m in msgs)


def test_hover_enriches_participants_with_their_class_card(tmp_path):
    from plantuml_lsp.workspace import WorkspaceIndex

    (tmp_path / "CL_W.puml").write_text(
        "@startuml\nclass Widget {\n  +draw() : None\n}\n@enduml\n"
    )
    seq = tmp_path / "SEQ_F.puml"
    seq.write_text("@startuml\nparticipant Widget\nactor U\nU -> Widget\n@enduml\n")
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(seq), seq.read_bytes())
    text = hover_for("Widget", index, ws)
    assert text is not None
    assert "**participant** `Widget`" in text
    assert "+draw() : None" in text
    assert "CL_W.puml" in text


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


def test_call_resolution_matches_by_name_only(tmp_path):
    from plantuml_lsp.definitions import call_at, resolve_call
    from plantuml_lsp.workspace import WorkspaceIndex

    (tmp_path / "CL_M.puml").write_text(
        "@startuml\nclass Molinillo {\n  +moler(gramos: int) : Cafe\n}\n@enduml\n"
    )
    doc = tmp_path / "SEQ.puml"
    src = (
        "@startuml\nparticipant Molinillo\n"
        "Cafetera -> Molinillo : moler(num_granos)\n"
        "Cafetera -> Molinillo : afilar(disco)\n"
        "Molinillo --> Cafetera : el cafe listo\n@enduml\n"
    ).encode()
    doc.write_bytes(src)
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(doc), src)

    call = call_at(src, 2, 26)
    assert call == ("Molinillo", "moler")
    tier, entity, method = resolve_call("Molinillo", "moler", index, ws)
    assert tier == "declared" and "gramos: int" in method[3]
    # undeclared method on a correlated class -> drift
    tier2, entity2, _ = resolve_call("Molinillo", "afilar", index, ws)
    assert tier2 == "drift" and entity2.kind == "class"
    # classless receiver, method declared somewhere -> best-effort jump
    tier3, entity3, loc3 = resolve_call("Actor", "moler", index, ws)
    assert tier3 == "declared" and loc3 is not None
    # classless receiver, declared nowhere -> unknown
    tier4, _e, _l = resolve_call("Actor", "inventado", index, ws)
    assert tier4 == "unknown"
    # free-text labels are not calls
    assert call_at(src, 4, 28) is None


def test_call_drift_lint_flags_only_undeclared(tmp_path):
    from plantuml_lsp.lints import collect_call_lints
    from plantuml_lsp.workspace import WorkspaceIndex

    (tmp_path / "CL_M.puml").write_text(
        "@startuml\nclass Molinillo {\n  +moler(gramos: int) : Cafe\n}\n@enduml\n"
    )
    doc = tmp_path / "SEQ.puml"
    src = (
        "@startuml\nparticipant Molinillo\n"
        "Cafetera -> Molinillo : moler(num_granos)\n"
        "Cafetera -> Molinillo : afilar(disco)\n@enduml\n"
    ).encode()
    doc.write_bytes(src)
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(doc), src)
    lints = collect_call_lints(src, index, ws)
    msgs = [msg for *_span, msg, _sev in lints]
    assert any("afilar" in m for m in msgs)
    assert not any("moler" in m and "afilar" not in m for m in msgs)


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


def test_activity_actions_correlate_with_methods(tmp_path):
    from plantuml_lsp.definitions import action_at, resolve_call
    from plantuml_lsp.workspace import WorkspaceIndex

    (tmp_path / "CL_C.puml").write_text(
        "@startuml\nclass Cafetera {\n  -calentar(objetivo: float) : None\n}\n@enduml\n"
    )
    doc = tmp_path / "ACT.puml"
    lines = [
        "@startuml",
        "|Cafetera|",
        ":calentar(objetivo);",
        ":afilar(disco);",
        ":texto libre sin llamada;",
        "@enduml",
        "",
    ]
    src = "\n".join(lines).encode()
    doc.write_bytes(src)
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(doc), src)

    assert action_at(index, 2) == ("Cafetera", "calentar")
    tier, entity, loc = resolve_call("Cafetera", "calentar", index, ws)
    assert tier == "declared" and "objetivo: float" in loc[3]
    # accion sin llamada no se registra
    assert action_at(index, 4) is None
    # sitios de llamada agregados al workspace
    assert len(ws.call_sites("calentar")) == 1


def test_activity_drift_lints_use_the_lane(tmp_path):
    from plantuml_lsp.lints import collect_call_lints
    from plantuml_lsp.workspace import WorkspaceIndex

    (tmp_path / "CL_M.puml").write_text(
        "@startuml\nclass Molinillo {\n  +moler(gramos: int) : Cafe\n}\n@enduml\n"
    )
    doc = tmp_path / "ACT.puml"
    lines = [
        "@startuml",
        "|Molinillo|",
        ":moler(granos);",
        ":afilar(disco);",
        "@enduml",
        "",
    ]
    src = "\n".join(lines).encode()
    doc.write_bytes(src)
    ws = WorkspaceIndex(str(tmp_path))
    index = build_index(str(doc), src)
    lints = collect_call_lints(src, index, ws)
    msgs = [msg for *_s, msg, _sev in lints]
    assert any("afilar" in m for m in msgs)
    assert not any("'moler" in m for m in msgs)
