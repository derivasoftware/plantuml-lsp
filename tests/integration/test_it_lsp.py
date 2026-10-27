"""The handlers at the protocol boundary, driven through a server double:
what an editor sends, what it gets back. Each test is registered by the
verification of the requirement whose handler it drives."""

from pathlib import Path

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_code_actions import code_action
from plantuml_lsp.server.lsp_completion import completion
from plantuml_lsp.server.lsp_definition import definition
from plantuml_lsp.server.lsp_diagnostics import did_open
from plantuml_lsp.server.lsp_formatting import formatting
from plantuml_lsp.server.lsp_hover import hover
from plantuml_lsp.server.lsp_links import document_link
from plantuml_lsp.server.lsp_references import references, rename
from plantuml_lsp.server.lsp_symbols import document_symbol
from plantuml_lsp.server.lsp_workspace_symbols import workspace_symbol
from tests.fakes import at, doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\nCafetera --> Taza\n@enduml\n"
SEQ = (
    "@startuml\nparticipant Cafetera\nparticipant Molinillo\n"
    "Cafetera -> Cafetera : preparar()\nCafetera -> Cafetera : moler()\n@enduml\n"
)


def _setup(tmp_path: Path, files: dict[str, str] | None = None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES, "s.puml": SEQ})


def test_publishes_parse_errors_lints_drift_and_participants(tmp_path):
    ls, uris = _setup(
        tmp_path,
        {"c.puml": CLASSES, "s.puml": SEQ, "b.puml": "@startuml\nclass {\n@enduml\n"},
    )
    for name in ("s.puml", "b.puml"):
        did_open(
            ls,
            types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(
                    uri=uris[name], language_id="plantuml", version=1, text=""
                )
            ),
        )
    by_uri = {p.uri: [d.message for d in p.diagnostics] for p in ls.published}
    seq = "\n".join(by_uri[uris["s.puml"]])
    assert "moler" in seq and "Molinillo" in seq and "preparar" not in seq
    assert by_uri[uris["b.puml"]]


def test_a_participant_naming_a_box_of_the_hld_resolves_and_is_not_an_orphan(tmp_path):
    hld = "@startuml\nnamespace Engine <<package>> {\n}\n@enduml\n"
    seq = "@startuml\nparticipant Engine\nparticipant Ghost\nEngine -> Ghost : run\n@enduml\n"
    ls, uris = _setup(tmp_path, {"HLD.puml": hld, "HSEQ.puml": seq})
    did_open(
        ls,
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uris["HSEQ.puml"], language_id="plantuml", version=1, text=""
            )
        ),
    )
    lints = [
        d.message
        for p in ls.published
        if p.uri == uris["HSEQ.puml"]
        for d in p.diagnostics
    ]
    assert any("Ghost" in m for m in lints)
    assert not any("Engine" in m for m in lints)
    card = hover(
        ls,
        types.HoverParams(text_document=doc_id(uris["HSEQ.puml"]), position=at(1, 14)),
    )
    assert "**package** `Engine`" in card.contents.value
    locations = definition(
        ls,
        types.DefinitionParams(
            text_document=doc_id(uris["HSEQ.puml"]), position=at(3, 2)
        ),
    )
    assert any(loc.uri == uris["HLD.puml"] for loc in locations)


def test_document_symbols_reach_the_editor(tmp_path):
    ls, uris = _setup(tmp_path)
    names = {
        s.name
        for s in document_symbol(
            ls, types.DocumentSymbolParams(text_document=doc_id(uris["c.puml"]))
        )
    }
    assert {"Cafetera", "Taza"} <= names


def test_definition_lands_on_the_method_a_call_names(tmp_path):
    ls, uris = _setup(tmp_path)
    loc = definition(
        ls,
        types.DefinitionParams(
            text_document=doc_id(uris["s.puml"]), position=at(3, 26)
        ),
    )
    assert loc.uri.endswith("c.puml") and loc.range.start.line == 2


def test_definition_lands_on_an_includesub_block(tmp_path):
    ls, uris = _setup(
        tmp_path,
        {
            "lib.iuml": "@startuml\n!startsub Base\nclass B\n!endsub\n@enduml\n",
            "m.puml": "@startuml\n!includesub lib.iuml!Base\n@enduml\n",
        },
    )
    loc = definition(
        ls,
        types.DefinitionParams(text_document=doc_id(uris["m.puml"]), position=at(1, 3)),
    )
    assert loc.uri.endswith("lib.iuml") and loc.range.start.line == 1


def test_formatting_answers_one_full_document_edit(tmp_path):
    ls, uris = _setup(
        tmp_path, {"f.puml": "@startuml\nclass A {\n+x : int\n}\n@enduml\n"}
    )
    edits = formatting(
        ls,
        types.DocumentFormattingParams(
            text_document=doc_id(uris["f.puml"]),
            options=types.FormattingOptions(tab_size=2, insert_spaces=True),
        ),
    )
    assert len(edits) == 1 and edits[0].range.start.line == 0


def test_completion_maps_methods_after_a_message_colon(tmp_path):
    seq = "@startuml\nparticipant Cafetera\nCafetera -> Cafetera : \n@enduml\n"
    ls, uris = _setup(tmp_path, {"c.puml": CLASSES, "s.puml": seq})
    items = completion(
        ls,
        types.CompletionParams(
            text_document=doc_id(uris["s.puml"]),
            position=at(2, len("Cafetera -> Cafetera : ")),
        ),
    )
    assert items and items[0].kind == types.CompletionItemKind.Method


def test_hover_shows_the_card_and_the_declared_method_of_a_call(tmp_path):
    ls, uris = _setup(tmp_path)
    card = hover(
        ls, types.HoverParams(text_document=doc_id(uris["c.puml"]), position=at(1, 8))
    )
    assert "**class** `Cafetera`" in card.contents.value
    call = hover(
        ls, types.HoverParams(text_document=doc_id(uris["s.puml"]), position=at(3, 26))
    )
    assert "+preparar() : Taza" in call.contents.value


def test_a_classless_receiver_jumps_to_a_homonym_and_says_so(tmp_path):
    seq = "@startuml\nrepo -> repo : preparar()\n@enduml\n"
    ls, uris = _setup(tmp_path, {"c.puml": CLASSES, "h.puml": seq})
    pos = at(1, len("repo -> repo : pre"))
    card = hover(
        ls, types.HoverParams(text_document=doc_id(uris["h.puml"]), position=pos)
    )
    assert "correlates with no class" in card.contents.value
    assert "+preparar() : Taza" in card.contents.value
    loc = definition(
        ls, types.DefinitionParams(text_document=doc_id(uris["h.puml"]), position=pos)
    )
    assert loc.uri == uris["c.puml"] and loc.range.start.line == 2


def test_references_and_rename_span_the_workspace(tmp_path):
    ls, uris = _setup(tmp_path)
    refs = references(
        ls,
        types.ReferenceParams(
            text_document=doc_id(uris["c.puml"]),
            position=at(1, 8),
            context=types.ReferenceContext(include_declaration=True),
        ),
    )
    assert {r.uri for r in refs} == {uris["c.puml"], uris["s.puml"]}
    edit = rename(
        ls,
        types.RenameParams(
            text_document=doc_id(uris["c.puml"]), position=at(1, 8), new_name="Maquina"
        ),
    )
    assert set(edit.changes) == {uris["c.puml"], uris["s.puml"]}


def test_document_links_point_at_the_included_files(tmp_path):
    ls, uris = _setup(tmp_path, {"m.puml": "@startuml\n!include lib.iuml\n@enduml\n"})
    (link,) = document_link(
        ls, types.DocumentLinkParams(text_document=doc_id(uris["m.puml"]))
    )
    assert link.target.endswith("lib.iuml") and link.range.start.line == 1


def test_workspace_symbols_answer_from_every_open_workspace(tmp_path):
    ls, uris = _setup(tmp_path)
    assert (
        workspace_symbol(ls, types.WorkspaceSymbolParams(query="Caf")) is None
    )  # nothing opened yet
    hover(
        ls, types.HoverParams(text_document=doc_id(uris["c.puml"]), position=at(1, 8))
    )
    names = {
        s.name for s in workspace_symbol(ls, types.WorkspaceSymbolParams(query="caf"))
    }
    assert "Cafetera" in names


def test_code_actions_offer_a_fix_per_lint(tmp_path):
    ls, uris = _setup(
        tmp_path,
        {"c.puml": CLASSES, "u.puml": "@startuml\nclass A\nA --> Ghost\n@enduml\n"},
    )
    diag = types.Diagnostic(
        range=core.range_of(2, 6, 2, 11), message="no declaration for 'Ghost'"
    )
    (action,) = code_action(
        ls,
        types.CodeActionParams(
            text_document=doc_id(uris["u.puml"]),
            range=diag.range,
            context=types.CodeActionContext(diagnostics=[diag]),
        ),
    )
    assert "Ghost" in action.title and action.kind == types.CodeActionKind.QuickFix


def test_the_core_keeps_one_workspace_index_per_root(tmp_path):
    ls, uris = _setup(tmp_path)
    doc, index = core.index_of(ls, uris["c.puml"])
    first = core.workspace_of(ls, doc)
    assert core.workspace_of(ls, doc) is first and "Cafetera" in index.entities
    assert len(core.merged_occurrences("Cafetera", index, first)) >= 3
