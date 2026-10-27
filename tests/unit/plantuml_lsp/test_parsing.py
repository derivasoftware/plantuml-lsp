"""One grammar instance per process: the parser, the tree and a node's text."""

from plantuml_lsp import parsing
from plantuml_lsp.parsing import get_parser, node_text, parse

__covers__ = (get_parser, parse, node_text)

SRC = b"@startuml\nclass Widget\n@enduml\n"


class TestGetParser:
    def test_builds_the_parser_once_and_reuses_it(self, monkeypatch) -> None:
        monkeypatch.setattr(parsing, "_parser", None)
        first = get_parser()
        assert get_parser() is first


class TestParse:
    def test_a_well_formed_document_has_no_error(self) -> None:
        tree = parse(SRC)
        assert tree.root_node.type
        assert not tree.root_node.has_error

    def test_a_broken_document_still_yields_a_tree(self) -> None:
        tree = parse(b"@startuml\nclass {\n@enduml\n")
        assert tree.root_node.has_error


class TestNodeText:
    def test_reads_the_bytes_a_node_spans(self) -> None:
        root = parse(SRC).root_node
        assert node_text(SRC, root) == SRC.decode()

    def test_undecodable_bytes_are_replaced_not_raised(self) -> None:
        src = b"@startuml\nclass W\xff\n@enduml\n"
        root = parse(src).root_node
        assert "�" in node_text(src, root)
