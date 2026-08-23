"""Document links: `!include`/`!includesub` paths become clickable."""

import re
from pathlib import Path

_DIRECTIVE = re.compile(r"^(\s*!include(?:sub)?\s+)([^\s!]+)")

# (row, start_col, end_col, resolved_target_path)
LinkTuple = tuple[int, int, int, str]


def collect_links(doc_path: str, src: bytes) -> list[LinkTuple]:
    links: list[LinkTuple] = []
    for row, line in enumerate(src.decode(errors="replace").splitlines()):
        m = _DIRECTIVE.match(line)
        if m:
            target = (Path(doc_path).parent / m.group(2)).resolve()
            scol = len(m.group(1))
            links.append((row, scol, scol + len(m.group(2)), str(target)))
    return links
