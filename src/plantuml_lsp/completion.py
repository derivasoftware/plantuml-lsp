"""Completion: every entity the index knows plus statement keywords.

The server offers the full set; the editor filters by prefix — no
cursor-context guessing, which keeps the feature honest and fast.
"""

from plantuml_lsp.index import Index

KEYWORDS = (
    "class", "abstract class", "interface", "enum",
    "annotation", "exception", "metaclass", "protocol",
    "struct", "record", "dataclass",
    "participant", "actor", "boundary", "control", "entity",
    "database", "collections", "queue",
    "package", "namespace", "together",
    "note", "hide", "show", "remove", "restore",
    "alt", "opt", "loop", "par", "break", "critical", "group", "else", "end",
    "activate", "deactivate", "return", "create", "destroy",
    "autonumber", "title", "skinparam",
)

# (label, kind) — kind is an entity kind or "keyword"
CompletionTuple = tuple[str, str]


def collect_completions(index: Index) -> list[CompletionTuple]:
    items: list[CompletionTuple] = [
        (entity.id, entity.kind) for entity in index.entities.values()
    ]
    items.extend((keyword, "keyword") for keyword in KEYWORDS)
    return items
