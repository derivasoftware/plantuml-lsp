"""An entity the index knows: a declaration with its place, members and methods."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    path: str
    row: int
    scol: int
    ecol: int
    members: list[str] = field(default_factory=list)
    # method name -> (row, scol, ecol, member line text)
    methods: dict[str, tuple[int, int, int, str]] = field(default_factory=dict)
    # a high-level box: a stereotyped namespace or package, kind = stereotype
    box: bool = False
