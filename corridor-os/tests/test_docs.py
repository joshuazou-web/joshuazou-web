"""The documents that must not drift from the code they describe."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from corridoros.core.authority import AI_ALLOWED, CONSEQUENTIAL_ACTIONS
from corridoros.risk.rules import RULES
from corridoros.risk.typologies import TYPOLOGIES

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_the_catalogue_is_the_generator_output():
    """Regenerating it must produce exactly what is committed."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_catalogue import render

    assert (DOCS / "AML_RULE_CATALOG.md").read_text(encoding="utf-8") == render(), (
        "docs/AML_RULE_CATALOG.md is stale — run python scripts/generate_catalogue.py"
    )


def test_every_rule_and_typology_is_documented():
    text = (DOCS / "AML_RULE_CATALOG.md").read_text(encoding="utf-8")
    for rule_id in RULES:
        assert rule_id in text
    for typology in TYPOLOGIES:
        assert typology.typology_id in text


def test_the_ai_boundary_document_names_every_permitted_action():
    text = (DOCS / "AI_BOUNDARIES.md").read_text(encoding="utf-8")
    for action in AI_ALLOWED:
        assert action.split(".")[-1].replace("_", " ") in text.lower() or action in text


def test_no_document_claims_production_use():
    """The one claim this repository must never make by accident."""
    forbidden = (
        "in production",
        "our customers",
        "licensed by",
        "partner bank",
        "real transaction",
    )
    for path in sorted(DOCS.glob("*.md")) + [ROOT / "README.md", ROOT / "README.zh-CN.md"]:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            for line in text.splitlines():
                if phrase in line:
                    assert any(
                        negation in line
                        for negation in ("never", "no ", "not ", "nothing", "cannot", "without")
                    ), f"{path.name}: '{phrase}' appears without a negation — {line.strip()[:120]}"


def test_consequential_actions_are_listed_as_refused():
    text = (DOCS / "AI_BOUNDARIES.md").read_text(encoding="utf-8").lower()
    for phrase in ("approve a kyb case", "change the ledger", "execute fx", "clear an aml alert"):
        assert phrase in text
    assert len(CONSEQUENTIAL_ACTIONS) >= 12


def test_the_catalogue_generator_runs_clean():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_catalogue.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
