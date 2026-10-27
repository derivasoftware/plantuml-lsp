"""Document symbols: entities, participants and grouping blocks."""

from plantuml_lsp.symbols import collect_symbols

__covers__ = (collect_symbols,)


class TestCollectSymbols:
    def test_entities_inside_a_namespace_are_qualified(self) -> None:
        src = (
            b"@startuml\nnamespace shop {\n  class Cart\n  interface Pay\n}\n@enduml\n"
        )
        names = {(name, kind) for name, kind, *_ in collect_symbols(src)}
        assert {
            ("shop", "namespace"),
            ("shop.Cart", "class"),
            ("shop.Pay", "interface"),
        } <= names

    def test_a_participant_is_named_by_its_alias(self) -> None:
        src = b'@startuml\nparticipant "Long Name" as L\nL -> L : ping\n@enduml\n'
        assert ("L", "participant") in {(n, k) for n, k, *_ in collect_symbols(src)}

    def test_a_symbol_carries_its_span(self) -> None:
        name, kind, sr, sc, er, ec = collect_symbols(b"@startuml\nclass A\n@enduml\n")[
            0
        ]
        assert (name, kind, sr) == ("A", "class", 1)
