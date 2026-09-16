"""CorridorOS — the four modules wired into one system.

This is the only file that knows all four modules exist. Each of them depends
on `core` and nothing else, so the wiring is here and the coupling is nowhere:
`payments` never imports `risk`; `risk` learns about a payment from
`payment.created`; `intervention` reads an assessment and a beneficiary and
returns a decision it cannot apply; `evidence` is called and never calls.

The methods below are the operating flow of the product, in the order an
operator meets it:

    onboard → approve → fund → create payment → controls → verify → approve
    → submit → settle → reconcile

`run_controls` is the interesting one. It assembles the evidence packet, runs
the deterministic assessment, asks the intervention engine what the payment
needs, stores those requirements on the payment, and opens an investigation
case when the band warrants one. Four modules participate and not one of them
decides anything: what comes out is a set of requirements that a person has to
satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .core.audit import AuditLog
from .core.domain import (
    BusinessProfile,
    PaymentInstruction,
    ReviewCase,
    RiskAssessment,
)
from .core.events import EventBus
from .core.ids import IdFactory
from .core.money import Money
from .evidence.copilot import CaseBrief, Copilot
from .evidence.packet import EvidencePacket, assemble_for_business, assemble_for_payment
from .evidence.store import EvidenceStore
from .intervention.engine import InterventionDecision, decide
from .payments.beneficiaries import BeneficiaryRegistry
from .payments.collection import CollectionRegistry
from .payments.fx import FxDesk
from .payments.kyb import KybRegistry
from .payments.ledger import Ledger
from .payments.payout import PayoutEngine
from .payments.reconciliation import BankStatementLine, ReconciliationEngine, ReconciliationResult
from .payments.settlement import SettlementBook
from .risk.assess import Assessor
from .risk.cases import CaseBook

# A case at this priority or better holds the payment until a compliance
# officer closes it.
BLOCKING_PRIORITY = 2


@dataclass(frozen=True)
class ControlOutcome:
    """What the controls concluded, and what a person must now do."""

    payment: PaymentInstruction
    assessment: RiskAssessment
    packet: EvidencePacket
    intervention: InterventionDecision
    case: ReviewCase | None
    brief: CaseBrief

    @property
    def blocked_by_case(self) -> bool:
        return self.case is not None and self.case.priority <= BLOCKING_PRIORITY


class CorridorOS:
    def __init__(self, namespace: str = "cos") -> None:
        ids = IdFactory(namespace)
        self.ids = ids
        self.bus = EventBus(ids)
        self.audit = AuditLog(ids)
        self.ledger = Ledger(ids)
        self.evidence = EvidenceStore(ids)
        self.businesses = KybRegistry(self.bus, self.audit, self.evidence.kinds_for_business)
        self.beneficiaries = BeneficiaryRegistry(self.bus, self.audit)
        self.collections = CollectionRegistry(self.audit, self.ledger, ids)
        self.fx = FxDesk(self.audit, ids)
        self.payouts = PayoutEngine(
            self.bus,
            self.audit,
            self.ledger,
            ids=ids,
            business_may_move_money=lambda business_id: self.businesses.get(business_id).may_move_money,
        )
        self.settlements = SettlementBook(ids)
        self.reconciliation = ReconciliationEngine(self.bus, self.audit, self.ledger, ids)
        self.assessor = Assessor(self.bus, self.audit, ids)
        self.cases = CaseBook(self.bus, self.audit, ids)
        self.copilot = Copilot()
        self._decisions = IdFactory(f"{namespace}d")
        self.interventions: dict[str, InterventionDecision] = {}

    # -- identifiers -------------------------------------------------------

    def next_decision_id(self) -> str:
        return self._decisions.next("decision")

    # -- onboarding --------------------------------------------------------

    def onboard(
        self,
        *,
        business_id: str,
        legal_name: str,
        uen: str,
        entity_country: str,
        expected_monthly_volume: Money,
        occurred_at: datetime,
    ) -> BusinessProfile:
        profile = BusinessProfile(
            business_id=business_id,
            legal_name=legal_name,
            entity_country=entity_country,
            uen=uen,
            review_status="draft",
            submitted_at=occurred_at,
            expected_monthly_volume=expected_monthly_volume,
        )
        return self.businesses.submit(profile, occurred_at=occurred_at)

    def approve_business(
        self,
        business_id: str,
        *,
        occurred_at: datetime,
        actor_id: str = "compliance.lead",
        note: str = "",
    ) -> BusinessProfile:
        return self.businesses.approve(
            business_id,
            occurred_at=occurred_at,
            actor_role="compliance_officer",
            actor_id=actor_id,
            decision_id=self.next_decision_id(),
            note=note,
        )

    def kyb_packet(self, business_id: str, *, now: datetime) -> EvidencePacket:
        return assemble_for_business(self.evidence, self.businesses.get(business_id), now=now)

    # -- money in ----------------------------------------------------------

    def collect(
        self,
        *,
        business_id: str,
        amount: Money,
        reference: str,
        received_at: datetime,
        provider_event_id: str,
    ) -> None:
        self.collections.open_intent(
            business_id=business_id,
            expected_amount=amount,
            reference=reference,
            created_at=received_at - timedelta(minutes=5),
        )
        self.collections.attribute(
            provider_event_id=provider_event_id,
            amount=amount,
            reference=reference,
            received_at=received_at,
        )

    # -- money out ---------------------------------------------------------

    def create_payment(
        self,
        *,
        business_id: str,
        beneficiary_id: str,
        amount: Money,
        purpose_code: str,
        business_instruction_id: str,
        idempotency_key: str,
        occurred_at: datetime,
        evidence_ids: tuple[str, ...] = (),
    ) -> PaymentInstruction:
        return self.payouts.create(
            business_id=business_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            purpose_code=purpose_code,
            business_instruction_id=business_instruction_id,
            idempotency_key=idempotency_key,
            occurred_at=occurred_at,
            evidence_ids=evidence_ids,
        )

    def run_controls(
        self,
        payment_id: str,
        *,
        now: datetime,
        instruction_note: str = "",
    ) -> ControlOutcome:
        """Assess, decide what is required, and open a case if one is warranted."""
        payment = self.payouts.get(payment_id)
        beneficiary = self.beneficiaries.get(payment.beneficiary_id)

        packet = assemble_for_payment(self.evidence, payment, beneficiary, now=now)
        assessment = self.assessor.assess(
            payment,
            beneficiary,
            now=now,
            prior_payments=self.payouts.for_business(payment.business_id),
            missing_evidence_kinds=packet.missing_kinds,
            instruction_note=instruction_note,
        )
        intervention = decide(payment, assessment, beneficiary, now=now)
        self.interventions[payment_id] = intervention

        payment = self.payouts.apply_controls(
            payment_id,
            assessment_id=assessment.assessment_id,
            intervention_level=intervention.selected_level,
            required_approvals=intervention.required_approvals,
            required_verifications=intervention.required_verifications,
            occurred_at=now,
        )

        if intervention.requires_intervention:
            self.bus.publish(
                "intervention.required",
                occurred_at=now,
                actor_role="system",
                actor_id="intervention.engine",
                subject={"payment": payment_id, "business": payment.business_id},
                payload=intervention.as_row(),
                idempotency_key=f"intervention.required:{payment_id}:{intervention.selected_level}",
            )

        case: ReviewCase | None = None
        if assessment.band in ("critical", "high"):
            case = self.cases.open(
                kind="aml_investigation",
                title=(
                    f"{payment.amount.format()} to {beneficiary.display_name}: "
                    f"{', '.join(signal.signal_id for signal in assessment.signals)}"
                ),
                assessment=assessment,
                payment_id=payment_id,
                business_id=payment.business_id,
                evidence_ids=tuple(sorted(packet.evidence_ids)),
                opened_at=now,
            )
            payment = self.payouts.attach_case(payment_id, case.case_id)
            if case.priority <= BLOCKING_PRIORITY:
                self.payouts.block(payment_id, case.case_id)

        brief = self.copilot.summarise_payment(
            packet,
            payment,
            beneficiary,
            assessment,
            now=now,
            untrusted_text=instruction_note,
        )
        return ControlOutcome(payment, assessment, packet, intervention, case, brief)

    def complete_verification(
        self,
        payment_id: str,
        verification_id: str,
        *,
        now: datetime,
        actor_id: str,
        actor_role: str = "treasury_operator",
        evidence_id: str | None = None,
        note: str = "",
    ) -> PaymentInstruction:
        payment = self.payouts.record_verification(
            payment_id,
            verification_id,
            occurred_at=now,
            actor_role=actor_role,
            actor_id=actor_id,
            evidence_id=evidence_id,
            note=note,
        )
        if verification_id == "callback_known_contact":
            self.beneficiaries.record_verification(
                payment.beneficiary_id,
                occurred_at=now,
                method="callback_to_number_on_file",
                actor_role=actor_role,
                actor_id=actor_id,
                evidence_id=evidence_id,
            )
        return payment

    def close_case(
        self,
        case_id: str,
        *,
        now: datetime,
        actor_id: str = "compliance.lead",
        reason_code: str = "investigated_no_further_action",
        note: str = "",
        ai_brief_id: str | None = None,
    ) -> ReviewCase:
        case = self.cases.close(
            case_id,
            occurred_at=now,
            actor_role="compliance_officer",
            actor_id=actor_id,
            decision_id=self.next_decision_id(),
            reason_code=reason_code,
            note=note,
            ai_brief_id=ai_brief_id,
        )
        if case.payment_id:
            self.payouts.release_block(case.payment_id, case_id)
        return case

    def approve_payment(
        self,
        payment_id: str,
        *,
        now: datetime,
        actor_id: str,
        reason_code: str = "reviewed_and_authorised",
        note: str = "",
    ) -> PaymentInstruction:
        return self.payouts.approve(
            payment_id,
            occurred_at=now,
            actor_role="payment_approver",
            actor_id=actor_id,
            decision_id=self.next_decision_id(),
            reason_code=reason_code,
            note=note,
        )

    def submit_payment(
        self, payment_id: str, *, now: datetime, actor_id: str = "approver.one"
    ) -> PaymentInstruction:
        return self.payouts.submit(
            payment_id, occurred_at=now, actor_role="payment_approver", actor_id=actor_id
        )

    def settle_payment(
        self,
        payment_id: str,
        *,
        now: datetime,
        fee: Money,
        provider_reference: str,
        value_date: datetime | None = None,
    ):
        payment = self.payouts.get(payment_id)
        self.payouts.accept(payment_id, occurred_at=now)
        settlement = self.settlements.record(
            payment_id=payment_id,
            gross=payment.amount,
            fee=fee,
            value_date=value_date or now,
            provider_reference=provider_reference,
        )
        self.payouts.settle(payment_id, occurred_at=now, settlement_id=settlement.settlement_id)
        return settlement

    def reconcile(
        self,
        *,
        now: datetime,
        bank_lines: tuple[BankStatementLine, ...],
        currency: str = "SGD",
    ) -> ReconciliationResult:
        return self.reconciliation.run(
            run_at=now,
            settlements=self.settlements.all,
            bank_lines=bank_lines,
            currency=currency,
        )

    # -- reading -----------------------------------------------------------

    def payment_view(self, payment_id: str, *, now: datetime) -> dict:
        """Everything the console shows about one payment, from every module."""
        payment = self.payouts.get(payment_id)
        beneficiary = self.beneficiaries.get(payment.beneficiary_id)
        business = self.businesses.get(payment.business_id)
        assessment = self.assessor.for_payment(payment_id)
        intervention = self.interventions.get(payment_id)
        packet = assemble_for_payment(self.evidence, payment, beneficiary, now=now)
        settlement = self.settlements.for_payment(payment_id)
        return {
            "payment": {
                "payment_id": payment.payment_id,
                "business_id": payment.business_id,
                "beneficiary_id": payment.beneficiary_id,
                "amount_minor": payment.amount.minor_units,
                "currency": payment.amount.currency,
                "amount_display": payment.amount.format(),
                "purpose_code": payment.purpose_code,
                "business_instruction_id": payment.business_instruction_id,
                "state": payment.state,
                "intervention_level": payment.intervention_level,
                "required_approvals": payment.required_approvals,
                "approvals": list(payment.approval_decision_ids),
                "required_verifications": list(payment.required_verifications),
                "completed_verifications": list(payment.completed_verifications),
                "outstanding_verifications": list(payment.outstanding_verifications),
                "blocking_cases": list(self.payouts.blocking_cases(payment_id)),
                "case_ids": list(payment.case_ids),
                "created_at": payment.created_at.isoformat(),
                "settled_at": payment.settled_at.isoformat() if payment.settled_at else None,
            },
            "business": {
                "business_id": business.business_id,
                "legal_name": business.legal_name,
                "uen": business.uen,
                "review_status": business.review_status,
            },
            "beneficiary": {
                "beneficiary_id": beneficiary.beneficiary_id,
                "display_name": beneficiary.display_name,
                "bank_country": beneficiary.bank_country,
                "account_last4": beneficiary.account_last4,
                "previous_account_last4": beneficiary.previous_account_last4,
                "last_changed_at": beneficiary.last_changed_at.isoformat()
                if beneficiary.last_changed_at
                else None,
                "verified_at": beneficiary.verified_at.isoformat() if beneficiary.verified_at else None,
                "verification_is_current": beneficiary.verification_is_current(now),
            },
            "assessment": None
            if assessment is None
            else {
                "assessment_id": assessment.assessment_id,
                "band": assessment.band,
                "score": assessment.score,
                "rules_version": assessment.rules_version,
                "signals": [
                    {
                        "signal_id": signal.signal_id,
                        "severity": signal.severity,
                        "summary": signal.summary,
                        "facts": signal.facts,
                    }
                    for signal in assessment.signals
                ],
            },
            "intervention": None if intervention is None else intervention.as_row(),
            "evidence": packet.as_row(),
            "evidence_items": [
                {
                    "evidence_id": item.evidence_id,
                    "kind": item.kind,
                    "title": item.title,
                    "issuer": item.issuer,
                    "issued_at": item.issued_at.isoformat() if item.issued_at else None,
                    "excerpt": item.excerpt,
                    "checksum": item.checksum,
                    "location": item.location,
                }
                for item in packet.items
            ],
            "cases": [
                {
                    "case_id": case.case_id,
                    "kind": case.kind,
                    "title": case.title,
                    "priority": case.priority,
                    "state": case.state,
                    "sla_due_at": case.sla_due_at.isoformat(),
                    "closure_reason": case.closure_reason,
                }
                for case in self.cases.for_payment(payment_id)
            ],
            "settlement": None
            if settlement is None
            else {
                "settlement_id": settlement.settlement_id,
                "gross": settlement.gross.format(),
                "fee": settlement.fee.format(),
                "net": settlement.net.format(),
                "value_date": settlement.value_date.isoformat(),
                "provider_reference": settlement.provider_reference,
            },
            "timeline": [event.as_row() for event in self.bus.timeline(payment=payment_id)],
            "audit": [
                {
                    "entry_id": entry.entry_id,
                    "seq": entry.seq,
                    "occurred_at": entry.occurred_at.isoformat(),
                    "actor_role": entry.actor_role,
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "summary": entry.summary,
                    "entry_hash": entry.entry_hash,
                }
                for entry in self.audit.for_object(payment_id)
            ],
        }
