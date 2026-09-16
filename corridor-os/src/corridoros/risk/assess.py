"""Assessment: signals in, `RiskAssessment` out, `risk.assessed` published.

The module subscribes to `payment.created` through `Assessor.on_payment_created`
rather than being called by the payments module, which is what keeps the
dependency one-directional. Payments does not know Risk exists.
"""

from __future__ import annotations

from datetime import datetime

from ..core.audit import AuditLog
from ..core.domain import Beneficiary, PaymentInstruction, RiskAssessment
from ..core.events import EventBus
from ..core.ids import IdFactory
from .signals import RULES_VERSION, PaymentContext, band_of, evaluate, score_of


class Assessor:
    def __init__(self, bus: EventBus, audit: AuditLog, ids: IdFactory | None = None) -> None:
        self._bus = bus
        self._audit = audit
        self._ids = ids or IdFactory("ra")
        self._assessments: dict[str, RiskAssessment] = {}

    def assess(
        self,
        payment: PaymentInstruction,
        beneficiary: Beneficiary,
        *,
        now: datetime,
        prior_payments: tuple[PaymentInstruction, ...] = (),
        missing_evidence_kinds: tuple[str, ...] = (),
        instruction_note: str = "",
    ) -> RiskAssessment:
        signals = evaluate(
            PaymentContext(
                payment=payment,
                beneficiary=beneficiary,
                now=now,
                prior_payments=prior_payments,
                missing_evidence_kinds=missing_evidence_kinds,
                instruction_note=instruction_note,
            )
        )
        score = score_of(signals)
        assessment = RiskAssessment(
            assessment_id=self._ids.next("assessment"),
            payment_id=payment.payment_id,
            band=band_of(score),
            score=score,
            signals=signals,
            assessed_at=now,
            rules_version=RULES_VERSION,
            evidence_complete=not missing_evidence_kinds,
            missing_evidence_kinds=missing_evidence_kinds,
        )
        self._assessments[assessment.assessment_id] = assessment
        self._audit.record(
            occurred_at=now,
            actor_role="system",
            actor_id="risk.rules",
            action="risk.assess",
            object_type="payment",
            object_id=payment.payment_id,
            summary=(
                f"{len(signals)} signal(s), band {assessment.band} "
                f"(rules {RULES_VERSION}); no model participated"
            ),
            payload={
                "assessment_id": assessment.assessment_id,
                "signals": [signal.signal_id for signal in signals],
                "score": score,
            },
        )
        self._bus.publish(
            "risk.assessed",
            occurred_at=now,
            actor_role="system",
            actor_id="risk.rules",
            subject={"payment": payment.payment_id, "beneficiary": beneficiary.beneficiary_id},
            payload={
                "assessment_id": assessment.assessment_id,
                "band": assessment.band,
                "score": score,
                "signals": [signal.signal_id for signal in signals],
                "rules_version": RULES_VERSION,
            },
            idempotency_key=f"risk.assessed:{assessment.assessment_id}",
        )
        return assessment

    def get(self, assessment_id: str) -> RiskAssessment:
        return self._assessments[assessment_id]

    def for_payment(self, payment_id: str) -> RiskAssessment | None:
        for assessment in self._assessments.values():
            if assessment.payment_id == payment_id:
                return assessment
        return None

    @property
    def all(self) -> tuple[RiskAssessment, ...]:
        return tuple(self._assessments.values())
