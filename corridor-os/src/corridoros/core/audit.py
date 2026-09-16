"""The audit log, and the hash chain over it.

The chain is ported from `crossborder-riskops/src/riskops/audit/chain.py`,
including its three-state verification, because that design was already right
and the reasoning behind it has not changed:

    Each entry's hash covers the previous entry's hash as well as its own
    contents, so editing entry *N* invalidates *N* and every entry after it.
    A standalone digest cannot do this: whoever edits the record recomputes the
    digest. The chain forces an edit to rewrite the whole tail.

    What this proves and does not prove, stated plainly because an auditor will
    ask: it makes a *partial* edit detectable. Someone who can rewrite the
    entire table can still recompute every link. Real non-repudiation needs the
    head anchored somewhere the editor does not control. This project does not
    do that, and says so rather than implying a guarantee it has not earned.

What CorridorOS adds is coverage. In RiskOps the chain covered AML decisions.
Here one chain covers every consequential act in the platform: a KYB approval,
a ledger posting, an FX execution, a payment release, a reconciliation
adjustment, an exception resolution. "Show me everything that happened to this
payment, in order, and prove the record was not edited" is one query against
one log.

`record_decision` is where the AI boundary is enforced for a second time, after
`ApprovalDecision` itself. Belt and braces is the correct engineering here: the
cost of the redundancy is six lines, and the cost of being wrong is the single
claim this platform makes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .authority import AI_COPILOT, require
from .domain import ApprovalDecision, AuditEvent
from .errors import AuthorityError
from .ids import IdFactory

GENESIS = "0" * 64


def canonical(entry: dict[str, Any]) -> str:
    """Canonical serialisation. Field order is fixed here, not left to a dict.

    `json.dumps` on a dict would encode whatever insertion order the caller
    happened to use, so two identical records could hash differently.
    """
    return json.dumps(
        [
            str(entry.get("entry_id", "")),
            str(entry.get("occurred_at", "")),
            str(entry.get("actor_role", "")),
            str(entry.get("actor_id", "")),
            str(entry.get("action", "")),
            str(entry.get("object_type", "")),
            str(entry.get("object_id", "")),
            str(entry.get("summary", "")),
            str(entry.get("payload_json", "")),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def link_hash(previous_hash: str, entry: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update((previous_hash or GENESIS).encode("utf-8"))
    digest.update(canonical(entry).encode("utf-8"))
    return digest.hexdigest()


@dataclass(frozen=True)
class ChainVerification:
    """`verified` every link recomputes; `broken` one does not; `unverifiable`
    the log carries no hashes at all because it predates chaining."""

    status: str
    valid: bool
    head: str
    entries_checked: int
    broken_at: int | None = None
    broken_entry_id: str | None = None

    def summary(self) -> str:
        if self.status == "verified":
            return (
                f"{self.entries_checked} entries verified; head {self.head[:12]}... "
                "A partial edit would break this chain."
            )
        if self.status == "unverifiable":
            return "the log carries no hashes; it cannot be verified either way"
        return (
            f"chain broken at entry {self.broken_at} ({self.broken_entry_id}); "
            "every entry from there on is unverifiable"
        )


def verify_entries(entries: list[dict[str, Any]]) -> ChainVerification:
    """Recompute every link in order."""
    if not entries:
        return ChainVerification("verified", True, GENESIS, 0)
    if all(not entry.get("entry_hash") for entry in entries):
        return ChainVerification("unverifiable", False, GENESIS, len(entries))

    previous = GENESIS
    for index, entry in enumerate(entries):
        stored = str(entry.get("entry_hash") or "")
        if not stored:
            return ChainVerification("broken", False, previous, len(entries), index, str(entry.get("entry_id")))
        expected = link_hash(previous, entry)
        if expected != stored:
            return ChainVerification("broken", False, previous, len(entries), index, str(entry.get("entry_id")))
        previous = stored
    return ChainVerification("verified", True, previous, len(entries))


class AuditLog:
    """Every consequential act in CorridorOS, hash-chained, in one place."""

    def __init__(self, ids: IdFactory | None = None) -> None:
        self._entries: list[AuditEvent] = []
        self._decisions: list[ApprovalDecision] = []
        self._ids = ids or IdFactory("aud")
        self.refusals: list[dict[str, Any]] = []

    # -- writing -----------------------------------------------------------

    def record(
        self,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        action: str,
        object_type: str,
        object_id: str,
        summary: str,
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Append one entry, after checking the actor was allowed to do it.

        A refused write is itself recorded — in `refusals`, not in the chain,
        because the chain records what happened and a refusal is precisely what
        did not happen. The operations view reads both.
        """
        try:
            require(actor_role, action, context=f"{object_type} {object_id}")
        except AuthorityError as error:
            self.refusals.append(
                {
                    "occurred_at": occurred_at.isoformat(),
                    "actor_role": actor_role,
                    "actor_id": actor_id,
                    "action": action,
                    "object_id": object_id,
                    "error": str(error),
                }
            )
            raise

        entry = {
            "entry_id": self._ids.next("audit"),
            "occurred_at": occurred_at.isoformat(),
            "actor_role": actor_role,
            "actor_id": actor_id,
            "action": action,
            "object_type": object_type,
            "object_id": object_id,
            "summary": summary,
            "payload_json": json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
        }
        previous = self._entries[-1].entry_hash if self._entries else GENESIS
        event = AuditEvent(
            entry_id=entry["entry_id"],
            seq=len(self._entries) + 1,
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            summary=summary,
            payload_json=entry["payload_json"],
            previous_hash=previous,
            entry_hash=link_hash(previous, entry),
        )
        self._entries.append(event)
        return event

    def record_decision(
        self,
        *,
        decision_id: str,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        action: str,
        object_type: str,
        object_id: str,
        reason_code: str,
        note: str = "",
        ai_brief_id: str | None = None,
        agreed_with_ai: bool | None = None,
    ) -> ApprovalDecision:
        """Commit a human decision and chain it.

        The copilot is rejected here explicitly rather than falling through to
        the permission matrix, so the error message says what is actually going
        on instead of reading like a misconfiguration.
        """
        if actor_role == AI_COPILOT:
            self.refusals.append(
                {
                    "occurred_at": occurred_at.isoformat(),
                    "actor_role": actor_role,
                    "actor_id": actor_id,
                    "action": action,
                    "object_id": object_id,
                    "error": "the AI copilot may not commit a decision",
                }
            )
            raise AuthorityError(
                f"the AI copilot may not commit {action!r} on {object_id}. "
                "It can assemble the evidence and say what is missing; the decision is a person's."
            )
        decision = ApprovalDecision(
            decision_id=decision_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            actor_role=actor_role,
            actor_id=actor_id,
            reason_code=reason_code,
            occurred_at=occurred_at,
            note=note,
            ai_brief_id=ai_brief_id,
            agreed_with_ai=agreed_with_ai,
        )
        self.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            summary=f"{actor_id} committed {action} ({reason_code})",
            payload={"decision_id": decision_id, "reason_code": reason_code, "note": note},
        )
        self._decisions.append(decision)
        return decision

    # -- reading -----------------------------------------------------------

    @property
    def entries(self) -> tuple[AuditEvent, ...]:
        return tuple(self._entries)

    @property
    def decisions(self) -> tuple[ApprovalDecision, ...]:
        return tuple(self._decisions)

    def decisions_for(self, object_id: str) -> tuple[ApprovalDecision, ...]:
        return tuple(item for item in self._decisions if item.object_id == object_id)

    def for_object(self, object_id: str) -> tuple[AuditEvent, ...]:
        return tuple(item for item in self._entries if item.object_id == object_id)

    def as_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "entry_id": item.entry_id,
                "seq": item.seq,
                "occurred_at": item.occurred_at.isoformat(),
                "actor_role": item.actor_role,
                "actor_id": item.actor_id,
                "action": item.action,
                "object_type": item.object_type,
                "object_id": item.object_id,
                "summary": item.summary,
                "payload_json": item.payload_json,
                "previous_hash": item.previous_hash,
                "entry_hash": item.entry_hash,
            }
            for item in self._entries
        ]

    def verify(self) -> ChainVerification:
        return verify_entries(self.as_rows())
