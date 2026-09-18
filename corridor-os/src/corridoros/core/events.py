"""The twelve events, and the log that will not accept a bad one.

This module is the join. `payments` publishes; `risk`, `intervention` and
`evidence` subscribe. None of them imports another, which is what stops the
four merged projects from growing back into four projects with a shared
requirements file.

Three properties are enforced here rather than left to each publisher:

**Append-only with a monotonic sequence.** Nothing is edited. A correction is a
later event, so the history of a payment is the history, not the current row.

**Idempotency by key.** A provider that delivers the same webhook twice — which
they do — gets the first event back and the log is unchanged. This is the
mechanism behind the "a retry never creates a second payout" guarantee; the
payout engine relies on it rather than re-implementing it.

**Ordering by lifecycle rank.** `payment.settled` cannot precede
`payment.submitted` for the same payment. An event that arrives early is not
dropped and not applied: it goes to `quarantine`, where an operator can see it.
Silently dropping it loses information; applying it corrupts the ledger.
RiskOps' state machine made the same choice, and this generalises it across
modules.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from .errors import EventError
from .ids import IdFactory, validate

# The twelve. Nothing else may be published.
EVENT_TYPES: tuple[str, ...] = (
    "business.submitted",
    "business.approved",
    "payment.created",
    "beneficiary.changed",
    "risk.assessed",
    "intervention.required",
    "case.opened",
    "payment.approved",
    "payment.submitted",
    "payment.settled",
    "reconciliation.failed",
    "exception.resolved",
)

# Rank within one payment's life. Events absent from this map (a beneficiary
# change, a case opening) may legitimately arrive at any point and are not
# ordered against the lifecycle.
PAYMENT_RANK: dict[str, int] = {
    "payment.created": 1,
    "risk.assessed": 2,
    "intervention.required": 3,
    "payment.approved": 4,
    "payment.submitted": 5,
    "payment.settled": 6,
    "reconciliation.failed": 7,
}


@dataclass(frozen=True)
class Event:
    event_id: str
    type: str
    occurred_at: datetime
    actor_role: str
    actor_id: str
    subject: dict[str, str] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None
    seq: int = 0

    def __post_init__(self) -> None:
        if self.type not in EVENT_TYPES:
            raise EventError(
                f"{self.type!r} is not one of the twelve CorridorOS events: {EVENT_TYPES}"
            )
        for kind, identifier in self.subject.items():
            validate(identifier, kind)

    @property
    def payment_id(self) -> str | None:
        return self.subject.get("payment")

    def as_row(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "seq": self.seq,
            "type": self.type,
            "occurred_at": self.occurred_at.isoformat(),
            "actor_role": self.actor_role,
            "actor_id": self.actor_id,
            "subject": dict(self.subject),
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class QuarantinedEvent:
    event: Event
    reason: str
    detail: str

    def as_row(self) -> dict[str, Any]:
        return {**self.event.as_row(), "quarantine_reason": self.reason, "detail": self.detail}


class EventBus:
    """An in-process append-only event log with synchronous subscribers.

    Synchronous on purpose: this is a demonstration system, and a reader
    following one payment through seven screens should not have to reason about
    delivery timing on top of everything else. The contract — typed events,
    idempotency, ordering, quarantine — is the part that would survive being
    put behind a real broker.
    """

    def __init__(self, ids: IdFactory | None = None) -> None:
        self._events: list[Event] = []
        self._by_key: dict[str, Event] = {}
        self._handlers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._ids = ids or IdFactory("evt")
        self.quarantine: list[QuarantinedEvent] = []
        self.duplicates: list[Event] = []

    # -- publishing --------------------------------------------------------

    def publish(
        self,
        type: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        subject: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Event:
        event = Event(
            event_id=self._ids.next("event"),
            type=type,
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject=dict(subject or {}),
            payload=dict(payload or {}),
            idempotency_key=idempotency_key,
        )
        return self.append(event)

    def append(self, event: Event) -> Event:
        """Accept, deduplicate or quarantine `event`; return what is in the log.

        A duplicate returns the original event, so a caller that retried gets
        the identifier it would have got the first time and does not create a
        second anything.
        """
        if event.idempotency_key is not None:
            existing = self._by_key.get(event.idempotency_key)
            if existing is not None:
                self.duplicates.append(event)
                return existing

        problem = self._ordering_problem(event)
        if problem is not None:
            reason, detail = problem
            self.quarantine.append(QuarantinedEvent(event, reason, detail))
            raise EventError(f"{event.type} for {event.subject}: {detail}")

        stored = replace(event, seq=len(self._events) + 1)
        self._events.append(stored)
        if stored.idempotency_key is not None:
            self._by_key[stored.idempotency_key] = stored
        for handler in self._handlers[stored.type]:
            handler(stored)
        for handler in self._handlers["*"]:
            handler(stored)
        return stored

    def _ordering_problem(self, event: Event) -> tuple[str, str] | None:
        rank = PAYMENT_RANK.get(event.type)
        payment_id = event.payment_id
        if rank is None or payment_id is None:
            return None
        seen = [
            PAYMENT_RANK[item.type]
            for item in self._events
            if item.payment_id == payment_id and item.type in PAYMENT_RANK
        ]
        if not seen:
            if rank > PAYMENT_RANK["payment.created"]:
                return (
                    "out_of_order",
                    f"{event.type} arrived before payment.created for {payment_id}",
                )
            return None
        highest = max(seen)
        if rank < highest:
            return (
                "out_of_order",
                f"{event.type} (rank {rank}) arrived after rank {highest} for {payment_id}",
            )
        if rank == highest:
            return (
                "replayed",
                f"{event.type} has already been recorded for {payment_id}",
            )
        return None

    # -- subscribing -------------------------------------------------------

    def subscribe(self, type: str, handler: Callable[[Event], None]) -> None:
        if type != "*" and type not in EVENT_TYPES:
            raise EventError(f"cannot subscribe to unknown event type {type!r}")
        self._handlers[type].append(handler)

    # -- reading -----------------------------------------------------------

    def __len__(self) -> int:
        return len(self._events)

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def timeline(self, **subject: str) -> tuple[Event, ...]:
        """Every event touching the given subject identifiers, in order."""
        return tuple(
            event
            for event in self._events
            if all(event.subject.get(kind) == value for kind, value in subject.items())
        )

    def of_type(self, *types: str) -> tuple[Event, ...]:
        wanted = set(types)
        return tuple(event for event in self._events if event.type in wanted)
