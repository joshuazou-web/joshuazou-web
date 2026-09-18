"""The intervention ladder, ported from FinSafe's business pack.

The properties tested here are the ones the original engine was measured on:
the amount sets a floor, signals can only raise it, a verified payee lowers the
floor by one, and a payee change on a payment of consequence is a stop.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from corridoros.core.domain import Beneficiary, PaymentInstruction, RiskAssessment, RiskSignal
from corridoros.core.ids import make_id
from corridoros.core.money import Money
from corridoros.intervention.engine import decide
from corridoros.intervention.policy import AMOUNT_TIERS, tier_for

NOW = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)
BUSINESS = make_id("business", "sz001")
BENEFICIARY = make_id("beneficiary", "ben0193")


def _payment(amount: str) -> PaymentInstruction:
    return PaymentInstruction(
        payment_id=make_id("payment", "p001"),
        business_id=BUSINESS,
        beneficiary_id=BENEFICIARY,
        amount=Money.from_major(amount, "SGD"),
        purpose_code="SUPPLIER_INVOICE",
        business_instruction_id="PO-1",
        idempotency_key="idem-1",
        created_at=NOW,
    )


def _beneficiary(*, verified: bool = False, changed_days_ago: int | None = None) -> Beneficiary:
    changed = NOW - timedelta(days=changed_days_ago) if changed_days_ago is not None else None
    verified_at = NOW - timedelta(days=1) if verified else None
    if verified and changed is not None:
        verified_at = changed + timedelta(hours=1)
    return Beneficiary(
        beneficiary_id=BENEFICIARY,
        business_id=BUSINESS,
        display_name="Meridian Components Pte. Ltd.",
        bank_country="SG",
        account_last4="8830",
        created_at=NOW - timedelta(days=200),
        last_changed_at=changed,
        verified_at=verified_at,
    )


def _assessment(*signal_ids: str) -> RiskAssessment:
    return RiskAssessment(
        assessment_id=make_id("assessment", "ra001"),
        payment_id=make_id("payment", "p001"),
        band="low" if not signal_ids else "high",
        score=10 * len(signal_ids),
        signals=tuple(RiskSignal(signal_id, "high", signal_id) for signal_id in signal_ids),
        assessed_at=NOW,
        rules_version="1.0.0",
    )


@pytest.mark.parametrize(
    "amount,expected_tier",
    [("800.00", "t0"), ("4500.00", "t1"), ("12500.00", "t2"), ("90000.00", "t3")],
)
def test_amount_tiers_are_stable(amount, expected_tier):
    assert tier_for(Money.from_major(amount, "SGD")).tier_id == expected_tier


def test_the_amount_sets_a_floor_with_no_signals_at_all():
    decision = decide(_payment("90000.00"), _assessment(), _beneficiary(), now=NOW)
    assert decision.selected_level == 3
    assert "amount_floor_rule" in decision.drivers
    assert "t3" in decision.why_not_weaker


def test_a_verified_payee_lowers_the_floor_by_one_but_never_removes_it():
    unverified = decide(_payment("12500.00"), _assessment(), _beneficiary(), now=NOW)
    verified = decide(_payment("12500.00"), _assessment(), _beneficiary(verified=True), now=NOW)
    assert unverified.amount_floor == 2
    assert verified.amount_floor == 1
    assert verified.selected_level >= 1


def test_signals_raise_the_level_and_never_lower_it():
    quiet = decide(_payment("800.00"), _assessment(), _beneficiary(verified=True), now=NOW)
    noisy = decide(
        _payment("800.00"), _assessment("executive_instruction"), _beneficiary(verified=True), now=NOW
    )
    assert quiet.selected_level == 0
    assert noisy.selected_level == 4


def test_a_payee_change_on_a_payment_of_consequence_is_pinned_to_a_stop():
    decision = decide(
        _payment("12500.00"),
        _assessment("payee_account_change"),
        _beneficiary(verified=True, changed_days_ago=6),
        now=NOW,
    )
    assert decision.selected_level == 4
    assert "large_payment_payee_change_override" in decision.drivers
    assert decision.required_approvals == 2
    assert "callback_known_contact" in decision.required_verifications
    assert "obtain_change_authorisation" in decision.required_verifications


def test_a_small_payee_change_still_escalates_but_is_not_overridden():
    decision = decide(
        _payment("400.00"),
        _assessment("payee_account_change"),
        _beneficiary(verified=True, changed_days_ago=3),
        now=NOW,
    )
    assert decision.selected_level == 4, "payee_account_change is a critical signal at any size"
    assert "large_payment_payee_change_override" not in decision.drivers


def test_every_decision_explains_what_it_did_not_choose():
    for amount in ("800.00", "12500.00", "90000.00"):
        decision = decide(_payment(amount), _assessment(), _beneficiary(), now=NOW)
        assert decision.why_not_weaker and decision.why_not_stronger
        assert decision.policy


def test_the_ladder_has_four_tiers_and_they_are_ordered():
    floors = [tier.floor_level for tier in AMOUNT_TIERS]
    assert floors == sorted(floors)
