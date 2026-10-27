"""Completion: the vocabulary, and completion by cursor context.
The public surface is re-exported here so no importer changes."""

from plantuml_lsp.completion.context import contextual_completions
from plantuml_lsp.completion.vocabulary import KEYWORDS, collect_completions

__all__ = ["KEYWORDS", "collect_completions", "contextual_completions"]
