"""Quick fixes for the lints, one key each."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

import re as _re

from plantuml_lsp.actions import declare_entity, declare_method, fix_include_path
from plantuml_lsp.server.core import index_of, range_of, server, workspace_of

_UNKNOWN_MSG = _re.compile(r"no declaration for '([\w.]+)'")
_INCLUDE_MSG = _re.compile(r"include target not found: (.+)$")
_DRIFT_MSG = _re.compile(r"'([\w.]+)' does not declare '(\w+)\(\)'")


@server.feature(types.TEXT_DOCUMENT_CODE_ACTION)
def code_action(ls: LanguageServer, params: types.CodeActionParams):
    doc, index = index_of(ls, params.text_document.uri)
    ws = workspace_of(ls, doc)
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
                                range=range_of(row, scol, row, ecol), new_text=new_text
                            )
                        ],
                    }
                ),
            )
        )
    return actions or None
