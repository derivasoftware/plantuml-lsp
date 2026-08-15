"""pygls wiring: thin handlers over the pure feature modules."""

from lsprotocol import types
from plantuml_fmt.formatter import format_text
from pygls.lsp.server import LanguageServer

from plantuml_lsp.diagnostics import collect_diagnostics
from plantuml_lsp.definitions import resolve_definition
from plantuml_lsp.symbols import collect_symbols

SYMBOL_KINDS = {
    "class": types.SymbolKind.Class,
    "interface": types.SymbolKind.Interface,
    "enum": types.SymbolKind.Enum,
    "namespace": types.SymbolKind.Namespace,
    "package": types.SymbolKind.Package,
    "participant": types.SymbolKind.Object,
}

server = LanguageServer("plantuml-lsp", "0.1.0")


def _publish(ls: LanguageServer, uri: str) -> None:
    doc = ls.workspace.get_text_document(uri)
    diags = [
        types.Diagnostic(
            range=types.Range(
                start=types.Position(line=sr, character=sc),
                end=types.Position(line=er, character=ec),
            ),
            message=msg,
            severity=types.DiagnosticSeverity.Error,
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg in collect_diagnostics(doc.source.encode())
    ]
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


def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
