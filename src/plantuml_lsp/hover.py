"""Hover: a markdown summary of the entity under the cursor. With a
workspace index at hand, a sequence participant also shows the card of
the class it choreographs — the class↔sequence correlation."""

from pathlib import Path

from plantuml_lsp.index import Entity, Index, resolve_entity
from plantuml_lsp.workspace import CLASS_KINDS, WorkspaceIndex


def _card(entity: Entity) -> list[str]:
    lines = [f"**{entity.kind}** `{entity.id}`"]
    if entity.name != entity.id:
        lines.append(f'declared as `"{entity.name}"`')
    if entity.members:
        lines.append("")
        lines.append("```")
        lines.extend(entity.members)
        lines.append("```")
    lines.append("")
    lines.append(f"*{Path(entity.path).name}:{entity.row + 1}*")
    return lines


def _workspace_card(entity_id: str, workspace: WorkspaceIndex | None):
    """The workspace class card a name (or its qualified tail) denotes."""
    if workspace is None:
        return None
    card = workspace.class_card(entity_id)
    if card is None and "." in entity_id:
        card = workspace.class_card(entity_id.rsplit(".", 1)[-1])
    return card


def _participant_enrichment(
    entity, index: Index, workspace: WorkspaceIndex | None
) -> str | None:
    """A classless participant's hover, enriched with its class card."""
    if workspace is None or entity.kind in CLASS_KINDS or entity.members:
        return None
    card = workspace.class_card(entity.id) or workspace.class_card(entity.name)
    if card is None:
        return None
    return _hover_body(entity, index) + "\n\n---\n\n" + "\n".join(_card(card))


def hover_for(
    entity_id: str,
    index: Index,
    workspace: WorkspaceIndex | None = None,
) -> str | None:
    resolved = resolve_entity(entity_id, index.entities)
    entity = index.entities.get(resolved) if resolved else None
    if entity is None:
        card = _workspace_card(entity_id, workspace)
        return "\n".join(_card(card)) if card is not None else None
    enriched = _participant_enrichment(entity, index, workspace)
    if enriched is not None:
        return enriched
    return _hover_body(entity, index)


def _hover_body(entity: Entity, index: Index) -> str:
    lines = [f"**{entity.kind}** `{entity.id}`"]
    if entity.name != entity.id:
        lines.append(f'declared as `"{entity.name}"`')
    if entity.members:
        lines.append("")
        lines.append("```")
        lines.extend(entity.members)
        lines.append("```")
    relations = index.relations.get(entity.id, [])
    if relations:
        lines.append("")
        lines.extend(f"- `{r}`" for r in relations[:8])
        if len(relations) > 8:
            lines.append(f"- … {len(relations) - 8} more")
    lines.append("")
    lines.append(f"*{Path(entity.path).name}:{entity.row + 1}*")
    return "\n".join(lines)
