"""Document symbols: entities, participants and grouping blocks."""

from tree_sitter import Node

from plantuml_lsp.parsing import node_text, parse

# (qualified_name, kind, start_line, start_col, end_line, end_col)
SymbolTuple = tuple[str, str, int, int, int, int]

_ENTITY_KINDS = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
}
_GROUP_KINDS = {
    "namespace_block": "namespace",
    "package_block": "package",
}


def collect_symbols(src: bytes) -> list[SymbolTuple]:
    found: list[SymbolTuple] = []
    _walk(parse(src).root_node, src, [], found)
    return found


def _walk(node: Node, src: bytes, ns: list[str], found: list[SymbolTuple]) -> None:
    kind = node.type
    if kind in _GROUP_KINDS:
        name = _name_of(node, src)
        found.append(_entry(".".join([*ns, name]), _GROUP_KINDS[kind], node))
        for child in node.children:
            _walk(child, src, [*ns, name], found)
        return
    if kind in _ENTITY_KINDS:
        found.append(
            _entry(".".join([*ns, _name_of(node, src)]), _ENTITY_KINDS[kind], node)
        )
    elif kind == "participant_declaration":
        alias = node.child_by_field_name("alias")
        target = alias if alias is not None else node.child_by_field_name("name")
        found.append(_entry(node_text(src, target).strip('"'), "participant", node))
    for child in node.children:
        _walk(child, src, ns, found)


def _name_of(node: Node, src: bytes) -> str:
    name = node.child_by_field_name("name")
    return node_text(src, name).strip('"') if name is not None else "?"


def _entry(name: str, kind: str, node: Node) -> SymbolTuple:
    sr, sc = node.start_point
    er, ec = node.end_point
    return (name, kind, sr, sc, er, ec)
