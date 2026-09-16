"""Supplier payout: the state machine, the idempotency rule, and dual approval.

This is where the platform's authority model stops being a diagram. Four
refusals live here, and each one exists because the corresponding mistake is
the one that actually costs money in a cross-border operation:

**A retry never creates a second payout.** Idempotency is keyed on the
business's own instruction identifier — the purchase order, not a UUID the
client generates fresh on every retry. A repeated `create` returns the first
payment. This is the one guarantee that has to hold even when the caller is
behaving badly, so it is checked before anything else.

**An outstanding verification blocks approval.** When the intervention engine
requires a callback to a known contact, the approver cannot approve until
someone records that the callback happened. The requirement is state on the
payment, not advice in a UI.

**Two approvers means two people.** The same person approving twice is refused
by identity, not by counting. A four-eyes control that one pair of eyes can
satisfy is not a control.

**An open blocking case holds the payment.** When Risk & Compliance opens an
investigation, the payment cannot be submitted while it is open — and closing
that case is a compliance officer's action, which the copilot cannot perform.

The state machine itself is adapted from RiskOps' `statemachine.py`, with the
card-acquiring lifecycle (`authorized -> captured`) replaced by the B2B payout
lifecycle the corridor blueprint specified.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from ..core.audit import AuditLog
from ..core.domain import PaymentInstruction
from ..core.errors import LifecycleError
from ..core.events import EventBus
from ..core.ids import IdFactory
from ..core.money import Money
from .ledger import Ledger, Leg, account_id

TRANSITIONS: dict[str, tuple[str, ...]] = {
    "created": ("awaiting_intervention", "awaiting_approval", "cancelled"),
    "awaiting_intervention": ("awaiting_approval", "cancelled"),
    "awaiting_approval": ("approved", "cancelled"),
    "approved": ("submitted", "cancelled"),
    "submitted": ("accepted", "failed", "returned"),
    "accepted": ("settled", "failed", "returned"),
    "settled": (),
    "failed": (),
    "returned": (),
    "cancelled": (),
}


@dataclass(frozen=True)
class DuplicateAttempt:
    business_instruction_id: str
    existing_payment_id: str
    attempted_at: datetime
    note: str


class PayoutEngine:
    def __init__(
        self,
        bus: EventBus,
        audit: AuditLog,
        ledger: Ledger,
        *,
        ids: IdFactory | None = None,
        business_may_move_money: Callable[[str], bool] | None = None,
    ) -> None:
        self._bus = bus
        self._audit = audit
        self._ledger = ledger
        self._ids = ids or IdFactory("pay")
        self._may_move_money = business_may_move_money or (lambda _business_id: True)
        self._payments: dict[str, PaymentInstruction] = {}
        self._by_instruction: dict[str, str] = {}
        self._blocking_cases: dict[str, set[str]] = {}
        self.duplicate_attempts: list[DuplicateAttempt] = []

    # -- reading -----------------------------------------------------------

    def get(self, payment_id: str) -> PaymentInstruction:
        try:
            return self._payments[payment_id]
        except KeyError:
            raise LifecycleError(f"unknown payment {payment_id}") from None

    @property
    def all(self) -> tuple[PaymentInstruction, ...]:
        return tuple(self._payments.values())

    def for_business(self, business_id: str) -> tuple[PaymentInstruction, ...]:
        return tuple(item for item in self._payments.values() if item.business_id == business_id)

    def blocking_cases(self, payment_id: str) -> tuple[str, ...]:
        return tuple(sorted(self._blocking_cases.get(payment_id, set())))

    def _move(self, payment: PaymentInstruction, to_state: str) -> None:
        allowed = TRANSITIONS[payment.state]
        if to_state not in allowed:
            raise LifecycleError(
                f"payment {payment.payment_id} cannot go {payment.state} -> {to_state}; "
                f"allowed: {allowed or '(terminal)'}"
            )

    def _store(self, payment: PaymentInstruction) -> PaymentInstruction:
        self._payments[payment.payment_id] = payment
        return payment

    # -- creation ----------------------------------------------------------

    def create(
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
        source_account: str = "SGD-OPERATING",
        actor_role: str = "treasury_operator",
        actor_id: str = "treasury.ops",
    ) -> PaymentInstruction:
        existing_id = self._by_instruction.get(business_instruction_id)
        if existing_id is not None:
            existing = self._payments[existing_id]
            self.duplicate_attempts.append(
                DuplicateAttempt(
                    business_instruction_id=business_instruction_id,
                    existing_payment_id=existing_id,
                    attempted_at=occurred_at,
                    note=(
                        f"a payment for {business_instruction_id} already exists "
                        f"in state {existing.state}; no second payout was created"
                    ),
                )
            )
            self._audit.record(
                occurred_at=occurred_at,
                actor_role=actor_role,
                actor_id=actor_id,
                action="payment.create",
                object_type="payment",
                object_id=existing_id,
                summary=f"duplicate instruction {business_instruction_id} returned the existing payment",
                payload={"business_instruction_id": business_instruction_id, "duplicate": True},
            )
            return existing

        if not self._may_move_money(business_id):
            raise LifecycleError(
                f"business {business_id} is not approved for payout; "
                "KYB approval gates money movement"
            )

        payment = PaymentInstruction(
            payment_id=self._ids.next("payment"),
            business_id=business_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            purpose_code=purpose_code,
            business_instruction_id=business_instruction_id,
            idempotency_key=idempotency_key,
            created_at=occurred_at,
            state="created",
            source_account=source_account,
            evidence_ids=evidence_ids,
        )
        self._store(payment)
        self._by_instruction[business_instruction_id] = payment.payment_id
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="payment.create",
            object_type="payment",
            object_id=payment.payment_id,
            summary=f"created {amount.format()} to {beneficiary_id} for {purpose_code}",
            payload={
                "business_instruction_id": business_instruction_id,
                "evidence_ids": list(evidence_ids),
            },
        )
        self._bus.publish(
            "payment.created",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject={"payment": payment.payment_id, "business": business_id, "beneficiary": beneficiary_id},
            payload={
                "amount_minor": amount.minor_units,
                "currency": amount.currency,
                "purpose_code": purpose_code,
                "evidence_ids": list(evidence_ids),
            },
            idempotency_key=f"payment.created:{idempotency_key}",
        )
        return payment

    # -- controls ----------------------------------------------------------

    def apply_controls(
        self,
        payment_id: str,
        *,
        assessment_id: str,
        intervention_level: int,
        required_approvals: int,
        required_verifications: tuple[str, ...],
        occurred_at: datetime,
    ) -> PaymentInstruction:
        """Record what the intervention engine decided this payment needs.

        The engine decides; this module only stores and enforces. Keeping the
        decision and the enforcement apart is what lets the engine be tested
        against 82 fixed cases without a ledger anywhere near it.
        """
        payment = self.get(payment_id)
        target = "awaiting_intervention" if required_verifications else "awaiting_approval"
        self._move(payment, target)
        updated = self._store(
            replace(
                payment,
                state=target,
                assessment_id=assessment_id,
                intervention_level=intervention_level,
                required_approvals=max(1, required_approvals),
                required_verifications=required_verifications,
            )
        )
        self._audit.record(
            occurred_at=occurred_at,
            actor_role="system",
            actor_id="intervention.engine",
            action="payment.create",
            object_type="payment",
            object_id=payment_id,
            summary=(
                f"intervention level {intervention_level}: {max(1, required_approvals)} approver(s), "
                f"verifications required: {', '.join(required_verifications) or 'none'}"
            ),
            payload={
                "intervention_level": intervention_level,
                "required_approvals": max(1, required_approvals),
                "required_verifications": list(required_verifications),
            },
        )
        return updated

    def record_verification(
        self,
        payment_id: str,
        verification_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        evidence_id: str | None = None,
        note: str = "",
    ) -> PaymentInstruction:
        payment = self.get(payment_id)
        if verification_id not in payment.required_verifications:
            raise LifecycleError(
                f"{verification_id!r} is not required for {payment_id}; "
                f"required: {payment.required_verifications or '(none)'}"
            )
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="payment.verify",
            object_type="payment",
            object_id=payment_id,
            summary=f"{actor_id} completed {verification_id}",
            payload={"verification": verification_id, "evidence_id": evidence_id, "note": note},
        )
        completed = tuple(dict.fromkeys(payment.completed_verifications + (verification_id,)))
        evidence_ids = payment.evidence_ids
        if evidence_id is not None and evidence_id not in evidence_ids:
            evidence_ids = evidence_ids + (evidence_id,)
        updated = replace(payment, completed_verifications=completed, evidence_ids=evidence_ids)
        if not updated.outstanding_verifications and updated.state == "awaiting_intervention":
            self._move(updated, "awaiting_approval")
            updated = replace(updated, state="awaiting_approval")
        return self._store(updated)

    def block(self, payment_id: str, case_id: str) -> None:
        """Hold a payment behind an open case. Only closing the case releases it."""
        self.get(payment_id)
        self._blocking_cases.setdefault(payment_id, set()).add(case_id)

    def release_block(self, payment_id: str, case_id: str) -> None:
        self._blocking_cases.get(payment_id, set()).discard(case_id)

    def attach_case(self, payment_id: str, case_id: str) -> PaymentInstruction:
        payment = self.get(payment_id)
        if case_id in payment.case_ids:
            return payment
        return self._store(replace(payment, case_ids=payment.case_ids + (case_id,)))

    # -- approval and release ---------------------------------------------

    def approve(
        self,
        payment_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        decision_id: str,
        reason_code: str = "reviewed_and_authorised",
        note: str = "",
        ai_brief_id: str | None = None,
    ) -> PaymentInstruction:
        payment = self.get(payment_id)
        if payment.state not in ("awaiting_approval", "awaiting_intervention"):
            raise LifecycleError(
                f"payment {payment_id} is in state {payment.state}; approvals apply to a payment awaiting one"
            )
        outstanding = payment.outstanding_verifications
        if outstanding:
            raise LifecycleError(
                f"payment {payment_id} still requires {', '.join(outstanding)}; "
                "an approval before the verification is the control being skipped"
            )
        blocking = self.blocking_cases(payment_id)
        if blocking:
            raise LifecycleError(
                f"payment {payment_id} is held behind open case(s) {', '.join(blocking)}; "
                "a compliance officer closes the case, then the payment can proceed"
            )
        already = {
            decision.actor_id
            for decision in self._audit.decisions_for(payment_id)
            if decision.action == "payment.approve"
        }
        if actor_id in already:
            raise LifecycleError(
                f"{actor_id} has already approved {payment_id}; "
                "dual approval means two people, not two clicks"
            )

        decision = self._audit.record_decision(
            decision_id=decision_id,
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="payment.approve",
            object_type="payment",
            object_id=payment_id,
            reason_code=reason_code,
            note=note,
            ai_brief_id=ai_brief_id,
        )
        approvals = payment.approval_decision_ids + (decision.decision_id,)
        updated = replace(payment, approval_decision_ids=approvals)

        if len(approvals) >= payment.required_approvals:
            if updated.state == "awaiting_intervention":
                updated = replace(updated, state="awaiting_approval")
            self._move(updated, "approved")
            updated = replace(updated, state="approved")
            self._bus.publish(
                "payment.approved",
                occurred_at=occurred_at,
                actor_role=actor_role,
                actor_id=actor_id,
                subject={"payment": payment_id, "business": payment.business_id},
                payload={
                    "approvals": list(approvals),
                    "required_approvals": payment.required_approvals,
                    "intervention_level": payment.intervention_level,
                },
                idempotency_key=f"payment.approved:{payment_id}",
            )
        return self._store(updated)

    def submit(
        self,
        payment_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
    ) -> PaymentInstruction:
        payment = self.get(payment_id)
        self._move(payment, "submitted")
        blocking = self.blocking_cases(payment_id)
        if blocking:
            raise LifecycleError(
                f"payment {payment_id} is held behind open case(s) {', '.join(blocking)}"
            )
        self._ledger.post(
            [
                Leg(account_id(payment.business_id, payment.amount.currency, "available"), -payment.amount),
                Leg(account_id(payment.business_id, payment.amount.currency, "payable"), payment.amount),
            ],
            posted_at=occurred_at,
            description=f"payout {payment_id} submitted",
            payment_id=payment_id,
        )
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="payment.submit",
            object_type="payment",
            object_id=payment_id,
            summary=f"submitted {payment.amount.format()} to the rail",
            payload={"beneficiary_id": payment.beneficiary_id},
        )
        updated = self._store(replace(payment, state="submitted", submitted_at=occurred_at))
        self._bus.publish(
            "payment.submitted",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject={"payment": payment_id, "business": payment.business_id},
            payload={"amount_minor": payment.amount.minor_units, "currency": payment.amount.currency},
            idempotency_key=f"payment.submitted:{payment.idempotency_key}",
        )
        return updated

    def accept(self, payment_id: str, *, occurred_at: datetime) -> PaymentInstruction:
        payment = self.get(payment_id)
        self._move(payment, "accepted")
        return self._store(replace(payment, state="accepted"))

    def settle(
        self,
        payment_id: str,
        *,
        occurred_at: datetime,
        settlement_id: str,
        actor_role: str = "system",
        actor_id: str = "provider.webhook",
    ) -> PaymentInstruction:
        payment = self.get(payment_id)
        self._move(payment, "settled")
        self._ledger.post(
            [
                Leg(account_id(payment.business_id, payment.amount.currency, "payable"), -payment.amount),
                Leg(account_id("", payment.amount.currency, "external"), payment.amount),
            ],
            posted_at=occurred_at,
            description=f"payout {payment_id} settled",
            payment_id=payment_id,
        )
        updated = self._store(replace(payment, state="settled", settled_at=occurred_at))
        self._bus.publish(
            "payment.settled",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject={"payment": payment_id, "business": payment.business_id},
            payload={"settlement_id": settlement_id},
            idempotency_key=f"payment.settled:{settlement_id}",
        )
        return updated

    def fail(self, payment_id: str, *, occurred_at: datetime, reason: str) -> PaymentInstruction:
        payment = self.get(payment_id)
        self._move(payment, "failed")
        if payment.state in ("submitted", "accepted"):
            self._ledger.post(
                [
                    Leg(account_id(payment.business_id, payment.amount.currency, "payable"), -payment.amount),
                    Leg(account_id(payment.business_id, payment.amount.currency, "available"), payment.amount),
                ],
                posted_at=occurred_at,
                description=f"payout {payment_id} failed: funds returned to available",
                payment_id=payment_id,
            )
        return self._store(replace(payment, state="failed", failure_reason=reason))
