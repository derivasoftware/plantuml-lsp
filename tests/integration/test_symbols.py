"""Symbols: entities qualify by namespace; participants use their alias."""

from plantuml_lsp.symbols import collect_symbols

SRC = b"""@startuml
namespace core {
  class Kernel
  interface Port
}
enum Mode
participant "Audit Evaluator" as eval
actor Developer
@enduml
"""


def test_symbols_inventory():
    symbols = collect_symbols(SRC)
    inventory = {(name, kind) for name, kind, *_ in symbols}
    assert ("core", "namespace") in inventory
    assert ("core.Kernel", "class") in inventory
    assert ("core.Port", "interface") in inventory
    assert ("Mode", "enum") in inventory
    assert ("eval", "participant") in inventory
    assert ("Developer", "participant") in inventory


def test_symbol_positions_are_line_accurate():
    by_name = {name: (sr, er) for name, _, sr, _, er, _ in collect_symbols(SRC)}
    assert by_name["core.Kernel"][0] == 2
    assert by_name["Mode"][0] == 5
