"""Pre-payment Intervention Engine.

FinSafe answered "is this message risky?" from pasted text. Here the same
algorithm reads a real `PaymentInstruction`, the deterministic `RiskAssessment`
beside it, and the state of the evidence — so the question becomes the one an
operator actually faces: **what must happen before this payment may be
submitted?**

The algorithm is the ported one, and its three properties are the reason it was
worth porting rather than replacing:

**The amount sets a floor, never a ceiling.** A large payment cannot fall below
its tier's level, and signals can only push it higher. A verified beneficiary
lowers the floor by one, which is what keeps routine instalments to known
suppliers from collecting friction they do not need.

**One override, stated explicitly.** An account change or a payee-name mismatch
on a payment in tier t2 or above pins the level to 4 regardless of how the
other inputs combine. That is the business email compromise case, and it is the
one case where the arithmetic is not allowed to average it away.

**Every decision explains what it did not choose.** `why_not_weaker` and
`why_not_stronger` come from the original engine, and they exist because a
reviewer who disagrees with a level needs to see which input produced it — not
a score.

The engine returns a decision. It does not apply it: `payments.payout` stores
the requirements and refuses the approval. A module that both decided and
enforced would be a module nobody could test with 82 fixed cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.domain import Beneficiary, PaymentInstruction, RiskAssessment
from .policy import (
    APPROVALS_BY_LEVEL,
    CRITICAL_SIGNALS,
    POLICY_TEXT,
    SIGNALS,
    VERIFICATION_ACTIONS,
    AmountTier,
    tier_for,
    tier_index,
)

ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class InterventionDecision:
    payment_id: str
    selected_level: int
    amount_tier: str
    amount_floor: int
    payee_known: bool
    drivers: tuple[str, ...]
    signal_ids: tuple[str, ...]
    required_approvals: int
    required_verifications: tuple[str, ...]
    policy: str
    why_not_weaker: str
    why_not_stronger: str
    decided_at: datetime
    engine_version: str = ENGINE_VERSION
    candidates: tuple[tuple[str, int], ...] = ()

    @property
    def requires_intervention(self) -> bool:
        return self.selected_level > 0

    def as_row(self) -> dict[str, object]:
        return {
            "payment_id": self.payment_id,
            "selected_level": self.selected_level,
            "amount_tier": self.amount_tier,
            "amount_floor": self.amount_floor,
            "payee_known": self.payee_known,
            "drivers": list(self.drivers),
            "signal_ids": list(self.signal_ids),
            "required_approvals": self.required_approvals,
            "required_verifications": list(self.required_verifications),
            "policy": self.policy,
            "why_not_weaker": self.why_not_weaker,
            "why_not_stronger": self.why_not_stronger,
            "engine_version": self.engine_version,
        }


def amount_floor(tier: AmountTier, payee_known: bool) -> int:
    """A verified payee lowers the floor by one. It never removes it."""
    return max(0, tier.floor_level - 1) if payee_known else tier.floor_level


def signal_level(signal_ids: tuple[str, ...]) -> int:
    levels = [SIGNALS[signal_id].level for signal_id in signal_ids if signal_id in SIGNALS]
    return max(levels) if levels else 0


def required_verifications_for(level: int, signal_ids: tuple[str, ...]) -> tuple[str, ...]:
    """What a person must do before this payment can be approved."""
    ordered: list[str] = []

    def add(action_id: str) -> None:
        if action_id not in ordered:
            ordered.append(action_id)

    if "payee_account_change" in signal_ids:
        add("callback_known_contact")
        add("obtain_change_authorisation")
    if "payee_name_mismatch" in signal_ids:
        add("match_payee_to_contract")
    if level >= 4:
        add("callback_known_contact")
        add("hold_and_document")
    elif level == 3:
        add("match_payee_to_contract")
    return tuple(action_id for action_id in ordered if action_id in VERIFICATION_ACTIONS)


def decide(
    payment: PaymentInstruction,
    assessment: RiskAssessment,
    beneficiary: Beneficiary,
    *,
    now: datetime,
) -> InterventionDecision:
    """Choose the intervention level for one payment, and explain the choice."""
    signal_ids = tuple(signal.signal_id for signal in assessment.signals)
    tier = tier_for(payment.amount)
    payee_known = beneficiary.verification_is_current(now)
    floor = amount_floor(tier, payee_known)
    from_signals = signal_level(signal_ids)

    # The one override: a payee change or name mismatch on a payment of any
    # consequence is a stop, however the other inputs happen to combine.
    large_payee_change = tier_index(tier) >= 2 and (
        "payee_account_change" in signal_ids or "payee_name_mismatch" in signal_ids
    )

    selected = 4 if large_payee_change else max(from_signals, floor)

    candidates = (("amount_floor_rule", floor), ("signal_rule", from_signals))
    drivers: list[str] = []
    if large_payee_change:
        drivers.append("large_payment_payee_change_override")
    if from_signals == selected and from_signals > 0:
        drivers.append("signal_rule")
    if floor == selected and floor > 0:
        drivers.append("amount_floor_rule")

    critical = [signal_id for signal_id in signal_ids if signal_id in CRITICAL_SIGNALS]
    if selected == 0:
        why_not_weaker = "No weaker level exists."
    elif large_payee_change:
        why_not_weaker = (
            "A payee-account change or payee-name mismatch on a payment of this size is pinned "
            "to a stop; averaging it against the other inputs is exactly the mistake this rule exists to prevent."
        )
    elif floor == selected and floor > from_signals:
        why_not_weaker = (
            f"Amount tier {tier.tier_id} ({tier.label}) sets this floor even with no stronger signal."
        )
    else:
        why_not_weaker = (
            f"A weaker level would not address {', '.join(critical or signal_ids) or 'the strongest signal found'}."
        )

    why_not_stronger = (
        "Level 4 is the maximum."
        if selected == 4
        else "No deterministic rule supports a stronger intervention from the available inputs."
    )

    return InterventionDecision(
        payment_id=payment.payment_id,
        selected_level=selected,
        amount_tier=tier.tier_id,
        amount_floor=floor,
        payee_known=payee_known,
        drivers=tuple(drivers),
        signal_ids=signal_ids,
        required_approvals=APPROVALS_BY_LEVEL[selected],
        required_verifications=required_verifications_for(selected, signal_ids),
        policy=POLICY_TEXT[selected],
        why_not_weaker=why_not_weaker,
        why_not_stronger=why_not_stronger,
        decided_at=now,
        candidates=candidates,
    )
