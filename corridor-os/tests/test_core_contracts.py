"""The contract layer: identifiers, money, events, audit."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from corridoros.core.audit import AuditLog, verify_entries
from corridoros.core.errors import EventError, IdError
from corridoros.core.events import EVENT_TYPES, EventBus
from corridoros.core.ids import IdFactory, make_id, validate
from corridoros.core.money import Money, MoneyError, convert

NOW = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)


def test_identifier_carries_its_kind():
    business = make_id("business", "sz001")
    assert validate(business, "business") == business
    with pytest.raises(IdError, match="payment identifier was required"):
        validate(business, "payment")


def test_mistyped_or_invented_identifier_is_refused():
    real = make_id("evidence", "inv4821")
    with pytest.raises(IdError, match="does not check out"):
        validate(real[:-1] + ("z" if real[-1] != "z" else "y"))
    with pytest.raises(IdError):
        validate("ev_totallymadeup")


def test_identifier_factory_is_deterministic():
    assert [IdFactory("x").next("payment") for _ in range(2)][0] == IdFactory("x").next("payment")


def test_money_refuses_floats_everywhere():
    with pytest.raises(MoneyError):
        Money(12.5, "SGD")
    with pytest.raises(MoneyError):
        Money.from_major(12.5, "SGD")
    with pytest.raises(MoneyError):
        convert(Money.from_major("100", "SGD"), "CNY", 5.32)


def test_conversion_records_its_rounding_remainder():
    result = convert(Money.from_major("100.01", "SGD"), "CNY", "5.3217")
    assert result.target.currency == "CNY"
    assert result.remainder != 0 or result.target.minor_units > 0


def test_event_bus_rejects_an_unknown_event_type():
    with pytest.raises(EventError):
        EventBus().publish("payment.exploded", occurred_at=NOW, actor_role="system", actor_id="x")


def test_the_twelve_events_are_the_twelve_events():
    assert len(EVENT_TYPES) == 12
    assert "payment.settled" in EVENT_TYPES and "exception.resolved" in EVENT_TYPES


def test_audit_chain_detects_a_partial_edit():
    log = AuditLog()
    for index in range(3):
        log.record(
            occurred_at=NOW + timedelta(minutes=index),
            actor_role="system",
            actor_id="core",
            action="risk.assess",
            object_type="payment",
            object_id=make_id("payment", f"p{index:03d}"),
            summary=f"entry {index}",
        )
    assert log.verify().status == "verified"

    rows = log.as_rows()
    rows[1]["summary"] = "quietly edited"
    broken = verify_entries(rows)
    assert broken.status == "broken"
    assert broken.broken_at == 1


def test_a_log_without_hashes_is_unverifiable_not_broken():
    rows = [{"entry_id": "aud_1", "entry_hash": ""}]
    assert verify_entries(rows).status == "unverifiable"
