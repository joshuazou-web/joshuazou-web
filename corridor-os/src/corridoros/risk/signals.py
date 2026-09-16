"""Deterministic risk signals over a payment.

Every rule here reads facts the platform already holds — when the beneficiary's
account changed, whether a verification post-dates that change, what evidence is
on file, what was paid to this counterparty before — and returns a signal with
the identifiers it read. No model participates in detection, and none can: the
assessment is produced before the copilot is invoked, and the copilot has no
way to add to it.

**Scope, stated plainly.** This is the payment-risk rule set for the vertical
slice. The twenty transaction-integrity rules and six AML typologies from
`crossborder-riskops` (structuring, rapid movement, funnel, circular flow,
profile mismatch, missing information) are not in this package yet; porting
them onto this event stream is phase P2. The signal identifiers used here are
the ones FinSafe's business pack already used, so a rule ported later lands
next to a vocabulary that already exists rather than beside a second one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.domain import Beneficiary, PaymentInstruction, RiskSignal

RULES_VERSION = "1.0.0"

RECENT_CHANGE_WINDOW = timedelta(days=30)
DUPLICATE_WINDOW = timedelta(hours=24)

SEVERITY_WEIGHT: dict[str, int] = {"low": 10, "medium": 25, "high": 45, "critical": 70}


@dataclass(frozen=True)
class PaymentContext:
    """Everything the rules are allowed to look at, gathered once.

    Passing a context rather than a database handle is what keeps the rules
    testable: a fixed context produces a fixed assessment, which is the
    precondition for any reproducible evaluation number.
    """

    payment: PaymentInstruction
    beneficiary: Beneficiary
    now: datetime
    prior_payments: tuple[PaymentInstruction, ...] = ()
    missing_evidence_kinds: tuple[str, ...] = ()
    instruction_note: str = ""


# Phrases that, in a payment instruction, describe the request rather than the
# goods. Kept from FinSafe's business pack, where they were measured.
NOTE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("executive_instruction", "critical", "urgent request from the ceo"),
    ("executive_instruction", "critical", "instructed by the director"),
    ("prepayment_pressure", "high", "pay today"),
    ("prepayment_pressure", "high", "before close of business"),
    ("settlement_off_platform", "high", "settle outside"),
    ("payee_name_mismatch", "high", "account holder differs"),
    ("contract_channel_change", "medium", "new contact email"),
)


def evaluate(context: PaymentContext) -> tuple[RiskSignal, ...]:
    """Run every rule. Order is stable so two runs produce identical output."""
    signals: list[RiskSignal] = []
    beneficiary = context.beneficiary
    payment = context.payment

    days_since_change = beneficiary.days_since_change(context.now)
    if days_since_change is not None and beneficiary.last_changed_at is not None:
        if context.now - beneficiary.last_changed_at <= RECENT_CHANGE_WINDOW:
            signals.append(
                RiskSignal(
                    signal_id="payee_account_change",
                    severity="critical",
                    summary=(
                        f"{beneficiary.display_name} changed bank account "
                        f"{days_since_change} day(s) ago, from ...{beneficiary.previous_account_last4} "
                        f"to ...{beneficiary.account_last4}"
                    ),
                    facts={
                        "days_since_change": days_since_change,
                        "previous_account_last4": beneficiary.previous_account_last4,
                        "new_account_last4": beneficiary.account_last4,
                        "change_count": beneficiary.change_count,
                    },
                )
            )

    if not beneficiary.verification_is_current(context.now):
        reason = (
            "the verification on file pre-dates the account change"
            if beneficiary.verified_at is not None
            else "these bank details have never been independently verified"
        )
        signals.append(
            RiskSignal(
                signal_id="beneficiary_unverified",
                severity="high",
                summary=f"No current verification for {beneficiary.display_name}: {reason}",
                facts={
                    "verified_at": beneficiary.verified_at.isoformat() if beneficiary.verified_at else None,
                    "verification_method": beneficiary.verification_method,
                },
            )
        )

    settled_before = [
        item
        for item in context.prior_payments
        if item.beneficiary_id == beneficiary.beneficiary_id
        and item.payment_id != payment.payment_id
        and item.state == "settled"
    ]
    if not settled_before:
        signals.append(
            RiskSignal(
                signal_id="first_payment_to_beneficiary",
                severity="low",
                summary=f"No settled payment to {beneficiary.display_name} exists yet",
                facts={"prior_settled": 0},
            )
        )

    near_duplicates = [
        item
        for item in context.prior_payments
        if item.payment_id != payment.payment_id
        and item.beneficiary_id == payment.beneficiary_id
        and item.amount == payment.amount
        and item.state not in ("cancelled", "failed")
        and abs(item.created_at - payment.created_at) <= DUPLICATE_WINDOW
    ]
    if near_duplicates:
        signals.append(
            RiskSignal(
                signal_id="duplicate_instruction",
                severity="high",
                summary=(
                    f"{len(near_duplicates)} payment(s) of the same amount to the same supplier "
                    "were created within 24 hours"
                ),
                facts={"payment_ids": [item.payment_id for item in near_duplicates]},
            )
        )

    if context.missing_evidence_kinds:
        signals.append(
            RiskSignal(
                signal_id="evidence_incomplete",
                severity="medium",
                summary=(
                    "Required supporting documents are missing: "
                    + ", ".join(context.missing_evidence_kinds)
                ),
                facts={"missing": list(context.missing_evidence_kinds)},
            )
        )

    note = (context.instruction_note or "").lower()
    seen: set[str] = set()
    for signal_id, severity, phrase in NOTE_PATTERNS:
        if phrase in note and signal_id not in seen:
            seen.add(signal_id)
            signals.append(
                RiskSignal(
                    signal_id=signal_id,
                    severity=severity,
                    summary=f"The instruction note contains {phrase!r}",
                    facts={"matched_phrase": phrase},
                )
            )

    return tuple(signals)


def score_of(signals: tuple[RiskSignal, ...]) -> int:
    """A bounded sum of severity weights. Ordering, not probability."""
    return min(100, sum(SEVERITY_WEIGHT.get(signal.severity, 0) for signal in signals))


def band_of(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "medium"
    return "low"
