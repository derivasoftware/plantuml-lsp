"""Completion: the index's ids and keywords, and by cursor context."""

from pathlib import Path

from plantuml_lsp.completion import (
    KEYWORDS,
    collect_completions,
    contextual_completions,
)
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (collect_completions, contextual_completions)

SRC = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nclass Taza\nCafetera --> \n@enduml\n"


def _index(tmp_path: Path, text: str = SRC):
    doc = tmp_path / "d.puml"
    doc.write_text(text)
    return build_index(str(doc), text.encode())


class TestCollectCompletions:
    def test_offers_every_entity_and_every_keyword(self, tmp_path: Path) -> None:
        items = collect_completions(_index(tmp_path))
        assert ("Cafetera", "class") in items and ("Taza", "class") in items
        assert {k for k, kind in items if kind == "keyword"} == set(KEYWORDS)


class TestContextualCompletions:
    def test_after_an_arrow_offers_the_endpoints(self, tmp_path: Path) -> None:
        index = _index(tmp_path)
        labels = [
            c[0]
            for c in contextual_completions(
                SRC.encode(), 5, len("Cafetera --> "), index
            )
        ]
        assert "Taza" in labels

    def test_in_a_label_the_receivers_methods_come_first(self, tmp_path: Path) -> None:
        text = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\nparticipant Cafetera\nCafetera -> Cafetera : \n@enduml\n"
        index = _index(tmp_path, text)
        ws = WorkspaceIndex(str(tmp_path))
        ws.refresh()
        items = contextual_completions(
            text.encode(), 5, len("Cafetera -> Cafetera : "), index, ws
        )
        assert items and items[0][0].startswith("preparar")

    def test_a_row_past_the_end_offers_nothing(self, tmp_path: Path) -> None:
        assert contextual_completions(SRC.encode(), 99, 0, _index(tmp_path)) == []
