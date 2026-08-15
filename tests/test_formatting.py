"""The formatting feature delegates to plantuml-fmt."""

from plantuml_fmt.formatter import format_text


def test_formatter_dependency_normalizes_indentation():
    messy = "@startuml\n   class Foo\n@enduml\n"
    assert format_text(messy) == "@startuml\nclass Foo\n@enduml\n"
