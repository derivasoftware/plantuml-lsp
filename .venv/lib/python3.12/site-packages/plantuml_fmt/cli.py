"""Command-line interface: plantuml-fmt [--check] <paths>."""

import argparse
import pathlib
import sys
from collections.abc import Iterable, Iterator

from plantuml_fmt.formatter import format_bytes

SUFFIXES = {".puml", ".plantuml", ".iuml", ".wsd"}


def iter_files(paths: Iterable[str]) -> Iterator[pathlib.Path]:
    for raw in paths:
        path = pathlib.Path(raw)
        if path.is_dir():
            yield from sorted(
                p for p in path.rglob("*") if p.suffix in SUFFIXES and p.is_file()
            )
        else:
            yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plantuml-fmt",
        description="Format PlantUML sources into the canonical style.",
    )
    parser.add_argument("paths", nargs="+", help="files or directories to format")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 listing files that would change",
    )
    args = parser.parse_args(argv)

    changed = []
    for path in iter_files(args.paths):
        source = path.read_bytes()
        formatted = format_bytes(source)
        if formatted != source:
            changed.append(path)
            if not args.check:
                path.write_bytes(formatted)
    if args.check and changed:
        for path in changed:
            print(path)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
