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


def hover_for(
    entity_id: str, index: Index, workspace: WorkspaceIndex | None = None,
) -> str | None:
    resolved = resolve_entity(entity_id, index.entities)
    entity = index.entities.get(resolved) if resolved else None
    if entity is None:
        if workspace is None:
            return None
        card = workspace.class_card(entity_id)
        if card is None and "." in entity_id:
            card = workspace.class_card(entity_id.rsplit(".", 1)[-1])
        return "\n".join(_card(card)) if card is not None else None
    if (
        workspace is not None
        and entity.kind not in CLASS_KINDS
        and not entity.members
    ):
        card = workspace.class_card(entity.id) or workspace.class_card(entity.name)
        if card is not None:
            local = _hover_body(entity, index)
            return local + "\n\n---\n\n" + "\n".join(_card(card))
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
