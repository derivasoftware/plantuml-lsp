"""The token under the cursor and the entity id it resolves to."""

from plantuml_lsp.index.cursor import identifier_at, resolve_entity, word_at

__covers__ = (identifier_at, word_at, resolve_entity)

SRC = b'@startuml\nclass "Fancy Name" as FN\nclass C {\n  +preparar(pedido: Pedido) : Taza\n}\n@enduml\n'


class TestIdentifierAt:
    def test_reads_an_identifier_token(self) -> None:
        assert identifier_at(SRC, 1, 23) == "FN"

    def test_strips_the_quotes_of_a_string_token(self) -> None:
        assert identifier_at(SRC, 1, 8) == "Fancy Name"

    def test_falls_back_to_the_word_in_an_opaque_node(self) -> None:
        assert identifier_at(SRC, 3, 22) == "Pedido"


class TestWordAt:
    def test_reads_words_in_opaque_positions(self) -> None:
        assert word_at(SRC, 3, 22) == "Pedido"
        assert word_at(SRC, 3, 31) == "Taza"

    def test_a_row_past_the_end_is_none(self) -> None:
        assert word_at(SRC, 99, 0) is None


class TestResolveEntity:
    def test_exact_then_the_tail_of_a_qualified_name(self) -> None:
        entities = {"Widget": object()}
        assert resolve_entity("Widget", entities) == "Widget"
        assert resolve_entity("maquina.Widget", entities) == "Widget"
        assert resolve_entity("otra.Cosa", entities) is None
