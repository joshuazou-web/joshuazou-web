"""Investigation cases, their priority, and their SLA.

A case is not an alert. RiskOps made that distinction the centre of its product
and it carries over unchanged: signals fire, a case is what a person opens
because signals fired, and the queue has a capacity that does not grow when the
alerts do.

Closing a case is a compliance officer's action. The copilot cannot close one —
`core.authority` refuses `case.close` for it — and while a case blocks a
payment, the payout engine refuses to submit. That chain is the reason "AI
cannot clear an AML alert" is a property of this system rather than a promise.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from ..core.audit import AuditLog
from ..core.domain import ReviewCase, RiskAssessment
from ..core.events import EventBus
from ..core.ids import IdFactory

# How long a case of each priority may wait before it is overdue.
SLA_HOURS: dict[int, int] = {1: 4, 2: 8, 3: 24, 4: 72}


def priority_for(assessment: RiskAssessment) -> int:
    """1 is most urgent. Derived from the band, not from a model."""
    return {"critical": 1, "high": 2, "medium": 3, "low": 4}[assessment.band]


class CaseBook:
    def __init__(self, bus: EventBus, audit: AuditLog, ids: IdFactory | None = None) -> None:
        self._bus = bus
        self._audit = audit
        self._ids = ids or IdFactory("case")
        self._cases: dict[str, ReviewCase] = {}

    def open(
        self,
        *,
        kind: str,
        title: str,
        assessment: RiskAssessment | None = None,
        payment_id: str | None = None,
        business_id: str | None = None,
        evidence_ids: tuple[str, ...] = (),
        opened_at: datetime,
        actor_role: str = "system",
        actor_id: str = "risk.rules",
        priority: int | None = None,
    ) -> ReviewCase:
        resolved_priority = priority if priority is not None else (
            priority_for(assessment) if assessment is not None else 3
        )
        case = ReviewCase(
            case_id=self._ids.next("case"),
            kind=kind,
            title=title,
            opened_at=opened_at,
            sla_due_at=opened_at + timedelta(hours=SLA_HOURS[resolved_priority]),
            priority=resolved_priority,
            payment_id=payment_id,
            business_id=business_id,
            evidence_ids=evidence_ids,
            signal_ids=tuple(signal.signal_id for signal in assessment.signals) if assessment else (),
        )
        self._cases[case.case_id] = case
        self._audit.record(
            occurred_at=opened_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="case.open",
            object_type="case",
            object_id=case.case_id,
            summary=title,
            payload={
                "priority": resolved_priority,
                "payment_id": payment_id,
                "signals": list(case.signal_ids),
            },
        )
        subject = {}
        if payment_id:
            subject["payment"] = payment_id
        if business_id:
            subject["business"] = business_id
        self._bus.publish(
            "case.opened",
            occurred_at=opened_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject=subject,
            payload={"case_id": case.case_id, "kind": kind, "priority": resolved_priority},
            idempotency_key=f"case.opened:{case.case_id}",
        )
        return case

    def assign(self, case_id: str, owner: str, *, occurred_at: datetime, actor_role: str, actor_id: str) -> ReviewCase:
        case = self.get(case_id)
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="case.assign",
            object_type="case",
            object_id=case_id,
            summary=f"assigned to {owner}",
            payload={"owner": owner},
        )
        updated = replace(case, owner=owner, state="assigned")
        self._cases[case_id] = updated
        return updated

    def close(
        self,
        case_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        decision_id: str,
        reason_code: str,
        note: str = "",
        ai_brief_id: str | None = None,
    ) -> ReviewCase:
        """Close a case. Refused for the copilot by `core.authority`."""
        case = self.get(case_id)
        self._audit.record_decision(
            decision_id=decision_id,
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="case.close",
            object_type="case",
            object_id=case_id,
            reason_code=reason_code,
            note=note,
            ai_brief_id=ai_brief_id,
        )
        updated = replace(case, state="closed", closed_at=occurred_at, closure_reason=reason_code)
        self._cases[case_id] = updated
        return updated

    def get(self, case_id: str) -> ReviewCase:
        return self._cases[case_id]

    @property
    def all(self) -> tuple[ReviewCase, ...]:
        return tuple(self._cases.values())

    def open_cases(self) -> tuple[ReviewCase, ...]:
        return tuple(case for case in self._cases.values() if case.state != "closed")

    def queue(self, capacity: int) -> tuple[tuple[ReviewCase, ...], tuple[ReviewCase, ...]]:
        """Split the open queue at the team's capacity.

        The second tuple is the backlog. It is returned rather than hidden,
        because a queue that reports only what fits above the line is reporting
        the capacity, not the risk.
        """
        ordered = sorted(self.open_cases(), key=lambda case: (case.priority, case.sla_due_at))
        return tuple(ordered[:capacity]), tuple(ordered[capacity:])

    def for_payment(self, payment_id: str) -> tuple[ReviewCase, ...]:
        return tuple(case for case in self._cases.values() if case.payment_id == payment_id)
