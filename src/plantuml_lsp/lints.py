"""Semantic lints — what neither the parser nor the official renderer
tells you:

- a relation endpoint no declaration in the closure explains (class
  diagrams only: sequence diagrams create participants implicitly, so
  there the same shape is idiomatic and stays quiet);
- an id declared twice;
- an include directive whose target file or fragment does not exist.
"""

import re
from pathlib import Path

from tree_sitter import Node

from plantuml_lsp.correlation import action_call_lints, label_call_lints
from plantuml_lsp.index import Index
from plantuml_lsp.parsing import node_text, parse

_INCLUDESUB = re.compile(r"^\s*!includesub\s+([^\s!]+)!(\w+)\s*$")
_INCLUDE = re.compile(r"^\s*!include\s+(\S+)\s*$")
_STARTSUB = re.compile(r"^\s*!startsub\s+(\w+)\s*$")

# (row, start_col, end_col, message, severity) — severity: "warning"|"error"
LintTuple = tuple[int, int, int, int, str, str]


def collect_call_lints(src: bytes, index: Index, workspace) -> list[LintTuple]:
    """Call-shaped message labels whose receiver correlates with a
    class that does not declare the method — behaviour drifting from
    structure. Free-text labels and classless receivers stay silent."""
    return label_call_lints(src, index, workspace) + action_call_lints(index, workspace)


def collect_lints(doc_path: str, src: bytes, index: Index) -> list[LintTuple]:
    lints: list[LintTuple] = []
    tree = parse(src)
    if _is_class_diagram(tree.root_node):
        _lint_unknown_endpoints(tree.root_node, src, index, lints)
    _lint_duplicates(doc_path, index, lints)
    _lint_includes(doc_path, src, lints)
    return lints


def _is_class_diagram(root: Node) -> bool:
    has_class = False

    def walk(node: Node) -> bool:
        nonlocal has_class
        if node.type in ("participant_declaration", "frame_block"):
            return True
        if node.type in (
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "entity_declaration",
        ):
            has_class = True
        return any(walk(child) for child in node.children)

    sequence = walk(root)
    return has_class and not sequence


def _lint_unknown_endpoints(
    node: Node,
    src: bytes,
    index: Index,
    lints: list[LintTuple],
) -> None:
    if node.type == "relation":
        for field_name in ("left", "right"):
            end = node.child_by_field_name(field_name)
            if end is None or end.type not in ("identifier", "string"):
                continue
            name = node_text(src, end).strip('"')
            short = name.rsplit(".", 1)[-1]
            if name not in index.entities and short not in index.entities:
                lints.append(
                    (
                        end.start_point[0],
                        end.start_point[1],
                        end.end_point[0],
                        end.end_point[1],
                        f"no declaration for '{name}' in this document or its includes",
                        "warning",
                    )
                )
    for child in node.children:
        _lint_unknown_endpoints(child, src, index, lints)


def _lint_duplicates(doc_path: str, index: Index, lints: list[LintTuple]) -> None:
    resolved = str(Path(doc_path).resolve())
    for dup in index.duplicates:
        if dup.path != resolved:
            continue
        first = index.entities[dup.id]
        lints.append(
            (
                dup.row,
                dup.scol,
                dup.row,
                dup.ecol,
                f"'{dup.id}' is already declared as {first.kind} "
                f"({Path(first.path).name}:{first.row + 1})",
                "warning",
            )
        )


def _lint_includes(doc_path: str, src: bytes, lints: list[LintTuple]) -> None:
    base = Path(doc_path).parent
    for row, line in enumerate(src.decode(errors="replace").splitlines()):
        m = _INCLUDESUB.match(line)
        if m:
            target = (base / m.group(1)).resolve()
            if not target.is_file():
                lints.append(
                    (
                        row,
                        0,
                        row,
                        len(line),
                        f"include target not found: {m.group(1)}",
                        "error",
                    )
                )
            elif not _has_startsub(target, m.group(2)):
                lints.append(
                    (
                        row,
                        0,
                        row,
                        len(line),
                        f"fragment '{m.group(2)}' not found in {m.group(1)}",
                        "error",
                    )
                )
            continue
        m = _INCLUDE.match(line)
        if m and not (base / m.group(1)).resolve().is_file():
            lints.append(
                (
                    row,
                    0,
                    row,
                    len(line),
                    f"include target not found: {m.group(1)}",
                    "error",
                )
            )


def _has_startsub(target: Path, sub_name: str) -> bool:
    for line in target.read_text(errors="replace").splitlines():
        m = _STARTSUB.match(line)
        if m and m.group(1) == sub_name:
            return True
    return False
