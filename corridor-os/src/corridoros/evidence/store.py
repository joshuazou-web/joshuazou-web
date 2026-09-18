"""The evidence register.

WealthGuard's contribution to CorridorOS is not its subject matter — nobody
here is asking whether SPY is suitable — it is its discipline about evidence:
a claim is worth what its source is worth, a source has a date and a checksum,
and an answer that cannot cite one should not be given.

An `EvidenceItem` here is an invoice, a purchase order, a signed account-change
letter, a callback record, or a published advisory. All of them carry the same
four things WealthGuard required of a document chunk: a checksum, a location
inside the source, an excerpt, and a date. That uniformity is what lets the
copilot cite a supplier's invoice and a police advisory in the same brief
without either being harder to check than the other.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from ..core.domain import EvidenceItem
from ..core.errors import EvidenceError
from ..core.ids import IdFactory


def checksum_of(text: str) -> str:
    """SHA-256 over the excerpt, so a later edit to the record is detectable."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EvidenceStore:
    def __init__(self, ids: IdFactory | None = None) -> None:
        self._ids = ids or IdFactory("ev")
        self._items: dict[str, EvidenceItem] = {}

    def add(
        self,
        *,
        kind: str,
        title: str,
        issuer: str,
        excerpt: str,
        location: str,
        issued_at: datetime | None = None,
        business_id: str | None = None,
        payment_id: str | None = None,
        beneficiary_id: str | None = None,
        case_id: str | None = None,
        status: str = "current",
        structured_facts: dict[str, str] | None = None,
        evidence_id: str | None = None,
    ) -> EvidenceItem:
        item = EvidenceItem(
            evidence_id=evidence_id or self._ids.next("evidence"),
            kind=kind,
            title=title,
            issuer=issuer,
            issued_at=issued_at,
            checksum=checksum_of(excerpt),
            location=location,
            excerpt=excerpt,
            business_id=business_id,
            payment_id=payment_id,
            beneficiary_id=beneficiary_id,
            case_id=case_id,
            status=status,
            structured_facts=dict(structured_facts or {}),
        )
        self._items[item.evidence_id] = item
        return item

    def link(self, evidence_id: str, **links: str) -> EvidenceItem:
        """Attach an existing item to a payment or case discovered later."""
        from dataclasses import replace

        item = self.get(evidence_id)
        updated = replace(item, **links)
        self._items[evidence_id] = updated
        return updated

    def get(self, evidence_id: str) -> EvidenceItem:
        try:
            return self._items[evidence_id]
        except KeyError:
            raise EvidenceError(
                f"{evidence_id} does not resolve to any evidence on file"
            ) from None

    def resolves(self, evidence_id: str) -> bool:
        return evidence_id in self._items

    @property
    def all(self) -> tuple[EvidenceItem, ...]:
        return tuple(self._items.values())

    def for_payment(self, payment_id: str) -> tuple[EvidenceItem, ...]:
        return tuple(item for item in self._items.values() if item.payment_id == payment_id)

    def for_business(self, business_id: str) -> tuple[EvidenceItem, ...]:
        return tuple(item for item in self._items.values() if item.business_id == business_id)

    def for_beneficiary(self, beneficiary_id: str) -> tuple[EvidenceItem, ...]:
        return tuple(item for item in self._items.values() if item.beneficiary_id == beneficiary_id)

    def kinds_for_business(self, business_id: str) -> set[str]:
        return {item.kind for item in self.for_business(business_id) if item.status == "current"}

    def verify_checksums(self) -> tuple[str, ...]:
        """Identifiers whose excerpt no longer matches the checksum on file."""
        return tuple(
            item.evidence_id
            for item in self._items.values()
            if checksum_of(item.excerpt) != item.checksum
        )
