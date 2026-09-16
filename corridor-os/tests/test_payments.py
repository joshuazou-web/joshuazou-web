"""Payment Core: ledger, KYB and the payout lifecycle."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from corridoros.core.errors import LedgerError, LifecycleError
from corridoros.core.ids import make_id
from corridoros.core.money import Money
from corridoros.payments.ledger import Ledger, Leg, account_id
from corridoros.scenario.world import BUSINESS_ID, SUPPLIER_ID, build_world

NOW = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)
SGD = Money.from_major("100.00", "SGD")


def test_a_journal_that_does_not_balance_posts_nothing():
    ledger = Ledger()
    with pytest.raises(LedgerError, match="does not balance"):
        ledger.post(
            [Leg(account_id(BUSINESS_ID, "SGD", "available"), SGD), Leg(account_id(BUSINESS_ID, "SGD", "payable"), SGD)],
            posted_at=NOW,
            description="unbalanced",
        )
    assert ledger.entries == ()


def test_a_correction_is_a_reversal_and_the_original_survives():
    ledger = Ledger()
    journal = ledger.post(
        [Leg(account_id("", "SGD", "external"), -SGD), Leg(account_id(BUSINESS_ID, "SGD", "available"), SGD)],
        posted_at=NOW,
        description="collection",
    )
    ledger.reverse(journal.journal_id, posted_at=NOW + timedelta(minutes=1), reason="duplicate advice")

    assert ledger.balance(account_id(BUSINESS_ID, "SGD", "available"), "SGD").is_zero()
    assert ledger.journal(journal.journal_id).entries, "the original entries are still there"
    assert ledger.is_balanced()

    with pytest.raises(LedgerError, match="already been reversed"):
        ledger.reverse(journal.journal_id, posted_at=NOW, reason="again")


def test_kyb_approval_is_refused_while_required_evidence_is_missing():
    world = build_world()
    system = world.system
    business_id = make_id("business", "sz002")
    system.onboard(
        business_id=business_id,
        legal_name="Anchor Logistics (Singapore) Pte. Ltd.",
        uen="202699999Z",
        entity_country="SG",
        expected_monthly_volume=Money.from_major("50000.00", "SGD"),
        occurred_at=NOW,
    )
    assert system.businesses.missing_evidence(business_id)
    with pytest.raises(LifecycleError, match="required evidence missing"):
        system.approve_business(business_id, occurred_at=NOW)


def test_an_unapproved_business_cannot_move_money():
    world = build_world()
    system = world.system
    business_id = make_id("business", "sz003")
    system.onboard(
        business_id=business_id,
        legal_name="Not Yet Approved Pte. Ltd.",
        uen="202612345B",
        entity_country="SG",
        expected_monthly_volume=Money.from_major("10000.00", "SGD"),
        occurred_at=NOW,
    )
    with pytest.raises(LifecycleError, match="not approved for payout"):
        system.create_payment(
            business_id=business_id,
            beneficiary_id=SUPPLIER_ID,
            amount=SGD,
            purpose_code="SUPPLIER_INVOICE",
            business_instruction_id="PO-9999",
            idempotency_key="idem-9999",
            occurred_at=NOW,
        )


def test_an_illegal_lifecycle_transition_is_refused():
    world = build_world()
    system = world.system
    with pytest.raises(LifecycleError, match="cannot go settled"):
        system.submit_payment(world.routine_payment_id, now=NOW)


def test_submitting_moves_money_from_available_to_payable_then_out():
    world = build_world()
    system = world.system
    entries = system.ledger.entries_for_payment(world.routine_payment_id)
    accounts = [entry.account.split(":")[-1] for entry in entries]
    assert accounts.count("payable") == 2, "reserved on submission, released on settlement"
    assert system.ledger.balance(account_id(BUSINESS_ID, "SGD", "payable"), "SGD").is_zero()


def test_settlement_arithmetic_is_checked_at_ingestion():
    from corridoros.core.domain import SettlementRecord

    with pytest.raises(ValueError, match="does not equal"):
        SettlementRecord(
            settlement_id=make_id("settlement", "stl001"),
            payment_id=make_id("payment", "p001"),
            gross=Money.from_major("100.00", "SGD"),
            fee=Money.from_major("2.00", "SGD"),
            net=Money.from_major("99.00", "SGD"),
            value_date=NOW,
            provider_reference="PSP-1",
        )
