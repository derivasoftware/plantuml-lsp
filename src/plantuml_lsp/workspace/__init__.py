"""The workspace index: every entity of every diagram under the root.
One file per class; the public surface is re-exported here so no importer
changes."""

from plantuml_lsp.workspace.WorkspaceIndex import CLASS_KINDS, WorkspaceIndex

__all__ = ["CLASS_KINDS", "WorkspaceIndex"]
