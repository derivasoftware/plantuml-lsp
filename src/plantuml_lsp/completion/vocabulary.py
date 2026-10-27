"""Completion's vocabulary: every indexed id with its kind, and the
statement keywords. The editor filters; this offers everything."""

from plantuml_lsp.index import Index

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


def collect_completions(index: Index) -> list[CompletionTuple]:
    items: list[CompletionTuple] = [
        (entity.id, entity.kind) for entity in index.entities.values()
    ]
    items.extend((keyword, "keyword") for keyword in KEYWORDS)
    return items
