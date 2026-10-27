"""Document links: include paths become clickable."""

from pathlib import Path

from plantuml_lsp.links import collect_links

__covers__ = (collect_links,)


class TestCollectLinks:
    def test_every_include_path_is_a_link_to_its_resolved_file(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "main.puml"
        src = b"@startuml\n!include lib/a.iuml\n  !includesub b.iuml!Sub\n@enduml\n"
        links = collect_links(str(doc), src)
        assert [(row, target) for row, _s, _e, target in links] == [
            (1, str((tmp_path / "lib/a.iuml").resolve())),
            (2, str((tmp_path / "b.iuml").resolve())),
        ]

    def test_the_span_covers_the_path_only(self, tmp_path: Path) -> None:
        ((row, scol, ecol, _t),) = collect_links(
            str(tmp_path / "d.puml"), b"!include x.iuml\n"
        )
        assert (row, scol, ecol) == (0, len("!include "), len("!include x.iuml"))
