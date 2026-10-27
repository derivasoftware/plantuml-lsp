"""The token under the cursor, and the entity id it resolves to."""

from __future__ import annotations

import re

from plantuml_lsp.index.Entity import Entity
from plantuml_lsp.parsing import node_text, parse


def identifier_at(src: bytes, row: int, col: int) -> str | None:
    """The identifier (or quoted name) token under the cursor, falling
    back to the identifier-shaped word at the cursor when the CST node
    is opaque (parameter payloads, member types, labels)."""
    node = parse(src).root_node.descendant_for_point_range((row, col), (row, col))
    if node is not None and node.type in ("identifier", "string"):
        return node_text(src, node).strip('"')
    return word_at(src, row, col)


_WORD = re.compile(r"[A-Za-z_][\w]*(?:[.-][A-Za-z_]\w*)*")


def word_at(src: bytes, row: int, col: int) -> str | None:
    """The identifier-shaped word covering the cursor column."""
    lines = src.decode(errors="replace").splitlines()
    if row >= len(lines):
        return None
    for match in _WORD.finditer(lines[row]):
        if match.start() <= col < match.end():
            return match.group(0)
    return None


def resolve_entity(name: str, entities: dict[str, Entity]) -> str | None:
    """The id a cursor token resolves to: exact, or the tail of a
    qualified name (maquina.Cafetera -> Cafetera)."""
    if name in entities:
        return name
    if "." in name:
        tail = name.rsplit(".", 1)[-1]
        if tail in entities:
            return tail
    return None
