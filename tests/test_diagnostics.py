"""Diagnostics: clean sources yield none; broken sources yield positions."""

from plantuml_lsp.diagnostics import collect_diagnostics

CLEAN = b"@startuml\nclass Foo\nDog --|> Animal\n@enduml\n"
BROKEN = b"@startuml\nclass Foo extends\n@enduml\n"


def test_clean_source_has_no_diagnostics():
    assert collect_diagnostics(CLEAN) == []


def test_broken_source_reports_positions():
    diags = collect_diagnostics(BROKEN)
    assert diags
    sr, sc, er, ec, msg = diags[0]
    assert sr == 1
    assert msg
