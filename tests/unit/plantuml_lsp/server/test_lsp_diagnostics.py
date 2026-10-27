"""Diagnostics published on open and change."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_diagnostics import did_change, did_open, publish
from tests.fakes import open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (publish, did_open, did_change)


class TestPublish:
    def test_open_and_change_publish_for_the_document(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path, {"b.puml": "@startuml\nclass {\n@enduml\n"})
        item = types.TextDocumentItem(
            uri=uris["b.puml"], language_id="plantuml", version=1, text=""
        )
        did_open(ls, types.DidOpenTextDocumentParams(text_document=item))
        did_change(
            ls,
            types.DidChangeTextDocumentParams(
                text_document=types.VersionedTextDocumentIdentifier(
                    uri=uris["b.puml"], version=2
                ),
                content_changes=[],
            ),
        )
        publish(ls, uris["b.puml"])
        assert len(ls.published) == 3 and all(p.diagnostics for p in ls.published)
