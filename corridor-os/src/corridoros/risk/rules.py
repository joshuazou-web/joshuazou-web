"""Deterministic rules over one payment.

Adapted from `crossborder-riskops/src/riskops/risk/rules.py`. Its twenty rules
were written for card acquiring — authorisation versus capture, chargebacks,
merchant category codes, device fingerprints — and a corridor payout has none of
those. What carried over is the structure and the judgement inside it: a rule is
a named specification with a family, a severity, a printed reason and the fields
it read, so an operator can argue with it.

Twenty-one rules, in eight families. Eleven are the source's rules with the
subject changed (duplication, velocity, amount anomaly, FX tolerance, fee
schedule, stale quote, shared payout account, missing evidence, untrusted
instructions, authority claims, quarantined events); the rest replace
card-specific rules with the corridor equivalents — a beneficiary's account
changing, a verification that pre-dates that change, a purpose outside the
declared activity, a ledger that disagrees with the provider's advice.

**No model participates.** Detection, severity and scoring are all deterministic,
and the assessment is produced before the copilot is ever invoked. The copilot
has no way to add a signal, remove one, or change a severity.

A rule that reads a field the context does not carry returns nothing rather than
guessing. `RiskSignal.rule_id` names the rule; `signal_id` keeps the vocabulary
the intervention ladder was measured against, so a rule with no equivalent there
contributes to the risk band and the AML queue without silently moving an
intervention level the ladder's evaluation never covered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..core.domain import Beneficiary, BusinessProfile, PaymentInstruction, RiskSignal
from ..core.money import Money

RULES_VERSION = "2.0.0"

SEVERITY_WEIGHT: dict[str, int] = {"low": 10, "medium": 25, "high": 45, "critical": 70}

RECENT_CHANGE_WINDOW = timedelta(days=30)
DUPLICATE_WINDOW = timedelta(hours=24)
VELOCITY_WINDOW = timedelta(hours=24)
VELOCITY_MULTIPLE = 3.0
AMOUNT_ANOMALY_MULTIPLE = 5.0
FX_TOLERANCE_BPS = 75
FEE_TOLERANCE_BPS = 50


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    family: str
    severity: str
    title: str
    reason: str
    reads: tuple[str, ...]
    signal_id: str = ""

    def signal_key(self) -> str:
        return self.signal_id or self.rule_id


def _spec(
    rule_id: str,
    family: str,
    severity: str,
    title: str,
    reason: str,
    reads: tuple[str, ...],
    signal_id: str = "",
) -> tuple[str, RuleSpec]:
    return rule_id, RuleSpec(rule_id, family, severity, title, reason, reads, signal_id)


RULES: dict[str, RuleSpec] = dict(
    (
        # --- duplication --------------------------------------------------
        _spec(
            "R101_DUPLICATE_INSTRUCTION",
            "duplication",
            "high",
            "A payment for this business instruction already exists",
            "The same purchase order or instruction identifier was submitted again. The engine "
            "returned the first payment rather than creating a second one; this rule records "
            "that it happened, because a retry loop is worth knowing about.",
            ("business_instruction_id",),
            "duplicate_instruction",
        ),
        _spec(
            "R102_NEAR_DUPLICATE_PAYMENT",
            "duplication",
            "high",
            "Same amount to the same supplier inside 24 hours",
            "Two payments of the same amount to the same beneficiary under different instruction "
            "identifiers. Idempotency cannot catch this one — the instruction identifiers differ — "
            "so it is a question for a person.",
            ("beneficiary_id", "amount", "created_at"),
            "duplicate_instruction",
        ),
        # --- integrity ----------------------------------------------------
        _spec(
            "R103_QUARANTINED_EVENTS",
            "integrity",
            "low",
            "The provider feed sent events this payment could not accept",
            "One or more events were illegal for the state the payment was in and were "
            "quarantined. The ledger is intact; the upstream feed is not.",
            ("quarantined_event_count",),
        ),
        _spec(
            "R104_LEDGER_SETTLEMENT_MISMATCH",
            "integrity",
            "high",
            "The ledger and the provider disagree about what moved",
            "What the product's own books say left the business does not equal the gross the "
            "provider reports. Someone is short, and it is either the business or the book.",
            ("ledger_outflow", "settlement_gross"),
        ),
        # --- velocity and amount -----------------------------------------
        _spec(
            "R201_BUSINESS_VELOCITY",
            "velocity",
            "high",
            "Payout velocity far above this business's own baseline",
            "More payments in the window than this business's own history supports. Busy is not "
            "suspicious; busy *for this payer* is worth a look.",
            ("business_id", "created_at"),
        ),
        _spec(
            "R202_AMOUNT_ANOMALY",
            "velocity",
            "high",
            "Amount far above this business's usual payment",
            "The payment is several times the business's typical ticket. Large is not suspicious; "
            "large for this payer is.",
            ("amount", "business_id"),
        ),
        _spec(
            "R203_ROUND_AMOUNT_REPEAT",
            "velocity",
            "medium",
            "Repeated identical round amounts to one supplier",
            "Invoices rarely land on the same round figure twice. A repeated round amount is "
            "either a standing arrangement — which the contract will show — or it is not "
            "invoice-driven at all.",
            ("amount", "beneficiary_id"),
        ),
        # --- beneficiary --------------------------------------------------
        _spec(
            "R301_BENEFICIARY_ACCOUNT_CHANGE",
            "beneficiary",
            "critical",
            "The supplier's bank account changed recently",
            "Business email compromise works by changing where the money goes. A recent change is "
            "the single highest-value fact on this payment.",
            ("beneficiary.last_changed_at", "beneficiary.account_last4"),
            "payee_account_change",
        ),
        _spec(
            "R302_BENEFICIARY_UNVERIFIED",
            "beneficiary",
            "high",
            "No current independent verification of these bank details",
            "Either the details were never verified, or the verification on file pre-dates the "
            "account change — in which case it verified a different account.",
            ("beneficiary.verified_at", "beneficiary.last_changed_at"),
            "beneficiary_unverified",
        ),
        _spec(
            "R303_FIRST_PAYMENT_TO_BENEFICIARY",
            "beneficiary",
            "low",
            "First payment to this counterparty",
            "No settled payment to this supplier exists yet. Ordinary on its own — every "
            "relationship starts once — and it carries weight only in combination.",
            ("beneficiary_id",),
            "first_payment_to_beneficiary",
        ),
        _spec(
            "R304_BENEFICIARY_COUNTRY_SHIFT",
            "beneficiary",
            "high",
            "Payment routed to a country the supplier is not registered in",
            "The receiving bank is in a different jurisdiction from the supplier on the contract. "
            "There are good reasons for this; none of them are visible from the payment alone.",
            ("beneficiary.bank_country", "beneficiary.registered_country"),
        ),
        _spec(
            "R305_SHARED_BENEFICIARY_ACCOUNT",
            "network",
            "medium",
            "This account receives from several unrelated businesses",
            "Shared payout accounts are not ordinary between unrelated payers. A collection agent "
            "and a mule account look identical here, which is exactly why a person decides.",
            ("beneficiary.account_last4",),
        ),
        # --- FX and fees --------------------------------------------------
        _spec(
            "R401_FX_OUT_OF_TOLERANCE",
            "fx_fee",
            "high",
            "Settlement is outside FX tolerance of the booked quote",
            "The amount settled does not follow from the instruction at the rate on file, beyond "
            f"the {FX_TOLERANCE_BPS} basis-point tolerance.",
            ("fx_rate_booked", "fx_rate_applied"),
        ),
        _spec(
            "R402_FEE_OFF_SCHEDULE",
            "fx_fee",
            "medium",
            "Fee does not match the corridor's schedule",
            "The fee charged is not what this corridor and payment size produce.",
            ("settlement_fee", "expected_fee"),
        ),
        _spec(
            "R403_STALE_FX_QUOTE",
            "fx_fee",
            "medium",
            "The conversion behind this payment used an expired quote",
            "The quote had expired before it was executed. The rate applied was not a rate the "
            "payer was ever shown. The FX desk fails closed on this, so a signal here means the "
            "record disagrees with the desk.",
            ("fx_quote_expires_at", "fx_executed_at"),
        ),
        # --- profile ------------------------------------------------------
        _spec(
            "R501_PURPOSE_OFF_PROFILE",
            "profile",
            "medium",
            "Purpose code outside the entity's declared activity",
            "The purpose does not belong to what this business said it does. Often a coding error "
            "at the payer's end — and sometimes not.",
            ("purpose_code", "business.industry"),
        ),
        _spec(
            "R502_VOLUME_ABOVE_DECLARED",
            "profile",
            "medium",
            "Month-to-date payouts far above the declared expectation",
            "The entity is moving several times what it told us at onboarding. The expectation may "
            "simply be stale, which is itself a KYB refresh.",
            ("business.expected_monthly_volume",),
        ),
        # --- completeness and instruction text ----------------------------
        _spec(
            "R801_MISSING_EVIDENCE",
            "completeness",
            "medium",
            "Required supporting evidence is missing",
            "A document this payment type requires is absent. This is not a risk claim; it is the "
            "reason the payment cannot be decided yet.",
            ("evidence_ids", "purpose_code"),
            "evidence_incomplete",
        ),
        _spec(
            "R802_UNTRUSTED_INSTRUCTIONS",
            "completeness",
            "high",
            "Instruction text contains directions aimed at an automated reader",
            "Supplier-supplied text is attacker-controlled. Text addressing a model rather than a "
            "person is treated as an attack surface and quarantined before any AI reads it.",
            ("instruction_note",),
        ),
        _spec(
            "R803_AUTHORITY_CLAIM",
            "completeness",
            "high",
            "Instruction text claims an approval that is not in the system",
            "The note asserts a pre-approval, exception or sign-off. No such record exists, and an "
            "assertion in free text is not an authorisation.",
            ("instruction_note",),
        ),
        _spec(
            "R804_INSTRUCTION_LANGUAGE",
            "completeness",
            "high",
            "Instruction text carries a known business-payment risk pattern",
            "Urgency, an executive bypassing the usual channel, settlement moved off the agreed "
            "channel, or a payee name that does not match the contract. These are the patterns the "
            "intervention ladder was measured on.",
            ("instruction_note",),
        ),
    )
)

FAMILIES: tuple[str, ...] = tuple(dict.fromkeys(spec.family for spec in RULES.values()))

# Phrases that describe the *request* rather than the goods. Kept from FinSafe's
# business pack, where they were measured, with their signal identifiers intact.
NOTE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("executive_instruction", "critical", "urgent request from the ceo"),
    ("executive_instruction", "critical", "instructed by the director"),
    ("prepayment_pressure", "high", "pay today"),
    ("prepayment_pressure", "high", "before close of business"),
    ("settlement_off_platform", "high", "settle outside"),
    ("payee_name_mismatch", "high", "account holder differs"),
    ("contract_channel_change", "medium", "new contact email"),
)

ON_PROFILE_PURPOSES: dict[str, tuple[str, ...]] = {
    "wholesale_trade": ("SUPPLIER_INVOICE", "LOGISTICS", "CUSTOMS_DUTY", "SALARY", "RENT"),
    "electronics_manufacturing": ("SUPPLIER_INVOICE", "COMPONENTS", "LOGISTICS", "SALARY"),
    "software_services": ("SALARY", "CLOUD_SERVICES", "CONTRACTOR_FEE", "RENT", "SERVICES"),
    "logistics": ("FUEL", "SALARY", "SUPPLIER_INVOICE", "CUSTOMS_DUTY"),
    "consumer_goods": ("SUPPLIER_INVOICE", "MARKETING", "LOGISTICS", "SALARY"),
}


@dataclass(frozen=True)
class PaymentContext:
    """Everything the rules are allowed to look at, gathered once.

    Passing a context rather than a database handle is what keeps the rules
    testable: a fixed context produces a fixed assessment, which is the
    precondition for any reproducible evaluation number. Optional fields default
    to absent, and a rule whose inputs are absent returns nothing rather than
    guessing.
    """

    payment: PaymentInstruction
    beneficiary: Beneficiary
    now: datetime
    prior_payments: tuple[PaymentInstruction, ...] = ()
    missing_evidence_kinds: tuple[str, ...] = ()
    instruction_note: str = ""
    business: BusinessProfile | None = None
    duplicate_attempt: bool = False
    quarantined_event_count: int = 0
    ledger_outflow: Money | None = None
    settlement_gross: Money | None = None
    settlement_fee: Money | None = None
    expected_fee: Money | None = None
    fx_quote_expired: bool = False
    fx_rate_booked: str = ""
    fx_rate_applied: str = ""
    beneficiary_registered_country: str = ""
    other_payer_count: int = 0
    month_to_date: Money | None = None
    industry: str = ""
    extra_facts: dict[str, object] = field(default_factory=dict)


def _signal(rule_id: str, summary: str, facts: dict[str, object] | None = None) -> RiskSignal:
    spec = RULES[rule_id]
    return RiskSignal(
        signal_id=spec.signal_key(),
        severity=spec.severity,
        summary=summary,
        facts={"rule_id": rule_id, "family": spec.family, **(facts or {})},
    )


def evaluate(context: PaymentContext) -> tuple[RiskSignal, ...]:
    """Run every rule. Order is stable, so two runs produce identical output."""
    signals: list[RiskSignal] = []
    payment = context.payment
    beneficiary = context.beneficiary
    now = context.now

    # --- duplication ------------------------------------------------------
    if context.duplicate_attempt:
        signals.append(
            _signal(
                "R101_DUPLICATE_INSTRUCTION",
                f"Instruction {payment.business_instruction_id} was submitted more than once; "
                "the existing payment was returned and no second payout was created.",
                {"business_instruction_id": payment.business_instruction_id},
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
            _signal(
                "R102_NEAR_DUPLICATE_PAYMENT",
                f"{len(near_duplicates)} payment(s) of {payment.amount.format()} to the same "
                "supplier were created within 24 hours under different instruction identifiers.",
                {"payment_ids": [item.payment_id for item in near_duplicates]},
            )
        )

    # --- integrity --------------------------------------------------------
    if context.quarantined_event_count:
        signals.append(
            _signal(
                "R103_QUARANTINED_EVENTS",
                f"{context.quarantined_event_count} provider event(s) were illegal for this "
                "payment's state and were quarantined.",
                {"quarantined_event_count": context.quarantined_event_count},
            )
        )

    if context.ledger_outflow is not None and context.settlement_gross is not None:
        if context.ledger_outflow != context.settlement_gross:
            signals.append(
                _signal(
                    "R104_LEDGER_SETTLEMENT_MISMATCH",
                    f"The ledger moved {context.ledger_outflow.format()} while the provider "
                    f"reports {context.settlement_gross.format()} gross.",
                    {
                        "ledger_outflow_minor": context.ledger_outflow.minor_units,
                        "settlement_gross_minor": context.settlement_gross.minor_units,
                    },
                )
            )

    # --- velocity and amount ---------------------------------------------
    recent = [
        item
        for item in context.prior_payments
        if item.payment_id != payment.payment_id
        and payment.created_at - VELOCITY_WINDOW <= item.created_at <= payment.created_at
    ]
    history = [item for item in context.prior_payments if item.payment_id != payment.payment_id]
    if history:
        daily_baseline = max(1.0, len(history) / 90)
        if len(recent) > max(3, daily_baseline * VELOCITY_MULTIPLE):
            signals.append(
                _signal(
                    "R201_BUSINESS_VELOCITY",
                    f"{len(recent)} payments in 24 hours against a baseline near "
                    f"{daily_baseline:.1f} a day for this business.",
                    {"recent_count": len(recent), "baseline_per_day": round(daily_baseline, 2)},
                )
            )

        typical = sorted(item.amount.minor_units for item in history)[len(history) // 2]
        if typical and payment.amount.minor_units > typical * AMOUNT_ANOMALY_MULTIPLE:
            signals.append(
                _signal(
                    "R202_AMOUNT_ANOMALY",
                    f"{payment.amount.format()} is "
                    f"{payment.amount.minor_units / typical:.1f}× this business's median payment.",
                    {"median_minor": typical, "amount_minor": payment.amount.minor_units},
                )
            )

    round_repeats = [
        item
        for item in history
        if item.beneficiary_id == payment.beneficiary_id and item.amount == payment.amount
    ]
    if round_repeats and payment.amount.minor_units % 100_000 == 0:
        signals.append(
            _signal(
                "R203_ROUND_AMOUNT_REPEAT",
                f"{payment.amount.format()} is a round figure already paid "
                f"{len(round_repeats)} time(s) to this supplier.",
                {"repeat_count": len(round_repeats)},
            )
        )

    # --- beneficiary ------------------------------------------------------
    days_since_change = beneficiary.days_since_change(now)
    if beneficiary.last_changed_at is not None and now - beneficiary.last_changed_at <= RECENT_CHANGE_WINDOW:
        signals.append(
            _signal(
                "R301_BENEFICIARY_ACCOUNT_CHANGE",
                f"{beneficiary.display_name} changed bank account {days_since_change} day(s) ago, "
                f"from ...{beneficiary.previous_account_last4} to ...{beneficiary.account_last4}.",
                {
                    "days_since_change": days_since_change,
                    "previous_account_last4": beneficiary.previous_account_last4,
                    "new_account_last4": beneficiary.account_last4,
                    "change_count": beneficiary.change_count,
                },
            )
        )

    if not beneficiary.verification_is_current(now):
        reason = (
            "the verification on file pre-dates the account change"
            if beneficiary.verified_at is not None
            else "these bank details have never been independently verified"
        )
        signals.append(
            _signal(
                "R302_BENEFICIARY_UNVERIFIED",
                f"No current verification for {beneficiary.display_name}: {reason}.",
                {
                    "verified_at": beneficiary.verified_at.isoformat()
                    if beneficiary.verified_at
                    else None,
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
            _signal(
                "R303_FIRST_PAYMENT_TO_BENEFICIARY",
                f"No settled payment to {beneficiary.display_name} exists yet.",
                {"prior_settled": 0},
            )
        )

    registered = context.beneficiary_registered_country
    if registered and registered != beneficiary.bank_country:
        signals.append(
            _signal(
                "R304_BENEFICIARY_COUNTRY_SHIFT",
                f"{beneficiary.display_name} is registered in {registered} but the receiving bank "
                f"is in {beneficiary.bank_country}.",
                {"registered_country": registered, "bank_country": beneficiary.bank_country},
            )
        )

    if context.other_payer_count > 1:
        signals.append(
            _signal(
                "R305_SHARED_BENEFICIARY_ACCOUNT",
                f"This account also receives payouts from {context.other_payer_count - 1} other "
                "business(es) on the platform.",
                {"payer_count": context.other_payer_count},
            )
        )

    # --- FX and fees ------------------------------------------------------
    if context.fx_rate_booked and context.fx_rate_applied:
        booked = float(context.fx_rate_booked)
        applied = float(context.fx_rate_applied)
        if booked and abs(applied - booked) / booked * 10_000 > FX_TOLERANCE_BPS:
            signals.append(
                _signal(
                    "R401_FX_OUT_OF_TOLERANCE",
                    f"Applied rate {applied} differs from booked rate {booked} by more than "
                    f"{FX_TOLERANCE_BPS} basis points.",
                    {"booked": context.fx_rate_booked, "applied": context.fx_rate_applied},
                )
            )

    if context.settlement_fee is not None and context.expected_fee is not None:
        gap = abs(context.settlement_fee.minor_units - context.expected_fee.minor_units)
        base = max(1, context.expected_fee.minor_units)
        if gap / base * 10_000 > FEE_TOLERANCE_BPS:
            signals.append(
                _signal(
                    "R402_FEE_OFF_SCHEDULE",
                    f"Fee {context.settlement_fee.format()} against an expected "
                    f"{context.expected_fee.format()} for this corridor and size.",
                    {
                        "fee_minor": context.settlement_fee.minor_units,
                        "expected_minor": context.expected_fee.minor_units,
                    },
                )
            )

    if context.fx_quote_expired:
        signals.append(
            _signal(
                "R403_STALE_FX_QUOTE",
                "The conversion behind this payment is recorded against a quote that had expired.",
                {"fx_quote_expired": True},
            )
        )

    # --- profile ----------------------------------------------------------
    industry = context.industry or (context.extra_facts.get("industry") if context.extra_facts else "")
    if industry:
        on_profile = ON_PROFILE_PURPOSES.get(str(industry), ())
        if on_profile and payment.purpose_code not in on_profile:
            signals.append(
                _signal(
                    "R501_PURPOSE_OFF_PROFILE",
                    f"Purpose {payment.purpose_code} is outside the declared activity "
                    f"({industry}).",
                    {"purpose_code": payment.purpose_code, "industry": industry},
                )
            )

    if context.business is not None and context.month_to_date is not None:
        expected = context.business.expected_monthly_volume
        if expected.minor_units and context.month_to_date.minor_units > expected.minor_units * 4:
            ratio = context.month_to_date.minor_units / expected.minor_units
            signals.append(
                _signal(
                    "R502_VOLUME_ABOVE_DECLARED",
                    f"{context.month_to_date.format()} month-to-date against a declared "
                    f"{expected.format()} a month — {ratio:.1f}×.",
                    {"ratio": round(ratio, 2)},
                )
            )

    # --- completeness and instruction text --------------------------------
    if context.missing_evidence_kinds:
        signals.append(
            _signal(
                "R801_MISSING_EVIDENCE",
                "Required supporting documents are missing: "
                + ", ".join(context.missing_evidence_kinds),
                {"missing": list(context.missing_evidence_kinds)},
            )
        )

    note = context.instruction_note or ""
    if note:
        from ..evidence.guardrails import match_authority_patterns, match_injection_patterns

        injection = match_injection_patterns(note)
        if injection:
            signals.append(
                _signal(
                    "R802_UNTRUSTED_INSTRUCTIONS",
                    "The instruction note addresses an automated reader: "
                    + ", ".join(injection)
                    + ". It was quarantined before any AI read it.",
                    {"labels": injection},
                )
            )
        authority = match_authority_patterns(note)
        if authority:
            signals.append(
                _signal(
                    "R803_AUTHORITY_CLAIM",
                    "The instruction note claims an approval that is not in the system: "
                    + ", ".join(authority)
                    + ".",
                    {"labels": authority},
                )
            )

        lowered = note.lower()
        seen: set[str] = set()
        for signal_id, severity, phrase in NOTE_PATTERNS:
            if phrase in lowered and signal_id not in seen:
                seen.add(signal_id)
                signals.append(
                    RiskSignal(
                        signal_id=signal_id,
                        severity=severity,
                        summary=f"The instruction note contains {phrase!r}",
                        facts={
                            "rule_id": "R804_INSTRUCTION_LANGUAGE",
                            "family": "completeness",
                            "matched_phrase": phrase,
                        },
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
