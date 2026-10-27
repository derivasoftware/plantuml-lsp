"""Rename: every occurrence rewritten, quotes kept."""

from plantuml_lsp.index import build_index
from plantuml_lsp.rename import edits_from, rename_edits

__covers__ = (edits_from, rename_edits)


class TestEditsFrom:
    def test_a_quoted_occurrence_keeps_its_quotes(self) -> None:
        src = b'"Widget" --> B\n'
        ((path, row, scol, ecol, text),) = edits_from(
            [("d", 0, 0, 8)], "Gadget", {"d": src}.get
        )
        assert (scol, ecol, text) == (1, 7, "Gadget")

    def test_an_unreadable_file_is_skipped(self) -> None:
        assert edits_from([("gone", 0, 0, 3)], "X", {}.get) == []


class TestRenameEdits:
    def test_rewrites_every_occurrence_in_the_closure(self, tmp_path) -> None:
        doc = tmp_path / "d.puml"
        src = b"@startuml\nclass Widget\nWidget --> Widget\n@enduml\n"
        doc.write_bytes(src)
        edits = rename_edits("Widget", "Gadget", build_index(str(doc), src))
        assert len(edits) == 3 and {e[4] for e in edits} == {"Gadget"}
