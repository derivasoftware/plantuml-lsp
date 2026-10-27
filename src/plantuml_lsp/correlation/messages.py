"""Call-shaped message labels against the methods their receiver's class
declares: where behaviour drifts from structure. A label is an invocation;
its arguments are free text and never matter, so matching is by name."""

from __future__ import annotations

import re

from tree_sitter import Node

from plantuml_lsp.index import Index, resolve_entity
from plantuml_lsp.parsing import node_text, parse
from plantuml_lsp.workspace import CLASS_KINDS

_CALL_SHAPE = re.compile(r"^\s*(\w+)\s*\(")


def _label_under_cursor(src: bytes, row: int, col: int):
    """The relation label node at the cursor, or None."""
    node = parse(src).root_node.descendant_for_point_range((row, col), (row, col))
    while node is not None and node.type != "relation":
        if node.type == "label":
            break
        node = node.parent
    if node is None or node.type != "label":
        return None
    relation = node.parent
    if relation is None or relation.type != "relation":
        return None
    return node


def _relation_receiver(src: bytes, relation):
    """The endpoint a message points at, honoring arrow direction."""
    operator = relation.child_by_field_name("operator")
    reversed_ = operator is not None and node_text(src, operator).startswith("<")
    receiver = relation.child_by_field_name("left" if reversed_ else "right")
    if receiver is None:
        return None
    return node_text(src, receiver).strip('"')


def call_at(src: bytes, row: int, col: int):
    """(receiver_name, method_name) when the cursor sits on the label
    of a message whose text is call-shaped; arguments are free text and
    never matter. None anywhere else."""
    label = _label_under_cursor(src, row, col)
    if label is None:
        return None
    m = _CALL_SHAPE.match(node_text(src, label))
    if m is None:
        return None
    receiver = _relation_receiver(src, label.parent)
    if receiver is None:
        return None
    return receiver, m.group(1)


def _receiver_candidates(receiver: str, index, workspace) -> list:
    """The entities a receiver name may denote: document first, then the
    workspace card (qualified tails included)."""
    candidates = []
    resolved = resolve_entity(receiver, index.entities)
    if resolved is not None:
        candidates.append(index.entities[resolved])
    if workspace is not None:
        card = workspace.class_card(receiver)
        if card is None and "." in receiver:
            card = workspace.class_card(receiver.rsplit(".", 1)[-1])
        if card is not None:
            candidates.append(card)
    return candidates


def resolve_call(receiver: str, method: str, index, workspace):
    """Three tiers, as ('declared'|'drift'|'unknown', entity|None,
    location|None):

    - declared: the receiver's class (or, receiver classless, some
      class in the workspace) declares the method — gd/hover target;
    - drift: the receiver correlates with a class that does NOT
      declare it — behaviour drifting from structure (warning);
    - unknown: no receiver class and no class anywhere declares it
      (information)."""
    candidates = _receiver_candidates(receiver, index, workspace)
    for entity in candidates:
        if method in entity.methods:
            return "declared", entity, entity.methods[method]
    for entity in candidates:
        if entity.kind in CLASS_KINDS:
            return "drift", entity, None
    if workspace is not None:
        for entity in workspace.method_declarations(method):
            return "declared", entity, entity.methods[method]
    return "unknown", None, None


def tier_lint(tier: str, entity, method: str, span: tuple) -> tuple | None:
    """One lint tuple for a resolved call tier, or None when declared."""
    if tier == "drift":
        return (*span, f"'{entity.id}' does not declare '{method}()'", "warning")
    if tier == "unknown":
        return (
            *span,
            f"no class in the workspace declares '{method}()'",
            "information",
        )
    return None


def label_call_lints(src: bytes, index: Index, workspace) -> list:
    """Drift lints over call-shaped relation labels."""
    found = []

    def walk(node: Node) -> None:
        label = node.child_by_field_name("label") if node.type == "relation" else None
        m = _CALL_SHAPE.match(node_text(src, label)) if label is not None else None
        receiver = _relation_receiver(src, node) if m is not None else None
        if receiver is not None:
            tier, entity, _loc = resolve_call(receiver, m.group(1), index, workspace)
            span = (
                label.start_point[0],
                label.start_point[1],
                label.end_point[0],
                label.end_point[1],
            )
            lint = tier_lint(tier, entity, m.group(1), span)
            if lint is not None:
                found.append(lint)
        for child in node.children:
            walk(child)

    walk(parse(src).root_node)
    return found
