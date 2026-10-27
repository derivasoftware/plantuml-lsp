"""Diagnostics, published on open and change: parse errors, semantic lints, drifting calls and unexplained participants."""

from __future__ import annotations

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from plantuml_lsp.correlation import unmatched_participants
from plantuml_lsp.diagnostics import collect_diagnostics
from plantuml_lsp.index import build_index
from plantuml_lsp.lints import collect_call_lints, collect_lints
from plantuml_lsp.server.core import SEVERITIES, range_of, server, workspace_of


def publish(ls: LanguageServer, uri: str) -> None:
    doc = ls.workspace.get_text_document(uri)
    src = doc.source.encode()
    diags = [
        types.Diagnostic(
            range=range_of(sr, sc, er, ec),
            message=msg,
            severity=types.DiagnosticSeverity.Error,
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg in collect_diagnostics(src)
    ]
    index = build_index(doc.path, src)
    diags.extend(
        types.Diagnostic(
            range=range_of(sr, sc, er, ec),
            message=msg,
            severity=SEVERITIES[severity],
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg, severity in collect_lints(doc.path, src, index)
    )
    # call-level drift: call-shaped labels whose receiver's class does
    # not declare the method
    ws = workspace_of(ls, doc)
    diags.extend(
        types.Diagnostic(
            range=range_of(sr, sc, er, ec),
            message=msg,
            severity=SEVERITIES[severity],
            source="plantuml-lsp",
        )
        for sr, sc, er, ec, msg, severity in collect_call_lints(src, index, ws)
    )
    # workspace drift: declared plain participants no class explains
    diags.extend(
        types.Diagnostic(
            range=range_of(e.row, e.scol, e.row, e.ecol),
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
    publish(ls, params.text_document.uri)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    publish(ls, params.text_document.uri)
