"""Rename: rewrite every occurrence of an entity id across the closure.

Occurrences come from the index's CST scan (identifier and quoted-name
tokens only), so labels, comments and note bodies are never touched.
Quoted occurrences keep their quotes: the edit replaces the inner text.
"""

from plantuml_lsp.index import Index

# (path, row, start_col, end_col, new_text)
EditTuple = tuple[str, int, int, int, str]


def rename_edits(entity_id: str, new_name: str, index: Index) -> list[EditTuple]:
    edits: list[EditTuple] = []
    for path, row, scol, ecol in index.occurrences(entity_id):
        src = index.files[path]
        line = src.decode(errors="replace").splitlines()[row]
        token = line[scol:ecol]
        if token.startswith('"') and token.endswith('"'):
            edits.append((path, row, scol + 1, ecol - 1, new_name))
        else:
            edits.append((path, row, scol, ecol, new_name))
    return edits
