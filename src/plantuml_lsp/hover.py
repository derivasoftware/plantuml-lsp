"""Hover: a markdown summary of the entity under the cursor."""

from pathlib import Path

from plantuml_lsp.index import Index


def hover_for(entity_id: str, index: Index) -> str | None:
    entity = index.entities.get(entity_id)
    if entity is None:
        return None
    lines = [f"**{entity.kind}** `{entity.id}`"]
    if entity.name != entity.id:
        lines.append(f'declared as `"{entity.name}"`')
    if entity.members:
        lines.append("")
        lines.append("```")
        lines.extend(entity.members)
        lines.append("```")
    relations = index.relations.get(entity_id, [])
    if relations:
        lines.append("")
        lines.extend(f"- `{r}`" for r in relations[:8])
        if len(relations) > 8:
            lines.append(f"- … {len(relations) - 8} more")
    lines.append("")
    lines.append(f"*{Path(entity.path).name}:{entity.row + 1}*")
    return "\n".join(lines)
