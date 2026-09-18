"""Business onboarding and KYB review.

The corridor blueprint made one point about onboarding that most product specs
miss, and it is the only reason this module is not a boolean: **evidence
expires and entities change**, so approval is a state with a version, not a
checkbox that stays ticked.

Two rules carry that:

  * `approve` refuses while any required evidence kind is absent. The
    compliance officer is not offered a button that produces an approval
    resting on nothing, so "approved with documents to follow" cannot happen by
    accident;
  * approval is bound to `evidence_version`. A later change to the entity's
    evidence increments it, which is what a change-triggered re-review would
    hang off.

`may_move_money` on the profile is the single gate the rest of the platform
checks. Collection and payout ask that one question rather than each carrying
their own idea of what "onboarded" means.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from ..core.audit import AuditLog
from ..core.domain import BusinessProfile
from ..core.errors import LifecycleError
from ..core.events import EventBus

# What a Singapore operating entity must have on file before it may move money.
REQUIRED_EVIDENCE_KINDS: tuple[str, ...] = (
    "incorporation_document",
    "ownership_declaration",
)

TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft": ("submitted",),
    "submitted": ("needs_information", "approved", "rejected"),
    "needs_information": ("submitted", "rejected"),
    "approved": ("needs_information",),
    "rejected": (),
}


class KybRegistry:
    def __init__(
        self,
        bus: EventBus,
        audit: AuditLog,
        evidence_kinds_for: Callable[[str], set[str]],
    ) -> None:
        self._bus = bus
        self._audit = audit
        self._evidence_kinds_for = evidence_kinds_for
        self._businesses: dict[str, BusinessProfile] = {}

    # -- reading -----------------------------------------------------------

    def get(self, business_id: str) -> BusinessProfile:
        try:
            return self._businesses[business_id]
        except KeyError:
            raise LifecycleError(f"unknown business {business_id}") from None

    @property
    def all(self) -> tuple[BusinessProfile, ...]:
        return tuple(self._businesses.values())

    def missing_evidence(self, business_id: str) -> tuple[str, ...]:
        held = self._evidence_kinds_for(business_id)
        return tuple(kind for kind in REQUIRED_EVIDENCE_KINDS if kind not in held)

    # -- transitions -------------------------------------------------------

    def _move(self, profile: BusinessProfile, to_state: str) -> None:
        allowed = TRANSITIONS[profile.review_status]
        if to_state not in allowed:
            raise LifecycleError(
                f"business {profile.business_id} cannot go {profile.review_status} -> {to_state}; "
                f"allowed: {allowed or '(terminal)'}"
            )

    def submit(
        self,
        profile: BusinessProfile,
        *,
        occurred_at: datetime,
        actor_role: str = "treasury_operator",
        actor_id: str = "merchant.finance",
    ) -> BusinessProfile:
        stored = self._businesses.get(profile.business_id)
        if stored is not None:
            self._move(stored, "submitted")
            profile = replace(stored, review_status="submitted", submitted_at=occurred_at)
        else:
            profile = replace(profile, review_status="submitted", submitted_at=occurred_at)
        self._businesses[profile.business_id] = profile
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="business.submit",
            object_type="business",
            object_id=profile.business_id,
            summary=f"{profile.legal_name} submitted for KYB review",
            payload={"uen": profile.uen, "entity_country": profile.entity_country},
        )
        self._bus.publish(
            "business.submitted",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject={"business": profile.business_id},
            payload={"legal_name": profile.legal_name, "uen": profile.uen},
            idempotency_key=f"business.submitted:{profile.business_id}:{profile.evidence_version}",
        )
        return profile

    def request_information(
        self,
        business_id: str,
        kinds: tuple[str, ...],
        *,
        occurred_at: datetime,
        actor_role: str = "compliance_officer",
        actor_id: str = "compliance.ops",
    ) -> BusinessProfile:
        profile = self.get(business_id)
        self._move(profile, "needs_information")
        updated = replace(profile, review_status="needs_information", outstanding_requests=kinds)
        self._businesses[business_id] = updated
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="business.request_information",
            object_type="business",
            object_id=business_id,
            summary=f"requested {', '.join(kinds)}",
            payload={"kinds": list(kinds)},
        )
        return updated

    def approve(
        self,
        business_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        decision_id: str,
        reason_code: str = "kyb_evidence_complete",
        note: str = "",
    ) -> BusinessProfile:
        profile = self.get(business_id)
        self._move(profile, "approved")
        missing = self.missing_evidence(business_id)
        if missing:
            raise LifecycleError(
                f"cannot approve {business_id}: required evidence missing ({', '.join(missing)}). "
                "An approval must rest on documents that exist."
            )
        self._audit.record_decision(
            decision_id=decision_id,
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="business.approve",
            object_type="business",
            object_id=business_id,
            reason_code=reason_code,
            note=note,
        )
        updated = replace(
            profile,
            review_status="approved",
            decided_at=occurred_at,
            decided_by=actor_id,
            outstanding_requests=(),
        )
        self._businesses[business_id] = updated
        self._bus.publish(
            "business.approved",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject={"business": business_id},
            payload={"decision_id": decision_id, "evidence_version": updated.evidence_version},
            idempotency_key=f"business.approved:{business_id}:{updated.evidence_version}",
        )
        return updated

    def reject(
        self,
        business_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        decision_id: str,
        reason_code: str,
        note: str = "",
    ) -> BusinessProfile:
        profile = self.get(business_id)
        self._move(profile, "rejected")
        self._audit.record_decision(
            decision_id=decision_id,
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="business.reject",
            object_type="business",
            object_id=business_id,
            reason_code=reason_code,
            note=note,
        )
        updated = replace(profile, review_status="rejected", decided_at=occurred_at, decided_by=actor_id)
        self._businesses[business_id] = updated
        return updated
