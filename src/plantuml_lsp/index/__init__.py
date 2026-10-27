"""The symbol index: every entity visible from a document, its own
declarations plus the transitive include closure. One file per class;
the public surface is re-exported here so no importer changes."""

from plantuml_lsp.index.cursor import identifier_at, resolve_entity, word_at
from plantuml_lsp.index.Entity import Entity
from plantuml_lsp.index.Index import Index, build_index, walk_tree
from plantuml_lsp.index.occurrences import scan_occurrences

__all__ = [
    "Entity",
    "Index",
    "build_index",
    "identifier_at",
    "resolve_entity",
    "scan_occurrences",
    "walk_tree",
    "word_at",
]
