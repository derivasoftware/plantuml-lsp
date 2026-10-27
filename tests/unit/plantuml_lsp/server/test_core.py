"""The core: one instance, the shared helpers, the entry point."""

from plantuml_lsp.server import core
from tests.fakes import open_workspace

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\n@enduml\n"


def _ls(tmp_path, files=None):
    core.workspaces.clear()
    return open_workspace(tmp_path, files or {"c.puml": CLASSES})


__covers__ = (
    core.range_of,
    core.index_of,
    core.workspace_of,
    core.merged_occurrences,
    core.main,
)


class TestCore:
    def test_range_of_builds_an_lsp_range(self) -> None:
        r = core.range_of(1, 2, 3, 4)
        assert (r.start.line, r.start.character, r.end.line, r.end.character) == (
            1,
            2,
            3,
            4,
        )

    def test_index_of_and_one_workspace_per_root(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        doc, index = core.index_of(ls, uris["c.puml"])
        assert "Cafetera" in index.entities
        assert core.workspace_of(ls, doc) is core.workspace_of(ls, doc)

    def test_merged_occurrences_drop_duplicates(self, tmp_path) -> None:
        ls, uris = _ls(tmp_path)
        doc, index = core.index_of(ls, uris["c.puml"])
        occs = core.merged_occurrences("Cafetera", index, core.workspace_of(ls, doc))
        assert len(occs) == len(set(occs))

    def test_main_starts_the_stdio_loop(self, monkeypatch) -> None:
        started = []
        monkeypatch.setattr(core.server, "start_io", lambda: started.append(True))
        core.main()
        assert started == [True]
