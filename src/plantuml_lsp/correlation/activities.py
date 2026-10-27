"""Activity actions against the methods of the class their swimlane names."""

from __future__ import annotations

from plantuml_lsp.correlation.messages import resolve_call, tier_lint
from plantuml_lsp.index import Index


def action_at(index, row: int):
    """(lane, method) when the row holds a call-shaped activity action."""
    for name, lane, arow, _scol, _ecol in index.actions:
        if arow == row:
            return lane, name
    return None


def action_call_lints(index: Index, workspace) -> list:
    """Drift lints over activity actions: the lane names the receiver."""
    found = []
    for name, lane, row, scol, ecol in index.actions:
        tier, entity, _loc = resolve_call(lane or "", name, index, workspace)
        lint = tier_lint(tier, entity, name, (row, scol, row, ecol))
        if lint is not None:
            found.append(lint)
    return found
