"""Workspace symbols."""

from lsprotocol import types

from plantuml_lsp.server import core
from plantuml_lsp.server.lsp_workspace_symbols import workspace_symbol
from tests.fakes import open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (workspace_symbol,)


class TestWorkspaceSymbol:
    def test_answers_from_an_open_workspace(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        assert workspace_symbol(ls, types.WorkspaceSymbolParams(query="x")) is None
        doc, _ = core.index_of(ls, uris["c.puml"])
        core.workspace_of(ls, doc)
        assert {
            s.name
            for s in workspace_symbol(ls, types.WorkspaceSymbolParams(query="taza"))
        } == {"Taza"}
