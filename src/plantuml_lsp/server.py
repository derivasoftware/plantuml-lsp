"""pygls wiring: thin handlers over the pure feature modules."""

from lsprotocol import types
from plantuml_fmt.formatter import format_text
from pygls.lsp.server import LanguageServer

from plantuml_lsp.completion import collect_completions
from plantuml_lsp.diagnostics import collect_diagnostics
from plantuml_lsp.definitions import resolve_definition
from plantuml_lsp.hover import hover_for
from plantuml_lsp.index import build_index, identifier_at
from plantuml_lsp.links import collect_links
from plantuml_lsp.lints import collect_lints
from plantuml_lsp.rename import rename_edits
from plantuml_lsp.symbols import collect_symbols

SYMBOL_KINDS = {
    "class": types.SymbolKind.Class,
    "interface": types.SymbolKind.Interface,
    "enum": types.SymbolKind.Enum,
    "namespace": types.SymbolKind.Namespace,
    "package": types.SymbolKind.Package,
    "participant": types.SymbolKind.Object,
}

server = LanguageServer("plantuml-lsp", "0.2.0")


_SEVERITIES = {
    "error": types.DiagnosticSeverity.Error,
    "warning": types.DiagnosticSeverity.Warning,
}


def _range(sr: int, sc: int, er: int, ec: int) -> types.Range:
    return types.Range(
        start=types.Position(line=sr, character=sc),
        end=types.Position(line=er, character=ec),
    )


def _index_of(ls: LanguageServer, uri: str):
    doc = ls.workspace.get_text_document(uri)
    return doc, build_index(doc.path, doc.source.encode())


def _publish(ls: LanguageServer, uri: str) -> None:
    doc = ls.workspace.get_text_document(uri)
    src = doc.source.encode()
    diags = [
        types.Diagnostic(
            range=_range(sr, sc, er, ec),
            message=msg,
            severity=types.DiagnosticSeverity.Error,
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg in collect_diagnostics(src)
    ]
    index = build_index(doc.path, src)
    diags.extend(
        types.Diagnostic(
            range=_range(sr, sc, er, ec),
            message=msg,
            severity=_SEVERITIES[severity],
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg, severity in collect_lints(doc.path, src, index)
    )
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(uri=uri, diagnostics=diags)
    )


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    _publish(ls, params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    _publish(ls, params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: LanguageServer, params: types.DocumentSymbolParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return [
        types.SymbolInformation(
            name=name,
            kind=SYMBOL_KINDS.get(kind, types.SymbolKind.Object),
            location=types.Location(
                uri=params.text_document.uri,
                range=types.Range(
                    start=types.Position(line=sr, character=sc),
                    end=types.Position(line=er, character=ec),
                ),
            ),
        )
        for name, kind, sr, sc, er, ec in collect_symbols(doc.source.encode())
    ]


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(ls: LanguageServer, params: types.DefinitionParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    lines = doc.source.splitlines()
    row = params.position.line
    if row >= len(lines):
        return None
    resolved = resolve_definition(doc.path, lines[row])
    if resolved is None:
        return None
    path, line = resolved
    return types.Location(
        uri=f"file://{path}",
        range=types.Range(
            start=types.Position(line=line, character=0),
            end=types.Position(line=line, character=0),
        ),
    )


@server.feature(types.TEXT_DOCUMENT_FORMATTING)
def formatting(ls: LanguageServer, params: types.DocumentFormattingParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    formatted = format_text(doc.source)
    if formatted == doc.source:
        return []
    lines = doc.source.splitlines(keepends=True)
    return [
        types.TextEdit(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=len(lines), character=0),
            ),
            new_text=formatted,
        )
    ]


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: types.CompletionParams):
    _doc, index = _index_of(ls, params.text_document.uri)
    kind_map = {"keyword": types.CompletionItemKind.Keyword,
                "interface": types.CompletionItemKind.Interface,
                "enum": types.CompletionItemKind.Enum}
    return [
        types.CompletionItem(
            label=label,
            kind=kind_map.get(kind, types.CompletionItemKind.Class),
            detail=kind,
        )
        for label, kind in collect_completions(index)
    ]


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams):
    doc, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    text = hover_for(name, index) if name else None
    if text is None:
        return None
    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=text)
    )


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def references(ls: LanguageServer, params: types.ReferenceParams):
    doc, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    if not name or name not in index.entities:
        return None
    return [
        types.Location(uri=f"file://{path}", range=_range(row, scol, row, ecol))
        for path, row, scol, ecol in index.occurrences(name)
    ]


@server.feature(types.TEXT_DOCUMENT_RENAME)
def rename(ls: LanguageServer, params: types.RenameParams):
    doc, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    if not name or name not in index.entities:
        return None
    changes: dict[str, list[types.TextEdit]] = {}
    for path, row, scol, ecol, new_text in rename_edits(name, params.new_name, index):
        changes.setdefault(f"file://{path}", []).append(
            types.TextEdit(range=_range(row, scol, row, ecol), new_text=new_text)
        )
    return types.WorkspaceEdit(changes=changes)


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_LINK)
def document_link(ls: LanguageServer, params: types.DocumentLinkParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    return [
        types.DocumentLink(
            range=_range(row, scol, row, ecol), target=f"file://{target}"
        )
        for row, scol, ecol, target in collect_links(doc.path, doc.source.encode())
    ]


def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
