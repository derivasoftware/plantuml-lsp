"""Smoke test: the wiring module imports and registers every feature.

This is the test that was missing when pygls 2 broke the import path —
the pure feature modules were covered but nothing ever imported the
server itself.
"""

import plantuml_lsp.server as server_module


def test_entrypoint_exists():
    assert callable(server_module.main)
