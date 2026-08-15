"""Shared parser access: one grammar instance per process."""

import tree_sitter_plantuml
from tree_sitter import Language, Node, Parser, Tree

_parser: Parser | None = None


def get_parser() -> Parser:
    global _parser
    if _parser is None:
        _parser = Parser(Language(tree_sitter_plantuml.language()))
    return _parser


def parse(src: bytes) -> Tree:
    return get_parser().parse(src)


def node_text(src: bytes, node: Node) -> str:
    return src[node.start_byte:node.end_byte].decode(errors="replace")
