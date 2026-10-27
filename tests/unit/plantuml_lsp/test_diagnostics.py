"""Parse diagnostics: ERROR and missing nodes with exact positions."""

from plantuml_lsp.diagnostics import MAX_DIAGNOSTICS, collect_diagnostics

__covers__ = (collect_diagnostics,)


class TestCollectDiagnostics:
    def test_a_clean_document_has_none(self) -> None:
        assert collect_diagnostics(b"@startuml\nclass A\n@enduml\n") == []

    def test_a_syntax_error_is_reported_with_its_position(self) -> None:
        found = collect_diagnostics(b"@startuml\nclass {\n@enduml\n")
        assert found
        sr, sc, er, ec, message = found[0]
        assert (er, ec) >= (sr, sc + 1) or er > sr
        assert message

    def test_a_zero_width_node_still_gets_one_column(self) -> None:
        for sr, sc, er, ec, _m in collect_diagnostics(b"@startuml\nA -> \n@enduml\n"):
            assert (er, ec) != (sr, sc)

    def test_the_list_is_capped(self) -> None:
        src = b"@startuml\n" + b"class {\n" * (MAX_DIAGNOSTICS * 2) + b"@enduml\n"
        assert len(collect_diagnostics(src)) <= MAX_DIAGNOSTICS
