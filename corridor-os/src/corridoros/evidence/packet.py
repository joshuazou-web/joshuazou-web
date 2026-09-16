"""Evidence packets, and what a decision is still missing.

The packet is assembled deterministically — by identifier, from the register —
before any summarising happens. That ordering is the point: the copilot writes
about a packet someone else selected, so it cannot quietly widen its own
evidence base, and "which documents were in front of the reviewer" is a
recorded fact rather than a model's recollection.

`missing_kinds` is computed from a table, not inferred. When a payment's
beneficiary changed recently, a signed change authorisation and a callback
record become required, and their absence is a fact about the packet — which is
what lets the copilot "identify missing information" without exercising any
judgement it is not allowed to have.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.domain import Beneficiary, BusinessProfile, EvidenceItem, PaymentInstruction
from .store import EvidenceStore

# What each context requires on file. Deliberately a table: a reviewer can read
# it, and a test can assert against it.
REQUIRED_FOR_PURPOSE: dict[str, tuple[str, ...]] = {
    "SUPPLIER_INVOICE": ("invoice", "purchase_order"),
    "SERVICES": ("invoice", "contract"),
    "REFUND": ("invoice",),
}

REQUIRED_AFTER_BENEFICIARY_CHANGE: tuple[str, ...] = (
    "beneficiary_change_authorisation",
    "callback_record",
)

REQUIRED_FOR_KYB: tuple[str, ...] = ("incorporation_document", "ownership_declaration")


@dataclass(frozen=True)
class EvidencePacket:
    subject_id: str
    subject_type: str
    items: tuple[EvidenceItem, ...]
    required_kinds: tuple[str, ...]
    missing_kinds: tuple[str, ...]
    assembled_at: datetime

    @property
    def is_complete(self) -> bool:
        return not self.missing_kinds

    @property
    def evidence_ids(self) -> frozenset[str]:
        """The closed set a citation must resolve into."""
        return frozenset(item.evidence_id for item in self.items)

    def as_row(self) -> dict[str, object]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "evidence_ids": sorted(self.evidence_ids),
            "required_kinds": list(self.required_kinds),
            "missing_kinds": list(self.missing_kinds),
            "complete": self.is_complete,
        }


def assemble_for_payment(
    store: EvidenceStore,
    payment: PaymentInstruction,
    beneficiary: Beneficiary,
    *,
    now: datetime,
    recent_change_days: int = 30,
) -> EvidencePacket:
    items = list(store.for_payment(payment.payment_id))
    seen = {item.evidence_id for item in items}
    for evidence_id in payment.evidence_ids:
        if evidence_id not in seen and store.resolves(evidence_id):
            items.append(store.get(evidence_id))
            seen.add(evidence_id)
    for item in store.for_beneficiary(beneficiary.beneficiary_id):
        if item.evidence_id not in seen:
            items.append(item)
            seen.add(item.evidence_id)

    required = list(REQUIRED_FOR_PURPOSE.get(payment.purpose_code, ()))
    days = beneficiary.days_since_change(now)
    if days is not None and days <= recent_change_days:
        required.extend(REQUIRED_AFTER_BENEFICIARY_CHANGE)

    # A requirement is satisfied only by evidence attached to *this* payment.
    # The supplier's previous purchase order is in the packet as context — it is
    # useful to the reviewer — but letting it tick the "purchase order" box would
    # mean last quarter's paperwork authorising this quarter's money.
    held = {
        item.kind
        for item in items
        if item.status == "current" and item.payment_id == payment.payment_id
    }
    missing = tuple(kind for kind in dict.fromkeys(required) if kind not in held)

    return EvidencePacket(
        subject_id=payment.payment_id,
        subject_type="payment",
        items=tuple(items),
        required_kinds=tuple(dict.fromkeys(required)),
        missing_kinds=missing,
        assembled_at=now,
    )


def assemble_for_business(
    store: EvidenceStore, business: BusinessProfile, *, now: datetime
) -> EvidencePacket:
    items = store.for_business(business.business_id)
    held = {item.kind for item in items if item.status == "current"}
    missing = tuple(kind for kind in REQUIRED_FOR_KYB if kind not in held)
    return EvidencePacket(
        subject_id=business.business_id,
        subject_type="business",
        items=items,
        required_kinds=REQUIRED_FOR_KYB,
        missing_kinds=missing,
        assembled_at=now,
    )
