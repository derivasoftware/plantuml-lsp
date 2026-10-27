"""Occurrences from the CST: identifier and string tokens only."""

from plantuml_lsp.index.occurrences import scan_occurrences
from plantuml_lsp.parsing import parse

__covers__ = (scan_occurrences,)


class TestScanOccurrences:
    def test_finds_identifiers_and_quoted_names_never_labels(self) -> None:
        src = b'@startuml\nclass Widget\n"Widget" --> B : Widget\n@enduml\n'
        found: list = []
        scan_occurrences(parse(src).root_node, src, "Widget", "d.puml", found)
        rows = sorted(row for _p, row, _s, _e in found)
        assert rows == [1, 2]

    def test_a_qualified_name_reports_its_tail(self) -> None:
        src = b"@startuml\nclass Widget\na.Widget --> B\n@enduml\n"
        found: list = []
        scan_occurrences(parse(src).root_node, src, "Widget", "d.puml", found)
        assert (found[-1][1], found[-1][2]) == (2, len("a."))
