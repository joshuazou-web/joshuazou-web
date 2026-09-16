"""SGD collection.

A collection intent exists so that incoming money can be attributed without
guessing. The blueprint's phrasing was exactly right and worth keeping: money
that arrives without a resolvable reference is not "probably customer X". It
becomes unattributed funds with an age, and ageing unattributed funds are an
operational exception rather than a rounding detail.

Attribution is idempotent on the provider's own event identifier, because a
payment provider that sends the same credit advice twice must not credit the
balance twice. The rule lives in the event log (see `core.events`), and this
module relies on it rather than writing a second version of it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from ..core.audit import AuditLog
from ..core.domain import CollectionIntent
from ..core.errors import LifecycleError
from ..core.ids import IdFactory
from ..core.money import Money
from .ledger import Ledger, Leg, account_id


@dataclass(frozen=True)
class UnattributedCredit:
    provider_event_id: str
    amount: Money
    reference: str
    received_at: datetime
    note: str


class CollectionRegistry:
    def __init__(self, audit: AuditLog, ledger: Ledger, ids: IdFactory | None = None) -> None:
        self._audit = audit
        self._ledger = ledger
        self._ids = ids or IdFactory("col")
        self._intents: dict[str, CollectionIntent] = {}
        self._by_reference: dict[str, str] = {}
        self._seen_events: set[str] = set()
        self.unattributed: list[UnattributedCredit] = []

    def open_intent(
        self,
        *,
        business_id: str,
        expected_amount: Money,
        reference: str,
        created_at: datetime,
        ttl: timedelta = timedelta(days=7),
    ) -> CollectionIntent:
        intent = CollectionIntent(
            intent_id=self._ids.next("intent"),
            business_id=business_id,
            expected_amount=expected_amount,
            reference=reference,
            expires_at=created_at + ttl,
            created_at=created_at,
        )
        self._intents[intent.intent_id] = intent
        self._by_reference[reference] = intent.intent_id
        return intent

    def get(self, intent_id: str) -> CollectionIntent:
        try:
            return self._intents[intent_id]
        except KeyError:
            raise LifecycleError(f"unknown collection intent {intent_id}") from None

    @property
    def all(self) -> tuple[CollectionIntent, ...]:
        return tuple(self._intents.values())

    def attribute(
        self,
        *,
        provider_event_id: str,
        amount: Money,
        reference: str,
        received_at: datetime,
        actor_role: str = "system",
        actor_id: str = "provider.webhook",
    ) -> CollectionIntent | None:
        """Credit an incoming payment to its intent, or record it as unattributed."""
        if provider_event_id in self._seen_events:
            return None
        self._seen_events.add(provider_event_id)

        intent_id = self._by_reference.get(reference)
        if intent_id is None:
            self.unattributed.append(
                UnattributedCredit(
                    provider_event_id=provider_event_id,
                    amount=amount,
                    reference=reference,
                    received_at=received_at,
                    note="no collection intent carries this reference",
                )
            )
            return None

        intent = self.get(intent_id)
        self._ledger.post(
            [
                Leg(account_id("", amount.currency, "external"), -amount),
                Leg(account_id(intent.business_id, amount.currency, "available"), amount),
            ],
            posted_at=received_at,
            description=f"collection {intent_id} attributed from {provider_event_id}",
        )
        self._audit.record(
            occurred_at=received_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="collection.attribute",
            object_type="intent",
            object_id=intent_id,
            summary=f"attributed {amount.format()} to {reference}",
            payload={"provider_event_id": provider_event_id},
        )
        updated = replace(intent, status="attributed", attributed_amount=amount, provider_event_id=provider_event_id)
        self._intents[intent_id] = updated
        return updated
