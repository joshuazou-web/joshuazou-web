"""The eleven objects every module agrees on.

Before the merge, "a payment" meant four different things. RiskOps meant a card
authorisation with a wallet and a merchant; the corridor blueprint meant a
supplier payout with a purpose code and an invoice; FinSafe meant a pasted
message about a payment; WealthGuard had no payment at all. None of them could
point at the others' objects, so nothing could be traced end to end — which is
the whole product claim.

These dataclasses are the fix. They are frozen: a state change produces a new
value through `dataclasses.replace`, and the old one stays in the event log.
Nothing here holds behaviour; the modules that own each lifecycle do. Keeping
the objects behaviourless is what lets `payments`, `risk`, `intervention` and
`evidence` share them without importing each other.

Money is always `Money`, never a number. Times are timezone-aware UTC. Every
identifier is validated on construction, so a mistyped `business_id` fails here
rather than surfacing as an empty query three screens later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .ids import validate
from .money import Money

# --- shared vocabularies --------------------------------------------------

KYB_STATES = ("draft", "submitted", "needs_information", "approved", "rejected")

PAYMENT_STATES = (
    "created",
    "awaiting_intervention",
    "awaiting_approval",
    "approved",
    "submitted",
    "accepted",
    "settled",
    "failed",
    "returned",
    "cancelled",
)

RISK_BANDS = ("low", "medium", "high", "critical")

CASE_KINDS = ("aml_investigation", "kyb_review", "payment_review")
CASE_STATES = ("open", "assigned", "awaiting_information", "closed")

EVIDENCE_KINDS = (
    "invoice",
    "purchase_order",
    "contract",
    "bank_letter",
    "beneficiary_change_authorisation",
    "incorporation_document",
    "ownership_declaration",
    "official_source",
    "callback_record",
    "provider_statement",
)

EXCEPTION_TYPES = (
    "timing",
    "fee",
    "fx",
    "duplicate",
    "missing_record",
    "amount",
    "beneficiary",
    "state",
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{value!r} is a naive datetime; CorridorOS stores UTC only")
    return value


# --- 1. BusinessProfile ---------------------------------------------------


@dataclass(frozen=True)
class BusinessProfile:
    business_id: str
    legal_name: str
    entity_country: str
    uen: str
    review_status: str
    submitted_at: datetime
    expected_monthly_volume: Money
    evidence_ids: tuple[str, ...] = ()
    evidence_version: int = 1
    decided_at: datetime | None = None
    decided_by: str | None = None
    outstanding_requests: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate(self.business_id, "business")
        if self.review_status not in KYB_STATES:
            raise ValueError(f"unknown KYB state {self.review_status!r}")
        _utc(self.submitted_at)
        for evidence_id in self.evidence_ids:
            validate(evidence_id, "evidence")

    @property
    def may_move_money(self) -> bool:
        """Collection and payout are gated on this, in one place."""
        return self.review_status == "approved"


# --- 2. Beneficiary -------------------------------------------------------


@dataclass(frozen=True)
class Beneficiary:
    beneficiary_id: str
    business_id: str
    display_name: str
    bank_country: str
    account_last4: str
    created_at: datetime
    last_changed_at: datetime | None = None
    change_count: int = 0
    verified_at: datetime | None = None
    verification_method: str | None = None
    previous_account_last4: str | None = None

    def __post_init__(self) -> None:
        validate(self.beneficiary_id, "beneficiary")
        validate(self.business_id, "business")
        _utc(self.created_at)

    def days_since_change(self, now: datetime) -> int | None:
        if self.last_changed_at is None:
            return None
        return (now - self.last_changed_at).days

    def verification_is_current(self, now: datetime) -> bool:
        """A verification performed before the last account change is stale.

        This single comparison is why "the supplier is a known counterparty"
        cannot be used to wave through a payment to an account nobody checked.
        """
        if self.verified_at is None:
            return False
        if self.last_changed_at is not None and self.verified_at < self.last_changed_at:
            return False
        return self.verified_at <= now


# --- 3. CollectionIntent --------------------------------------------------


@dataclass(frozen=True)
class CollectionIntent:
    intent_id: str
    business_id: str
    expected_amount: Money
    reference: str
    expires_at: datetime
    created_at: datetime
    status: str = "open"
    attributed_amount: Money | None = None
    provider_event_id: str | None = None

    def __post_init__(self) -> None:
        validate(self.intent_id, "intent")
        validate(self.business_id, "business")
        _utc(self.expires_at)


# --- 4. PaymentInstruction ------------------------------------------------


@dataclass(frozen=True)
class PaymentInstruction:
    payment_id: str
    business_id: str
    beneficiary_id: str
    amount: Money
    purpose_code: str
    business_instruction_id: str
    idempotency_key: str
    created_at: datetime
    state: str = "created"
    source_account: str = "SGD-OPERATING"
    evidence_ids: tuple[str, ...] = ()
    approval_decision_ids: tuple[str, ...] = ()
    required_approvals: int = 1
    required_verifications: tuple[str, ...] = ()
    completed_verifications: tuple[str, ...] = ()
    intervention_level: int | None = None
    assessment_id: str | None = None
    case_ids: tuple[str, ...] = ()
    submitted_at: datetime | None = None
    settled_at: datetime | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        validate(self.payment_id, "payment")
        validate(self.business_id, "business")
        validate(self.beneficiary_id, "beneficiary")
        if self.state not in PAYMENT_STATES:
            raise ValueError(f"unknown payment state {self.state!r}")
        _utc(self.created_at)

    @property
    def outstanding_verifications(self) -> tuple[str, ...]:
        done = set(self.completed_verifications)
        return tuple(item for item in self.required_verifications if item not in done)


# --- 5. RiskAssessment ----------------------------------------------------


@dataclass(frozen=True)
class RiskSignal:
    signal_id: str
    severity: str
    summary: str
    evidence_ids: tuple[str, ...] = ()
    facts: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskAssessment:
    assessment_id: str
    payment_id: str
    band: str
    score: int
    signals: tuple[RiskSignal, ...]
    assessed_at: datetime
    rules_version: str
    evidence_complete: bool = True
    missing_evidence_kinds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate(self.assessment_id, "assessment")
        validate(self.payment_id, "payment")
        if self.band not in RISK_BANDS:
            raise ValueError(f"unknown risk band {self.band!r}")

    def has(self, signal_id: str) -> bool:
        return any(signal.signal_id == signal_id for signal in self.signals)


# --- 6. EvidenceItem ------------------------------------------------------


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    kind: str
    title: str
    issuer: str
    issued_at: datetime | None
    checksum: str
    location: str
    excerpt: str
    business_id: str | None = None
    payment_id: str | None = None
    beneficiary_id: str | None = None
    case_id: str | None = None
    status: str = "current"
    structured_facts: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate(self.evidence_id, "evidence")
        if self.kind not in EVIDENCE_KINDS:
            raise ValueError(f"unknown evidence kind {self.kind!r}")
        for identifier, kind in (
            (self.business_id, "business"),
            (self.payment_id, "payment"),
            (self.beneficiary_id, "beneficiary"),
            (self.case_id, "case"),
        ):
            if identifier is not None:
                validate(identifier, kind)


# --- 7. ReviewCase --------------------------------------------------------


@dataclass(frozen=True)
class ReviewCase:
    case_id: str
    kind: str
    title: str
    opened_at: datetime
    sla_due_at: datetime
    priority: int
    state: str = "open"
    owner: str | None = None
    business_id: str | None = None
    payment_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    signal_ids: tuple[str, ...] = ()
    closed_at: datetime | None = None
    closure_reason: str | None = None

    def __post_init__(self) -> None:
        validate(self.case_id, "case")
        if self.kind not in CASE_KINDS:
            raise ValueError(f"unknown case kind {self.kind!r}")
        if self.state not in CASE_STATES:
            raise ValueError(f"unknown case state {self.state!r}")


# --- 8. ApprovalDecision --------------------------------------------------


@dataclass(frozen=True)
class ApprovalDecision:
    """A decision a person committed.

    The constructor refuses `actor_role="ai_copilot"`. That refusal is
    deliberately here, in the object, and not only in the function that writes
    it: a future caller that builds a decision by hand and inserts it directly
    still cannot make the copilot the author of one.
    """

    decision_id: str
    action: str
    object_type: str
    object_id: str
    actor_role: str
    actor_id: str
    reason_code: str
    occurred_at: datetime
    note: str = ""
    ai_brief_id: str | None = None
    agreed_with_ai: bool | None = None

    def __post_init__(self) -> None:
        from .authority import AI_COPILOT, can

        validate(self.decision_id, "decision")
        if self.actor_role == AI_COPILOT:
            raise ValueError(
                "an ApprovalDecision cannot have the AI copilot as its actor; "
                "the copilot advises, a person decides"
            )
        if not can(self.actor_role, self.action):
            raise ValueError(
                f"role {self.actor_role!r} may not commit {self.action!r}"
            )


# --- 9. SettlementRecord --------------------------------------------------


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    payment_id: str
    gross: Money
    fee: Money
    net: Money
    value_date: datetime
    provider_reference: str
    bank_reference: str | None = None

    def __post_init__(self) -> None:
        validate(self.settlement_id, "settlement")
        validate(self.payment_id, "payment")
        if self.net != self.gross - self.fee:
            raise ValueError(
                f"settlement {self.settlement_id}: net {self.net} does not equal "
                f"gross {self.gross} minus fee {self.fee}"
            )


# --- 10. ExceptionCase ----------------------------------------------------


@dataclass(frozen=True)
class ExceptionCase:
    exception_id: str
    exception_type: str
    summary: str
    opened_at: datetime
    due_at: datetime
    owner: str
    state: str = "open"
    payment_id: str | None = None
    settlement_id: str | None = None
    difference: Money | None = None
    evidence_ids: tuple[str, ...] = ()
    resolution_code: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None

    def __post_init__(self) -> None:
        validate(self.exception_id, "exception")
        if self.exception_type not in EXCEPTION_TYPES:
            raise ValueError(f"unknown exception type {self.exception_type!r}")


# --- 11. AuditEvent -------------------------------------------------------


@dataclass(frozen=True)
class AuditEvent:
    entry_id: str
    seq: int
    occurred_at: datetime
    actor_role: str
    actor_id: str
    action: str
    object_type: str
    object_id: str
    summary: str
    payload_json: str = "{}"
    previous_hash: str = ""
    entry_hash: str = ""

    def __post_init__(self) -> None:
        validate(self.entry_id, "audit")
