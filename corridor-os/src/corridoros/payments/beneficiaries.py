"""Supplier bank details, and the one fact that matters most about them: when
they last changed.

Business email compromise works by changing where the money goes, so a
beneficiary record that only holds current details is missing the field the
whole control depends on. This registry keeps `last_changed_at`,
`previous_account_last4` and `change_count`, and publishes `beneficiary.changed`
so that Risk and the intervention engine learn about it without either of them
polling the payments module.

`verification_is_current` (on the object itself) is the second half: a
verification recorded before the account changed does not count. "Known
supplier" cannot be used to lower friction on an account nobody has checked.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from ..core.audit import AuditLog
from ..core.domain import Beneficiary
from ..core.errors import LifecycleError
from ..core.events import EventBus


class BeneficiaryRegistry:
    def __init__(self, bus: EventBus, audit: AuditLog) -> None:
        self._bus = bus
        self._audit = audit
        self._beneficiaries: dict[str, Beneficiary] = {}

    def get(self, beneficiary_id: str) -> Beneficiary:
        try:
            return self._beneficiaries[beneficiary_id]
        except KeyError:
            raise LifecycleError(f"unknown beneficiary {beneficiary_id}") from None

    @property
    def all(self) -> tuple[Beneficiary, ...]:
        return tuple(self._beneficiaries.values())

    def register(
        self,
        beneficiary: Beneficiary,
        *,
        actor_role: str = "treasury_operator",
        actor_id: str = "treasury.ops",
    ) -> Beneficiary:
        self._beneficiaries[beneficiary.beneficiary_id] = beneficiary
        self._audit.record(
            occurred_at=beneficiary.created_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="beneficiary.create",
            object_type="beneficiary",
            object_id=beneficiary.beneficiary_id,
            summary=f"registered {beneficiary.display_name} ({beneficiary.bank_country})",
            payload={"account_last4": beneficiary.account_last4},
        )
        return beneficiary

    def change_account(
        self,
        beneficiary_id: str,
        *,
        new_account_last4: str,
        occurred_at: datetime,
        actor_role: str = "treasury_operator",
        actor_id: str = "treasury.ops",
        source: str = "email_from_supplier",
    ) -> Beneficiary:
        """Change where a supplier's money goes, and tell the platform about it."""
        current = self.get(beneficiary_id)
        updated = replace(
            current,
            previous_account_last4=current.account_last4,
            account_last4=new_account_last4,
            last_changed_at=occurred_at,
            change_count=current.change_count + 1,
        )
        self._beneficiaries[beneficiary_id] = updated
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="beneficiary.change",
            object_type="beneficiary",
            object_id=beneficiary_id,
            summary=(
                f"account changed from ...{current.account_last4} to ...{new_account_last4} "
                f"(source: {source})"
            ),
            payload={
                "previous_account_last4": current.account_last4,
                "new_account_last4": new_account_last4,
                "source": source,
            },
        )
        self._bus.publish(
            "beneficiary.changed",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject={"beneficiary": beneficiary_id, "business": current.business_id},
            payload={
                "previous_account_last4": current.account_last4,
                "new_account_last4": new_account_last4,
                "source": source,
                "change_count": updated.change_count,
            },
            idempotency_key=f"beneficiary.changed:{beneficiary_id}:{updated.change_count}",
        )
        return updated

    def record_verification(
        self,
        beneficiary_id: str,
        *,
        occurred_at: datetime,
        method: str,
        actor_role: str,
        actor_id: str,
        evidence_id: str | None = None,
    ) -> Beneficiary:
        """Record that a person independently verified these bank details."""
        current = self.get(beneficiary_id)
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="beneficiary.verify",
            object_type="beneficiary",
            object_id=beneficiary_id,
            summary=f"{actor_id} verified bank details by {method}",
            payload={"method": method, "evidence_id": evidence_id},
        )
        updated = replace(current, verified_at=occurred_at, verification_method=method)
        self._beneficiaries[beneficiary_id] = updated
        return updated
