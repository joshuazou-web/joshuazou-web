"""Intervention policy: the tiers, the signals, and the actions.

Ported from `think-before-click-product-case/docs/finsafe/js/b2b-data.js`. The
structure is unchanged — amount tiers with a floor, signals with a severity,
verification actions with a source — and three things were adapted:

  * the currency is SGD rather than CNY, and the tier boundaries were restated
    for a corridor whose ordinary supplier invoice is four to five figures;
  * the signal list gained four entries that only exist because CorridorOS has
    a payment object to look at: an unverified beneficiary, incomplete
    supporting evidence, a duplicate instruction, and a first payment to a
    counterparty. FinSafe could not see any of these — it had a pasted message;
  * sources kept their original identifiers, so a citation in this platform
    still resolves to the same published advisory it did in FinSafe.

The evaluation numbers behind the original ladder were measured on 82 fixed
business cases in that project, on synthetic data. They are reproduced in
`docs/EVALUATION.md` with that provenance attached, not restated as CorridorOS
results.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.money import Money

# --- amount tiers ---------------------------------------------------------


@dataclass(frozen=True)
class AmountTier:
    tier_id: str
    max_minor: int | None  # None means "no upper bound"
    floor_level: int
    label: str


# The amount sets a floor, never a ceiling. A large payment cannot be waved
# through quietly, and signal rules remain free to escalate above the floor.
AMOUNT_TIERS: tuple[AmountTier, ...] = (
    AmountTier("t0", 100_000, 0, "under SGD 1,000"),
    AmountTier("t1", 1_000_000, 1, "SGD 1,000-10,000"),
    AmountTier("t2", 4_000_000, 2, "SGD 10,000-40,000"),
    AmountTier("t3", None, 3, "SGD 40,000 and above"),
)


def tier_for(amount: Money) -> AmountTier:
    for tier in AMOUNT_TIERS:
        if tier.max_minor is None or amount.minor_units < tier.max_minor:
            return tier
    return AMOUNT_TIERS[-1]


def tier_index(tier: AmountTier) -> int:
    return AMOUNT_TIERS.index(tier)


# --- signals --------------------------------------------------------------


@dataclass(frozen=True)
class SignalSpec:
    signal_id: str
    level: int
    summary: str
    source_ids: tuple[str, ...] = ()


# Level 4 signals: the two that make a payment catastrophic rather than merely
# unusual. Both are about *who* is being paid, or who claims to have authorised it.
CRITICAL_SIGNALS: tuple[str, ...] = ("payee_account_change", "executive_instruction")

SIGNALS: dict[str, SignalSpec] = {
    spec.signal_id: spec
    for spec in (
        SignalSpec(
            "payee_account_change",
            4,
            "The supplier's bank account was changed recently",
            ("src_spf_bec_2026", "src_ic3_bec_2024"),
        ),
        SignalSpec(
            "executive_instruction",
            4,
            "The instruction claims to come from an executive and bypasses the usual channel",
            ("src_ic3_bec_2024",),
        ),
        SignalSpec(
            "payee_name_mismatch",
            3,
            "The account holder name does not match the contracted supplier",
            ("src_spf_bec_2026",),
        ),
        SignalSpec(
            "settlement_off_platform",
            3,
            "Settlement is being moved off the agreed channel",
            ("src_ic3_bec_2024",),
        ),
        SignalSpec(
            "prepayment_pressure",
            3,
            "Unusual urgency is attached to paying before the agreed schedule",
            ("src_ic3_bec_2024",),
        ),
        SignalSpec(
            "beneficiary_unverified",
            3,
            "No current independent verification of these bank details exists",
        ),
        SignalSpec(
            "duplicate_instruction",
            3,
            "An earlier payment carries the same business instruction identifier",
        ),
        SignalSpec(
            "contract_channel_change",
            2,
            "The request departs from the agreed contractual channel",
            ("src_hkpf_bec_2026",),
        ),
        SignalSpec(
            "evidence_incomplete",
            2,
            "A supporting document this payment type requires is missing",
        ),
        SignalSpec(
            "first_payment_to_beneficiary",
            1,
            "This is the first payment to this counterparty",
        ),
    )
}


# --- verification actions -------------------------------------------------


@dataclass(frozen=True)
class VerificationAction:
    action_id: str
    title: str
    detail: str
    performed_by: str


VERIFICATION_ACTIONS: dict[str, VerificationAction] = {
    action.action_id: action
    for action in (
        VerificationAction(
            "callback_known_contact",
            "Call back a known contact",
            "Telephone the supplier on the number already on file — never a number from the "
            "request itself — and confirm the account change with a named person.",
            "treasury_operator",
        ),
        VerificationAction(
            "match_payee_to_contract",
            "Match the payee to the contract",
            "Check the account holder name against the contracted entity and the purchase order.",
            "treasury_operator",
        ),
        VerificationAction(
            "obtain_change_authorisation",
            "Obtain a signed change authorisation",
            "Request the supplier's account-change letter on letterhead, signed and dated.",
            "treasury_operator",
        ),
        VerificationAction(
            "hold_and_document",
            "Hold and document",
            "Keep the payment unsubmitted and record what was checked, by whom, and when.",
            "payment_approver",
        ),
    )
}

# Level -> what an operator is being asked to do, in one sentence.
POLICY_TEXT: dict[int, str] = {
    0: "No supported risk signal, and the amount is below the reminder threshold.",
    1: "The amount alone warrants a reminder to check the payee against the contract.",
    2: "The request departs from the agreed channel or schedule and warrants a second look.",
    3: "Callback, payee-name matching and settlement-channel checks are required before releasing funds.",
    4: "Stop. A second approver and an independent callback are required before this payment may be submitted.",
}

# Approvals required at each level. Four eyes start at level 4, where the
# failure mode is an irreversible payment to an account nobody verified.
APPROVALS_BY_LEVEL: dict[int, int] = {0: 1, 1: 1, 2: 1, 3: 1, 4: 2}
