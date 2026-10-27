"""Message labels against the receiver's declared methods."""

from pathlib import Path

from plantuml_lsp.correlation.messages import (
    call_at,
    label_call_lints,
    resolve_call,
    tier_lint,
)
from plantuml_lsp.index import build_index
from plantuml_lsp.workspace import WorkspaceIndex

__covers__ = (call_at, resolve_call, tier_lint, label_call_lints)

CLASSES = "@startuml\nclass Cafetera {\n  +preparar() : Taza\n}\n@enduml\n"
SEQ = "@startuml\nparticipant Cafetera\nCafetera -> Cafetera : preparar(leche)\nCafetera -> Cafetera : moler()\n@enduml\n"


def _setup(tmp_path: Path):
    (tmp_path / "c.puml").write_text(CLASSES)
    doc = tmp_path / "s.puml"
    doc.write_text(SEQ)
    ws = WorkspaceIndex(str(tmp_path))
    ws.refresh()
    return build_index(str(doc), SEQ.encode()), ws


class TestCallAt:
    def test_reads_receiver_and_method_on_a_call_shaped_label(self) -> None:
        assert call_at(SEQ.encode(), 2, len("Cafetera -> Cafetera : pre")) == (
            "Cafetera",
            "preparar",
        )

    def test_is_none_off_a_label(self) -> None:
        assert call_at(SEQ.encode(), 1, 3) is None


class TestResolveCall:
    def test_declared_drift_and_unknown(self, tmp_path: Path) -> None:
        index, ws = _setup(tmp_path)
        assert resolve_call("Cafetera", "preparar", index, ws)[0] == "declared"
        assert resolve_call("Cafetera", "moler", index, ws)[0] == "drift"
        assert resolve_call("Nadie", "volar", index, ws)[0] == "unknown"


class TestTierLint:
    def test_drift_warns_unknown_informs_declared_is_silent(self) -> None:
        class E:
            id = "Cafetera"

        assert tier_lint("drift", E, "moler", (1, 2, 1, 7))[-1] == "warning"
        assert tier_lint("unknown", None, "volar", (1, 2, 1, 7))[-1] == "information"
        assert tier_lint("declared", E, "preparar", (1, 2, 1, 7)) is None


class TestLabelCallLints:
    def test_only_the_drifting_label_is_linted(self, tmp_path: Path) -> None:
        index, ws = _setup(tmp_path)
        messages = [lint[4] for lint in label_call_lints(SEQ.encode(), index, ws)]
        assert any("moler" in m for m in messages) and not any(
            "preparar" in m for m in messages
        )
