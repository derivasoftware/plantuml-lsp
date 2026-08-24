"""Go-to-definition across the preprocessor include directives.

`!includesub path!NAME` on the cursor line resolves to the `!startsub
NAME` line of the referenced file; `!include path` resolves to the top
of the referenced file. Paths resolve relative to the requesting
document, matching PlantUML's own preprocessor semantics.
"""

import re
from pathlib import Path

_INCLUDESUB = re.compile(r"^\s*!includesub\s+([^\s!]+)!(\w+)\s*$")
_INCLUDE = re.compile(r"^\s*!include\s+(\S+)\s*$")
_STARTSUB = re.compile(r"^\s*!startsub\s+(\w+)\s*$")

# (target_path, line)
DefinitionTuple = tuple[str, int]

# (path, row, start_col, end_col)
EntityLocation = tuple[str, int, int, int]


def entity_definitions(name, index, workspace) -> list[EntityLocation]:
    """Declarations a name (qualified tails included) resolves to —
    the document closure first, then the whole workspace."""
    from plantuml_lsp.index import resolve_entity

    names = [name]
    if "." in name:
        names.append(name.rsplit(".", 1)[-1])
    found: list[EntityLocation] = []
    seen: set[EntityLocation] = set()
    resolved = resolve_entity(name, index.entities)
    if resolved is not None:
        e = index.entities[resolved]
        loc = (e.path, e.row, e.scol, e.ecol)
        seen.add(loc)
        found.append(loc)
    if workspace is not None:
        for candidate in names:
            for e in workspace.declarations(candidate):
                loc = (e.path, e.row, e.scol, e.ecol)
                if loc not in seen:
                    seen.add(loc)
                    found.append(loc)
    return found


def resolve_definition(doc_path: str, line_text: str) -> DefinitionTuple | None:
    m = _INCLUDESUB.match(line_text)
    if m:
        target = (Path(doc_path).parent / m.group(1)).resolve()
        return _find_startsub(target, m.group(2))
    m = _INCLUDE.match(line_text)
    if m:
        target = (Path(doc_path).parent / m.group(1)).resolve()
        return (str(target), 0) if target.is_file() else None
    return None


def _find_startsub(target: Path, sub_name: str) -> DefinitionTuple | None:
    if not target.is_file():
        return None
    for lineno, line in enumerate(target.read_text(errors="replace").splitlines()):
        m = _STARTSUB.match(line)
        if m and m.group(1) == sub_name:
            return (str(target), lineno)
    return None
