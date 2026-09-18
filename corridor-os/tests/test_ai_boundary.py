"""The ten lines of this repository that matter most.

Six things the copilot may do, six it may not. These tests fail if a later
change widens the first list or weakens the refusals behind the second.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from corridoros.core.audit import AuditLog
from corridoros.core.authority import AI_ALLOWED, AI_COPILOT, CONSEQUENTIAL_ACTIONS, can, require
from corridoros.core.domain import ApprovalDecision
from corridoros.core.errors import AuthorityError
from corridoros.core.ids import make_id
from corridoros.evidence.copilot import FORBIDDEN_BRIEF_FIELDS, brief_fields

NOW = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)

# The six forbidden things, named as the actions that would perform them.
FORBIDDEN = [
    ("approve a KYB case", "business.approve"),
    ("change the ledger", "ledger.post"),
    ("execute FX", "fx.execute"),
    ("submit a payment", "payment.submit"),
    ("release a payment", "payment.approve"),
    ("clear an AML alert", "alert.clear"),
    ("close an investigation", "case.close"),
    ("resolve an exception", "exception.resolve"),
]


@pytest.mark.parametrize("description,action", FORBIDDEN)
def test_copilot_cannot_perform_consequential_actions(description, action):
    assert not can(AI_COPILOT, action), description
    with pytest.raises(AuthorityError, match="AI copilot may not"):
        require(AI_COPILOT, action)


def test_the_permitted_set_is_exactly_six_and_none_are_consequential():
    assert len(AI_ALLOWED) == 6
    assert not (AI_ALLOWED & CONSEQUENTIAL_ACTIONS)


def test_an_approval_decision_cannot_name_the_copilot_as_its_author():
    with pytest.raises(ValueError, match="cannot have the AI copilot"):
        ApprovalDecision(
            decision_id=make_id("decision", "dec001"),
            action="payment.approve",
            object_type="payment",
            object_id=make_id("payment", "p001"),
            actor_role=AI_COPILOT,
            actor_id="copilot",
            reason_code="looks fine to me",
            occurred_at=NOW,
        )


def test_the_audit_log_refuses_an_ai_decision_and_records_the_refusal():
    log = AuditLog()
    with pytest.raises(AuthorityError):
        log.record_decision(
            decision_id=make_id("decision", "dec002"),
            occurred_at=NOW,
            actor_role=AI_COPILOT,
            actor_id="copilot",
            action="case.close",
            object_type="case",
            object_id=make_id("case", "case001"),
            reason_code="resolved",
        )
    assert len(log.refusals) == 1
    assert log.entries == ()


def test_the_brief_has_nowhere_to_put_a_decision():
    """Not 'the copilot is told not to decide' — there is no field for it."""
    assert not (brief_fields() & FORBIDDEN_BRIEF_FIELDS)
