"""A double of the pygls server the handlers talk to: documents by uri,
the workspace root, and the diagnostics they publish."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lsprotocol import types


@dataclass
class FakeDocument:
    path: str
    source: str


@dataclass
class FakeWorkspace:
    root_path: str
    documents: dict[str, FakeDocument] = field(default_factory=dict)

    def get_text_document(self, uri: str) -> FakeDocument:
        return self.documents[uri]


@dataclass
class FakeServer:
    workspace: FakeWorkspace
    published: list[types.PublishDiagnosticsParams] = field(default_factory=list)

    def text_document_publish_diagnostics(
        self, params: types.PublishDiagnosticsParams
    ) -> None:
        self.published.append(params)


def open_workspace(
    root: Path, files: dict[str, str]
) -> tuple[FakeServer, dict[str, str]]:
    """Write the files under root and open each as a document; returns the
    server double and the uri of each file by name."""
    ws = FakeWorkspace(root_path=str(root))
    uris = {}
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        uri = f"file://{path}"
        ws.documents[uri] = FakeDocument(path=str(path), source=text)
        uris[name] = uri
    return FakeServer(workspace=ws), uris


def doc_id(uri: str) -> types.TextDocumentIdentifier:
    return types.TextDocumentIdentifier(uri=uri)


def at(line: int, character: int) -> types.Position:
    return types.Position(line=line, character=character)
