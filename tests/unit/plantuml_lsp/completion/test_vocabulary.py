"""Completion's vocabulary: every indexed id and the keywords."""

from pathlib import Path

from plantuml_lsp.completion.vocabulary import KEYWORDS, collect_completions
from plantuml_lsp.index import build_index

__covers__ = (collect_completions,)

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
