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
    msgs = [msg for _r, _s, _e, _ec, msg, _sev in collect_lints(doc, src.encode(), index)]
    assert any("missing.iuml" in m for m in msgs)
    assert any("Nope" in m for m in msgs)


def test_lints_flag_duplicate_declarations(tmp_path):
    src = "@startuml\nclass A\ninterface A\n@enduml\n"
    doc, index = idx(tmp_path, "dup.puml", src)
    msgs = [msg for _r, _s, _e, _ec, msg, _sev in collect_lints(doc, src.encode(), index)]
    assert any("A" in m and "declared" in m for m in msgs)
