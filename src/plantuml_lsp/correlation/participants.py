"""Sequence participants against the workspace's classes: a declared,
class-cased plain participant no structural declaration explains."""

from __future__ import annotations

from plantuml_lsp.index import Entity
from plantuml_lsp.workspace import WorkspaceIndex


def unmatched_participants(workspace: WorkspaceIndex, doc_path: str) -> list[Entity]:
    """Declared plain participants of one document with no structural
    declaration anywhere in the workspace. Actors and the other
    participant kinds are legitimately abstract and stay exempt."""
    return [
        e
        for e in workspace.entities_of(doc_path)
        if e.kind == "participant"
        # class-cased names only: lowercase participants (cli,
        # daemon...) are conceptual actors, not missing classes
        and e.name[:1].isupper()
        and workspace.class_card(e.id) is None
        and workspace.class_card(e.name) is None
        # a participant naming a box of the high-level design is explained
        and workspace.box_card(e.id) is None
        and workspace.box_card(e.name) is None
    ]
