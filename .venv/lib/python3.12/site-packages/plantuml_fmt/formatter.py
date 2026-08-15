"""Indentation-normalizing PlantUML formatter (v0).

The v0 canonical style touches ONLY leading horizontal whitespace:
statement lines are re-indented to two spaces per enclosing block, and
opaque content — note bodies, raw-block bodies, block-comment
continuation lines — is preserved byte-identical. Everything after the
first non-whitespace byte of a line never changes, which makes the
formatter lossless by construction and trivially idempotent.
"""

import tree_sitter_plantuml
from tree_sitter import Language, Node, Parser

INDENT = b"  "

# Braced blocks whose inner lines gain one indentation level.
_BLOCKS = {"entity_body", "package_block", "namespace_block", "together_block"}

_parser = None


def _get_parser() -> Parser:
    global _parser
    if _parser is None:
        _parser = Parser(Language(tree_sitter_plantuml.language()))
    return _parser


def _freeze(frozen: list[bool], first_row: int, last_row: int) -> None:
    for row in range(max(first_row, 0), min(last_row + 1, len(frozen))):
        frozen[row] = True


def _child_row(node: Node, child_type: str) -> int | None:
    """Row of the last child of the given type, or None."""
    row = None
    for child in node.children:
        if child.type == child_type:
            row = child.start_point[0]
    return row


def _indent_block(node: Node, depth: list[int]) -> None:
    # the closing-brace row keeps the parent depth; blocks that consume
    # a trailing newline end on the NEXT row, so anchor on the '}' child
    brace_row = _child_row(node, "}")
    if brace_row is None:
        brace_row = node.end_point[0]
    for row in range(node.start_point[0] + 1, brace_row):
        depth[row] += 1


def _collect(node: Node, depth: list[int], frozen: list[bool]) -> None:
    kind = node.type
    if kind in _BLOCKS:
        _indent_block(node, depth)
    elif kind == "note_statement":
        end_row = _child_row(node, "end note")
        if end_row is not None:
            _freeze(frozen, node.start_point[0] + 1, end_row - 1)
    elif kind == "raw_block":
        tail_row = _child_row(node, "raw_line")
        if tail_row is not None:
            _freeze(frozen, node.start_point[0] + 1, tail_row - 1)
    elif kind == "block_comment":
        # continuation lines live inside the token; the first line's
        # leading whitespace is outside it and stays reindentable
        _freeze(frozen, node.start_point[0] + 1, node.end_point[0])
    for child in node.children:
        _collect(child, depth, frozen)


def format_bytes(src: bytes) -> bytes:
    tree = _get_parser().parse(src)
    lines = src.split(b"\n")
    depth = [0] * len(lines)
    frozen = [False] * len(lines)
    _collect(tree.root_node, depth, frozen)

    out = []
    for row, line in enumerate(lines):
        if frozen[row]:
            out.append(line)
        elif not (stripped := line.lstrip(b" \t")):
            out.append(b"")
        else:
            out.append(INDENT * depth[row] + stripped)
    return b"\n".join(out)


def format_text(src: str) -> str:
    return format_bytes(src.encode()).decode()
