"""Quick fixes."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_code_actions import code_action
from tests.fakes import doc_id, open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (code_action,)


class TestCodeAction:
    def test_a_diagnostic_no_fix_matches_offers_nothing(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        diag = types.Diagnostic(
            range=core.range_of(1, 0, 1, 1), message="something else"
        )
        ctx = types.CodeActionContext(diagnostics=[diag])
        assert (
            code_action(
                ls,
                types.CodeActionParams(
                    text_document=doc_id(uris["c.puml"]), range=diag.range, context=ctx
                ),
            )
            is None
        )
