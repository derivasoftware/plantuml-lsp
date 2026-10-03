"""Integration tests: the functions the verifications register, which drive
the product at its boundary; the rest of tests/unit/test_server.py stays unit.
"""

import plantuml_lsp.server as server_module


def test_server_wires_all_features():
    fm = getattr(server_module.server, "feature_manager", None)
    if fm is None:
        fm = server_module.server.protocol.fm
    assert set(fm.features) == {
        "textDocument/didOpen",
        "textDocument/didChange",
        "textDocument/documentSymbol",
        "textDocument/definition",
        "textDocument/formatting",
        "textDocument/completion",
        "textDocument/hover",
        "textDocument/references",
        "textDocument/rename",
        "textDocument/documentLink",
        "workspace/symbol",
        "textDocument/codeAction",
    }
