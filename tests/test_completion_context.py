"""Contextual completion: candidates follow the cursor's lexical
context — the receiver's methods after a message colon, participants
after an arrow, the lane's methods in an activity action, keywords
only at statement heads, silence elsewhere."""

from pathlib import Path

from plantuml_lsp.completion import contextual_completions
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex


def make(tmp_path: Path):
    (tmp_path / "CL_M.puml").write_text(
        "@startuml\nclass Molinillo {\n  +moler(gramos: int) : Cafe\n"
        "  +ajustar(grosor: int) : None\n}\n@enduml\n"
    )
    lines = [
        "@startuml",
        "participant Cafetera",
        "participant Molinillo",
        "Cafetera -> Molinillo : moler(n)",
        "Cafetera -> ",
        "|Molinillo|",
        ": ",
        "par",
        "@enduml",
        "",
    ]
    doc = tmp_path / "SEQ.puml"
    src = "\n".join(lines).encode()
    doc.write_bytes(src)
    ws = WorkspaceIndex(str(tmp_path))
    return src, build_index(str(doc), src), ws


def labels(items):
    return {label for label, _kind, _detail in items}


def test_methods_after_the_message_colon(tmp_path):
    src, index, ws = make(tmp_path)
    items = contextual_completions(src, 3, 24, index, ws)  # tras ': '
    assert labels(items) == {"moler", "ajustar"}
    kinds = {label: kind for label, kind, _d in items}
    assert kinds["moler"] == "method"
    details = {label: d for label, _k, d in items}
    assert "gramos: int" in details["moler"]


def test_participants_after_an_arrow(tmp_path):
    src, index, ws = make(tmp_path)
    items = contextual_completions(src, 4, 12, index, ws)  # tras '-> '
    got = labels(items)
    assert {"Cafetera", "Molinillo"} <= got
    assert "class" not in got and "note" not in got  # sin keywords


def test_lane_methods_in_an_activity_action(tmp_path):
    src, index, ws = make(tmp_path)
    items = contextual_completions(src, 6, 2, index, ws)  # ': ' bajo |Molinillo|
    assert labels(items) == {"moler", "ajustar"}


def test_keywords_and_entities_at_statement_head(tmp_path):
    src, index, ws = make(tmp_path)
    items = contextual_completions(src, 7, 3, index, ws)  # 'par'
    got = labels(items)
    assert {"participant", "package", "par"} <= got
    assert "Cafetera" in got


def test_silence_in_free_label_text(tmp_path):
    src, index, ws = make(tmp_path)
    # dentro de los argumentos de la llamada: nada que ofrecer
    items = contextual_completions(src, 3, 30, index, ws)
    assert items == []
