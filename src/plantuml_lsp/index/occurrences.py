"""Occurrences from the CST: identifier and string tokens spelling an id,
never regex over text, so renames cannot touch labels, comments or notes."""

from __future__ import annotations

from tree_sitter import Node

from plantuml_lsp.parsing import node_text


def scan_occurrences(
    node: Node,
    src: bytes,
    entity_id: str,
    path: str,
    found: list[tuple[str, int, int, int]],
) -> None:
    if node.type in ("identifier", "string"):
        text = node_text(src, node).strip('"')
        if text == entity_id:
            found.append(
                (path, node.start_point[0], node.start_point[1], node.end_point[1])
            )
        elif text.endswith("." + entity_id):
            # qualified use: report the span of the tail segment only,
            # so references highlight and renames rewrite just the name
            offset = (node.end_point[1] - node.start_point[1]) - len(entity_id)
            found.append(
                (
                    path,
                    node.start_point[0],
                    node.start_point[1] + offset,
                    node.end_point[1],
                )
            )
        return
    for child in node.children:
        scan_occurrences(child, src, entity_id, path, found)
