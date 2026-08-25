"""Parse diagnostics: ERROR and missing nodes with exact positions."""

from tree_sitter import Node

from plantuml_lsp.parsing import parse

MAX_DIAGNOSTICS = 50

# (start_line, start_col, end_line, end_col, message)
DiagnosticTuple = tuple[int, int, int, int, str]


def collect_diagnostics(src: bytes) -> list[DiagnosticTuple]:
    tree = parse(src)
    found: list[DiagnosticTuple] = []
    _walk(tree.root_node, found)
    return found[:MAX_DIAGNOSTICS]


def _walk(node: Node, found: list[DiagnosticTuple]) -> None:
    if not node.has_error and not node.is_missing:
        return
    if node.type == "ERROR":
        found.append(_entry(node, "PlantUML syntax error"))
    elif node.is_missing:
        found.append(_entry(node, f"missing '{node.type}'"))
    for child in node.children:
        _walk(child, found)


def _entry(node: Node, message: str) -> DiagnosticTuple:
    sr, sc = node.start_point
    er, ec = node.end_point
    if (sr, sc) == (er, ec):
        ec += 1
    return (sr, sc, er, ec, message)
