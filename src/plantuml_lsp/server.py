"""pygls wiring: thin handlers over the pure feature modules."""

from lsprotocol import types
from plantuml_fmt.formatter import format_text
from pygls.lsp.server import LanguageServer

from plantuml_lsp.completion import collect_completions
from plantuml_lsp.diagnostics import collect_diagnostics
from plantuml_lsp.definitions import entity_definitions, resolve_definition
from plantuml_lsp.hover import hover_for
from plantuml_lsp.index import build_index, identifier_at, resolve_entity
from plantuml_lsp.links import collect_links
from plantuml_lsp.lints import collect_lints
from plantuml_lsp.rename import edits_from
from plantuml_lsp.symbols import collect_symbols
from plantuml_lsp.workspace import WorkspaceIndex

SYMBOL_KINDS = {
    "class": types.SymbolKind.Class,
    "interface": types.SymbolKind.Interface,
    "enum": types.SymbolKind.Enum,
    "namespace": types.SymbolKind.Namespace,
    "package": types.SymbolKind.Package,
    "participant": types.SymbolKind.Object,
}

server = LanguageServer("plantuml-lsp", "0.3.0")


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


_workspaces: dict[str, WorkspaceIndex] = {}


def _workspace_of(ls: LanguageServer, doc) -> WorkspaceIndex:
    import os
    root = getattr(ls.workspace, "root_path", None) or os.path.dirname(doc.path)
    ws = _workspaces.get(root)
    if ws is None:
        ws = _workspaces[root] = WorkspaceIndex(root)
    else:
        ws.refresh_if_stale()
    return ws


def _merged_occurrences(name: str, index, ws: WorkspaceIndex):
    seen = set()
    merged = []
    for occ in index.occurrences(name) + ws.occurrences(name):
        if occ not in seen:
            seen.add(occ)
            merged.append(occ)
    return merged


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
    # workspace drift: declared plain participants no class explains
    ws = _workspace_of(ls, doc)
    diags.extend(
        types.Diagnostic(
            range=_range(e.row, e.scol, e.row, e.ecol),
            message=(
                f"'{e.id}' no corresponde a ninguna clase del workspace"
            ),
            severity=types.DiagnosticSeverity.Information,
            source="plantuml-lsp",
        )
        for e in ws.unmatched_participants(doc.path)
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
    if resolved is not None:
        path, line = resolved
        return types.Location(
            uri=f"file://{path}",
            range=types.Range(
                start=types.Position(line=line, character=0),
                end=types.Position(line=line, character=0),
            ),
        )
    # not an include directive: jump to the entity's declaration
    doc2, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc2.source.encode(), params.position.line, params.position.character
    )
    if not name:
        return None
    locations = [
        types.Location(uri=f"file://{path}", range=_range(r, sc, r, ec))
        for path, r, sc, ec in entity_definitions(
            name, index, _workspace_of(ls, doc2)
        )
    ]
    if not locations:
        return None
    return locations[0] if len(locations) == 1 else locations


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
    text = hover_for(name, index, _workspace_of(ls, doc)) if name else None
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
    ws = _workspace_of(ls, doc)
    name = name and (resolve_entity(name, index.entities) or name)
    if not name or (name not in index.entities and not ws.declarations(name)):
        return None
    return [
        types.Location(uri=f"file://{path}", range=_range(row, scol, row, ecol))
        for path, row, scol, ecol in _merged_occurrences(name, index, ws)
    ]


@server.feature(types.TEXT_DOCUMENT_RENAME)
def rename(ls: LanguageServer, params: types.RenameParams):
    doc, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    ws = _workspace_of(ls, doc)
    name = name and (resolve_entity(name, index.entities) or name)
    if not name or (name not in index.entities and not ws.declarations(name)):
        return None
    read = lambda path: index.files.get(path) or ws.file_bytes(path)
    changes: dict[str, list[types.TextEdit]] = {}
    for path, row, scol, ecol, new_text in edits_from(
        _merged_occurrences(name, index, ws), params.new_name, read
    ):
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


@server.feature(types.WORKSPACE_SYMBOL)
def workspace_symbol(ls: LanguageServer, params: types.WorkspaceSymbolParams):
    if not _workspaces:
        return None
    hits = []
    for ws in _workspaces.values():
        ws.refresh_if_stale()
        hits.extend(ws.symbols(params.query))
    return [
        types.SymbolInformation(
            name=e.id,
            kind=SYMBOL_KINDS.get(e.kind, types.SymbolKind.Object),
            container_name=e.kind,
            location=types.Location(
                uri=f"file://{e.path}",
                range=_range(e.row, e.scol, e.row, e.ecol),
            ),
        )
        for e in hits[:200]
    ]


def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
