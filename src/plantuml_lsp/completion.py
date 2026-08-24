"""Completion: contextual first, generic as the statement-head base.

Completion fires on half-written lines, where the CST is broken — so
the context is decided lexically over the line up to the cursor, and
the candidates come from the index: the receiver's methods after a
message colon, participants after an arrow, the lane's methods inside
an activity action, keywords only at statement heads, silence in free
label text.
"""

import re

from plantuml_lsp.index import Index, resolve_entity
from plantuml_lsp.workspace import CLASS_KINDS, WorkspaceIndex

KEYWORDS = (
    "class",
    "abstract class",
    "interface",
    "enum",
    "annotation",
    "exception",
    "metaclass",
    "protocol",
    "struct",
    "record",
    "dataclass",
    "participant",
    "actor",
    "boundary",
    "control",
    "entity",
    "database",
    "collections",
    "queue",
    "package",
    "namespace",
    "together",
    "note",
    "hide",
    "show",
    "remove",
    "restore",
    "alt",
    "opt",
    "loop",
    "par",
    "break",
    "critical",
    "group",
    "else",
    "end",
    "activate",
    "deactivate",
    "return",
    "create",
    "destroy",
    "autonumber",
    "title",
    "skinparam",
)

# (label, kind) — kind is an entity kind or "keyword"
CompletionTuple = tuple[str, str]

# (label, kind, detail) — detail carries the declared signature
ContextualTuple = tuple[str, str, str]


def collect_completions(index: Index) -> list[CompletionTuple]:
    items: list[CompletionTuple] = [
        (entity.id, entity.kind) for entity in index.entities.values()
    ]
    items.extend((keyword, "keyword") for keyword in KEYWORDS)
    return items


_HEAD = re.compile(r"^\s*\w*$")
_ACTION = re.compile(r"^\s*:\s*\w*$")
_KIND_HEAD = re.compile(
    r"^\s*(participant|actor|boundary|control|entity|database|"
    r"collections|queue)\s+\w*$"
)
_OPERATOR = re.compile(r"^[<>ox\[\]()?*+|\\/.#=-]+$")
_LANE = re.compile(r"^\s*\|(?:#[^|]*\|)?([^|]+)\|")


def _receiver_methods(
    receiver: str,
    index: Index,
    workspace: WorkspaceIndex | None,
) -> list[ContextualTuple]:
    entity = None
    resolved = resolve_entity(receiver, index.entities)
    if resolved is not None:
        entity = index.entities[resolved]
    if (entity is None or not entity.methods) and workspace is not None:
        card = workspace.class_card(receiver)
        if card is None and "." in receiver:
            card = workspace.class_card(receiver.rsplit(".", 1)[-1])
        if card is not None:
            entity = card
    if entity is None:
        return []
    return [
        (name, "method", text)
        for name, (_r, _s, _e, text) in sorted(entity.methods.items())
    ]


def _message_receiver(head: str) -> str | None:
    """The receiver of `A -> B` — the token the arrow points at."""
    tokens = head.split()
    for i, token in enumerate(tokens):
        if _OPERATOR.fullmatch(token) and ("-" in token or "." in token):
            if token.startswith("<"):
                return tokens[i - 1].strip('"') if i > 0 else None
            return tokens[i + 1].strip('"') if i + 1 < len(tokens) else None
    return None


def _active_lane(src: bytes, row: int) -> str | None:
    lines = src.decode(errors="replace").splitlines()
    for r in range(min(row, len(lines)) - 1, -1, -1):
        m = _LANE.match(lines[r])
        if m:
            return m.group(1).strip()
    return None


def _action_completions(
    src: bytes, row: int, index: Index, workspace: WorkspaceIndex | None
) -> list[ContextualTuple]:
    """:accion bajo un carril → métodos de la clase del carril."""
    lane = _active_lane(src, row)
    if lane is None:
        return []
    return _receiver_methods(lane, index, workspace)


def _head_completions(index: Index) -> list[ContextualTuple]:
    """Cabecera de statement → keywords + entidades del documento."""
    items: list[ContextualTuple] = [
        (e.id, e.kind, e.name) for e in index.entities.values()
    ]
    items.extend((k, "keyword", "") for k in KEYWORDS)
    return items


def _participant_completions(workspace: WorkspaceIndex) -> list[ContextualTuple]:
    """participant <cursor> → clases del workspace."""
    return [
        (e.id, e.kind, e.name)
        for e in workspace.entities()
        if e.kind in CLASS_KINDS
    ][:100]


def _label_completions(
    prefix: str, index: Index, workspace: WorkspaceIndex | None
) -> list[ContextualTuple]:
    """A -> B : <cursor> → métodos del receptor."""
    head, _, tail = prefix.rpartition(":")
    if re.fullmatch(r"\s*\w*", tail) and _message_receiver(head):
        return _receiver_methods(_message_receiver(head), index, workspace)
    return []


def _endpoint_completions(
    index: Index, workspace: WorkspaceIndex | None
) -> list[ContextualTuple]:
    """A -> <cursor> → participantes y entidades, sin keywords."""
    pool = list(index.entities.values())
    if workspace is not None:
        pool += [x for x in workspace.entities() if x.kind in CLASS_KINDS]
    seen = set()
    items = []
    for e in pool:
        if e.id not in seen:
            seen.add(e.id)
            items.append((e.id, e.kind, e.name))
    return items


def _after_operator(prefix: str) -> bool:
    return _message_receiver(prefix + " x") is not None or bool(
        prefix.rstrip() and _OPERATOR.fullmatch(prefix.split()[-1])
    )


def contextual_completions(
    src: bytes,
    row: int,
    col: int,
    index: Index,
    workspace: WorkspaceIndex | None = None,
) -> list[ContextualTuple]:
    lines = src.decode(errors="replace").splitlines()
    if row >= len(lines):
        return []
    prefix = lines[row][:col]

    if _ACTION.match(prefix):
        return _action_completions(src, row, index, workspace)
    if _HEAD.match(prefix):
        return _head_completions(index)
    if _KIND_HEAD.match(prefix) and workspace is not None:
        return _participant_completions(workspace)
    if ":" in prefix:
        return _label_completions(prefix, index, workspace)
    if _after_operator(prefix):
        return _endpoint_completions(index, workspace)
    return []
