"""The symbol index: every entity visible from a document — its own
declarations plus the transitive `!include`/`!includesub` closure.

The index is the substrate the v1 features share: completion offers its
ids, hover reads its members and relations, references and rename walk
its occurrence scan. Occurrences come from the CST (identifier/string
nodes whose text matches), never from regex over text, so renames can't
touch labels, comments or note bodies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from tree_sitter import Node

from plantuml_lsp.parsing import node_text, parse

_INCLUDE_ANY = re.compile(r"^\s*!include(?:sub)?\s+([^\s!]+)")

_DECLARATIONS = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
}

_REFERENCE_FIELDS = ("left", "right", "target")


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    path: str
    row: int
    scol: int
    ecol: int
    members: list[str] = field(default_factory=list)


@dataclass
class Index:
    doc_path: str
    entities: dict[str, Entity] = field(default_factory=dict)
    files: dict[str, bytes] = field(default_factory=dict)
    # duplicate declarations kept aside for the lints
    duplicates: list[Entity] = field(default_factory=list)
    # relation lines by entity id, for hover
    relations: dict[str, list[str]] = field(default_factory=dict)

    def occurrences(self, entity_id: str) -> list[tuple[str, int, int, int]]:
        """CST-backed (path, row, start_col, end_col) of every identifier
        or quoted-string token spelling the id, declaration included."""
        found: list[tuple[str, int, int, int]] = []
        for path, src in self.files.items():
            _scan_occurrences(parse(src).root_node, src, entity_id, path, found)
        return found


def build_index(doc_path: str, src: bytes) -> Index:
    index = Index(doc_path=doc_path)
    _index_file(doc_path, src, index, seen=set())
    return index


def identifier_at(src: bytes, row: int, col: int) -> str | None:
    """The identifier (or quoted name) token under the cursor."""
    node = parse(src).root_node.descendant_for_point_range((row, col), (row, col))
    if node is None:
        return None
    if node.type in ("identifier", "string"):
        return node_text(src, node).strip('"')
    return None


def _index_file(path: str, src: bytes, index: Index, seen: set[str]) -> None:
    resolved = str(Path(path).resolve())
    if resolved in seen:
        return
    seen.add(resolved)
    index.files[resolved] = src
    _walk(parse(src).root_node, src, resolved, index)
    for line in src.decode(errors="replace").splitlines():
        m = _INCLUDE_ANY.match(line)
        if m:
            target = (Path(path).parent / m.group(1)).resolve()
            if target.is_file():
                _index_file(str(target), target.read_bytes(), index, seen)


def _walk(node: Node, src: bytes, path: str, index: Index) -> None:
    kind = _declared_kind(node, src)
    if kind is not None:
        _add(index, node, src, path, kind)
    elif node.type == "relation":
        _record_relation(node, src, index)
    for child in node.children:
        _walk(child, src, path, index)


def _declared_kind(node: Node, src: bytes) -> str | None:
    if node.type in _DECLARATIONS:
        return _DECLARATIONS[node.type]
    if node.type in ("entity_declaration", "participant_declaration"):
        kind_node = node.child_by_field_name("kind")
        if kind_node is not None:
            return node_text(src, kind_node)
        return "entity" if node.type == "entity_declaration" else "participant"
    return None


def _record_relation(node: Node, src: bytes, index: Index) -> None:
    line = node_text(src, node).strip()
    for field_name in ("left", "right"):
        end = node.child_by_field_name(field_name)
        if end is not None and end.type in ("identifier", "string"):
            index.relations.setdefault(
                node_text(src, end).strip('"'), []
            ).append(line)


def _add(index: Index, node: Node, src: bytes, path: str, kind: str) -> None:
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return
    alias_node = node.child_by_field_name("alias")
    id_node = alias_node if alias_node is not None else name_node
    entity_id = node_text(src, id_node).strip('"')
    entity = Entity(
        id=entity_id,
        name=node_text(src, name_node).strip('"'),
        kind=kind,
        path=path,
        row=id_node.start_point[0],
        scol=id_node.start_point[1],
        ecol=id_node.end_point[1],
        members=_members(node, src),
    )
    if entity_id in index.entities:
        index.duplicates.append(entity)
    else:
        index.entities[entity_id] = entity


def _members(node: Node, src: bytes) -> list[str]:
    body = node.child_by_field_name("body")
    if body is None:
        return []
    return [
        node_text(src, member).strip()
        for member in body.named_children
        if member.type == "member"
    ]


def resolve_entity(name: str, entities: dict[str, "Entity"]) -> str | None:
    """The id a cursor token resolves to: exact, or the tail of a
    qualified name (maquina.Cafetera -> Cafetera)."""
    if name in entities:
        return name
    if "." in name:
        tail = name.rsplit(".", 1)[-1]
        if tail in entities:
            return tail
    return None


def _scan_occurrences(
    node: Node, src: bytes, entity_id: str, path: str,
    found: list[tuple[str, int, int, int]],
) -> None:
    if node.type in ("identifier", "string"):
        text = node_text(src, node).strip('"')
        if text == entity_id:
            found.append((path, node.start_point[0],
                          node.start_point[1], node.end_point[1]))
        elif text.endswith("." + entity_id):
            # qualified use: report the span of the tail segment only,
            # so references highlight and renames rewrite just the name
            offset = (node.end_point[1] - node.start_point[1]) - len(entity_id)
            found.append((path, node.start_point[0],
                          node.start_point[1] + offset, node.end_point[1]))
        return
    for child in node.children:
        _scan_occurrences(child, src, entity_id, path, found)
