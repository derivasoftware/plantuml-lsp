"""pygls wiring: thin handlers over the pure feature modules."""

from lsprotocol import types
from plantuml_fmt.formatter import format_text
from pygls.lsp.server import LanguageServer

import re as _re

from plantuml_lsp.actions import declare_entity, declare_method, fix_include_path
from plantuml_lsp.completion import contextual_completions
from plantuml_lsp.diagnostics import collect_diagnostics
from plantuml_lsp.correlation import (
    action_at,
    call_at,
    resolve_call,
    unmatched_participants,
)
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
    "information": types.DiagnosticSeverity.Information,
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
    # call-level drift: call-shaped labels whose receiver's class does
    # not declare the method
    ws = _workspace_of(ls, doc)
    from plantuml_lsp.lints import collect_call_lints

    diags.extend(
        types.Diagnostic(
            range=_range(sr, sc, er, ec),
            message=msg,
            severity=_SEVERITIES[severity],
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg, severity in collect_call_lints(src, index, ws)
    )
    # workspace drift: declared plain participants no class explains
    diags.extend(
        types.Diagnostic(
            range=_range(e.row, e.scol, e.row, e.ecol),
            message=(f"'{e.id}' no corresponde a ninguna clase del workspace"),
            severity=types.DiagnosticSeverity.Information,
            source="plantuml-lsp",
        )
        for e in unmatched_participants(ws, doc.path)
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
    # not an include directive: a call label resolves to the method
    doc2, index = _index_of(ls, params.text_document.uri)
    src2 = doc2.source.encode()
    call = call_at(src2, params.position.line, params.position.character) or action_at(
        index, params.position.line
    )
    if call is not None:
        tier, entity, loc = resolve_call(
            call[0], call[1], index, _workspace_of(ls, doc2)
        )
        if tier == "declared" and loc is not None:
            mrow, mscol, mecol, _text = loc
            return types.Location(
                uri=f"file://{entity.path}",
                range=_range(mrow, mscol, mrow, mecol),
            )
    name = identifier_at(src2, params.position.line, params.position.character)
    if not name:
        return None
    locations = [
        types.Location(uri=f"file://{path}", range=_range(r, sc, r, ec))
        for path, r, sc, ec in entity_definitions(name, index, _workspace_of(ls, doc2))
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


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=[":", ">", " ", "|"]),
)
def completion(ls: LanguageServer, params: types.CompletionParams):
    doc, index = _index_of(ls, params.text_document.uri)
    kind_map = {
        "keyword": types.CompletionItemKind.Keyword,
        "interface": types.CompletionItemKind.Interface,
        "enum": types.CompletionItemKind.Enum,
        "method": types.CompletionItemKind.Method,
    }
    items = contextual_completions(
        doc.source.encode(),
        params.position.line,
        params.position.character,
        index,
        _workspace_of(ls, doc),
    )
    if not items:
        return None
    return [
        types.CompletionItem(
            label=label,
            kind=kind_map.get(kind, types.CompletionItemKind.Class),
            detail=detail or kind,
        )
        for label, kind, detail in items
    ]


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams):
    doc, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    text = hover_for(name, index, _workspace_of(ls, doc)) if name else None
    if text is None:
        call = call_at(
            doc.source.encode(), params.position.line, params.position.character
        ) or action_at(index, params.position.line)
        if call is not None:
            tier, entity, loc = resolve_call(
                call[0], call[1], index, _workspace_of(ls, doc)
            )
            if tier == "declared" and loc is not None:
                _r, _s, _e, member_text = loc
                text = f"**{entity.kind}** `{entity.id}`\n\n```\n{member_text}\n```"
    if text is None:
        return None
    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=text)
    )


def _entity_reference_locations(name: str, index, ws) -> list:
    """Occurrence locations of an entity across the closure and workspace."""
    if name not in index.entities and not ws.declarations(name):
        return []
    return [
        types.Location(uri=f"file://{path}", range=_range(row, scol, row, ecol))
        for path, row, scol, ecol in _merged_occurrences(name, index, ws)
    ]


def _method_reference_locations(name: str, index, ws, results: list) -> None:
    """Extend results with a method's declarations and call sites."""
    is_method = any(
        name in e.methods for e in index.entities.values()
    ) or ws.method_declarations(name)
    if not is_method:
        return
    seen = {
        (loc.uri, loc.range.start.line, loc.range.start.character) for loc in results
    }

    def add(uri: str, row: int, scol: int, ecol: int) -> None:
        key = (uri, row, scol)
        if key not in seen:
            seen.add(key)
            results.append(types.Location(uri=uri, range=_range(row, scol, row, ecol)))

    for entity in ws.method_declarations(name):
        row, scol, ecol, _txt = entity.methods[name]
        add(f"file://{entity.path}", row, scol, ecol)
    for path, row, scol, ecol in ws.call_sites(name):
        add(f"file://{path}", row, scol, ecol)


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def references(ls: LanguageServer, params: types.ReferenceParams):
    doc, index = _index_of(ls, params.text_document.uri)
    name = identifier_at(
        doc.source.encode(), params.position.line, params.position.character
    )
    ws = _workspace_of(ls, doc)
    name = name and (resolve_entity(name, index.entities) or name)
    if not name:
        return None
    results = _entity_reference_locations(name, index, ws)
    # a method name: add its call sites (sequence labels and activity
    # actions) and its declarations across the workspace
    _method_reference_locations(name, index, ws, results)
    return results or None


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

    def read(path: str) -> bytes | None:
        return index.files.get(path) or ws.file_bytes(path)

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


_UNKNOWN_MSG = _re.compile(r"no declaration for '([\w.]+)'")
_INCLUDE_MSG = _re.compile(r"include target not found: (.+)$")
_DRIFT_MSG = _re.compile(r"'([\w.]+)' does not declare '(\w+)\(\)'")


@server.feature(types.TEXT_DOCUMENT_CODE_ACTION)
def code_action(ls: LanguageServer, params: types.CodeActionParams):
    doc, index = _index_of(ls, params.text_document.uri)
    ws = _workspace_of(ls, doc)
    src = doc.source.encode()
    lines = doc.source.splitlines()
    fixes = []
    for diag in params.context.diagnostics:
        msg = diag.message
        m = _UNKNOWN_MSG.search(msg)
        if m:
            fixes.append((declare_entity(m.group(1), doc.path, src), diag))
            continue
        m = _INCLUDE_MSG.search(msg)
        if m:
            row = diag.range.start.line
            if row < len(lines):
                fixes.append((fix_include_path(row, lines[row], doc.path, ws), diag))
            continue
        m = _DRIFT_MSG.search(msg)
        if m:
            entity = ws.class_card(m.group(1))
            if entity is not None:
                fixes.append((declare_method(m.group(2), entity, ws), diag))
    actions = []
    for fix, diag in fixes:
        if fix is None:
            continue
        title, path, row, scol, ecol, new_text = fix
        actions.append(
            types.CodeAction(
                title=title,
                kind=types.CodeActionKind.QuickFix,
                diagnostics=[diag],
                edit=types.WorkspaceEdit(
                    changes={
                        f"file://{path}": [
                            types.TextEdit(
                                range=_range(row, scol, row, ecol), new_text=new_text
                            )
                        ],
                    }
                ),
            )
        )
    return actions or None


def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
