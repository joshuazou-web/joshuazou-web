"""One JSON document containing everything the console shows.

The console has two ways to run. Against the API it reads live objects from a
running `CorridorOS`. On a static host it reads this snapshot, which is the same
data serialised after the demonstration has run. Both paths render the same
screens from the same shapes, so the published demo is not a separate,
hand-maintained mock that drifts away from the code.

Nothing is computed here that the platform does not already hold. This module
is a projection, which is why it is safe for it to be the thing a reader sees.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..platform import CorridorOS
from ..risk.evaluate import DEFAULT_CAPACITY
from ..risk.evaluate import evaluate as evaluate_aml
from ..risk.rules import RULES
from ..risk.typologies import TYPOLOGIES
from .feed import run_monitoring
from .world import RECONCILIATION_DATE, World, build_demo


def _money(value) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"minor_units": value.minor_units, "currency": value.currency, "display": value.format()}


def build_snapshot(
    world: World,
    *,
    now: datetime = RECONCILIATION_DATE,
    include_evaluation: bool = True,
) -> dict[str, Any]:
    system: CorridorOS = world.system
    verification = system.audit.verify()
    queue, backlog = system.cases.queue(capacity=3)

    businesses = [
        {
            "business_id": business.business_id,
            "legal_name": business.legal_name,
            "uen": business.uen,
            "entity_country": business.entity_country,
            "review_status": business.review_status,
            "submitted_at": business.submitted_at.isoformat(),
            "decided_at": business.decided_at.isoformat() if business.decided_at else None,
            "decided_by": business.decided_by,
            "expected_monthly_volume": _money(business.expected_monthly_volume),
            "missing_evidence": list(system.businesses.missing_evidence(business.business_id)),
            "evidence_ids": [
                item.evidence_id for item in system.evidence.for_business(business.business_id)
            ],
            "balances": {
                bucket: _money(amount)
                for bucket, amount in system.ledger.balances(business.business_id, "SGD").items()
            },
        }
        for business in system.businesses.all
    ]

    payments = [system.payment_view(payment.payment_id, now=now) for payment in system.payouts.all]

    # The AML layer runs over the corridor's whole monitored feed — the
    # platform's own settled movements included — not over a separate world.
    aml_queue, aml_context, population = run_monitoring(
        system, capacity=DEFAULT_CAPACITY, now=now
    )
    aml_evaluation = evaluate_aml() if include_evaluation else None

    return {
        "generated_at": now.isoformat(),
        "disclaimer": (
            "Every business, supplier, payment, document, amount and result in this snapshot is "
            "synthetic and was produced by a seeded generator. Nothing here has run in production, "
            "and no licence, bank partner, customer or real transaction is involved."
        ),
        "overview": {
            "businesses": len(businesses),
            "payments": len(payments),
            "settled_payments": sum(1 for item in system.payouts.all if item.state == "settled"),
            "open_cases": len(system.cases.open_cases()),
            "open_exceptions": len(system.reconciliation.open_exceptions()),
            "events": len(system.bus),
            "audit_entries": len(system.audit.entries),
            "audit_status": verification.status,
            "audit_head": verification.head,
            "audit_summary": verification.summary(),
            "ledger_balanced": system.ledger.is_balanced(),
            "ai_refusals": len(system.audit.refusals),
            "quarantined_events": len(system.bus.quarantine),
            "duplicate_attempts": len(system.payouts.duplicate_attempts),
            "flagship_payment_id": world.flagship_payment_id,
        },
        "demo_transcript": list(world.transcript),
        "businesses": businesses,
        "beneficiaries": [
            {
                "beneficiary_id": beneficiary.beneficiary_id,
                "business_id": beneficiary.business_id,
                "display_name": beneficiary.display_name,
                "bank_country": beneficiary.bank_country,
                "account_last4": beneficiary.account_last4,
                "previous_account_last4": beneficiary.previous_account_last4,
                "last_changed_at": beneficiary.last_changed_at.isoformat()
                if beneficiary.last_changed_at
                else None,
                "verified_at": beneficiary.verified_at.isoformat() if beneficiary.verified_at else None,
                "verification_is_current": beneficiary.verification_is_current(now),
                "change_count": beneficiary.change_count,
            }
            for beneficiary in system.beneficiaries.all
        ],
        "payments": payments,
        "cases": {
            "within_capacity": [
                {
                    "case_id": case.case_id,
                    "kind": case.kind,
                    "title": case.title,
                    "priority": case.priority,
                    "state": case.state,
                    "sla_due_at": case.sla_due_at.isoformat(),
                    "payment_id": case.payment_id,
                    "signal_ids": list(case.signal_ids),
                    "closure_reason": case.closure_reason,
                }
                for case in queue
            ],
            "backlog": [
                {
                    "case_id": case.case_id,
                    "title": case.title,
                    "priority": case.priority,
                    "state": case.state,
                }
                for case in backlog
            ],
            "capacity": 3,
        },
        "evidence": [
            {
                "evidence_id": item.evidence_id,
                "kind": item.kind,
                "title": item.title,
                "issuer": item.issuer,
                "issued_at": item.issued_at.isoformat() if item.issued_at else None,
                "location": item.location,
                "excerpt": item.excerpt,
                "checksum": item.checksum,
                "business_id": item.business_id,
                "payment_id": item.payment_id,
                "beneficiary_id": item.beneficiary_id,
                "status": item.status,
            }
            for item in system.evidence.all
        ],
        "ledger": {
            "balanced": system.ledger.is_balanced(),
            "journals": [
                {
                    "journal_id": journal.journal_id,
                    "posted_at": journal.posted_at.isoformat(),
                    "description": journal.description,
                    "payment_id": journal.payment_id,
                    "reverses_journal_id": journal.reverses_journal_id,
                    "legs": [
                        {"account": entry.account, "amount": _money(entry.amount), "memo": entry.memo}
                        for entry in journal.entries
                    ],
                }
                for journal in system.ledger.journals
            ],
        },
        "reconciliation": {
            "settlements": [
                {
                    "settlement_id": settlement.settlement_id,
                    "payment_id": settlement.payment_id,
                    "gross": _money(settlement.gross),
                    "fee": _money(settlement.fee),
                    "net": _money(settlement.net),
                    "value_date": settlement.value_date.isoformat(),
                    "provider_reference": settlement.provider_reference,
                }
                for settlement in system.settlements.all
            ],
            "exceptions": [
                {
                    "exception_id": exception.exception_id,
                    "exception_type": exception.exception_type,
                    "summary": exception.summary,
                    "owner": exception.owner,
                    "state": exception.state,
                    "opened_at": exception.opened_at.isoformat(),
                    "due_at": exception.due_at.isoformat(),
                    "payment_id": exception.payment_id,
                    "difference": _money(exception.difference),
                    "resolution_code": exception.resolution_code,
                }
                for exception in system.reconciliation.exceptions
            ],
        },
        "aml": {
            "run": aml_queue.as_row(),
            "monitored_transfers": len(aml_context.transfers),
            "monitored_accounts": len(aml_context.monitored_accounts()),
            "platform_movements_in_feed": sum(
                1 for transfer in aml_context.transfers if transfer.payment_id
            ),
            "queue": [case.as_row() for case in aml_queue.within_capacity],
            "backlog": [
                {
                    "case_key": case.case_key,
                    "subject_name": case.subject_name,
                    "subject_account": case.subject_account,
                    "priority_score": round(case.priority_score, 4),
                    "priority_band": case.priority_band,
                    "queue_position": case.queue_position,
                    "typology_keys": list(case.typology_keys),
                    "alert_count": len(case.alerts),
                }
                for case in aml_queue.backlog
            ],
            "backlog_note": (
                "Cases below the capacity line were not cleared. They were not looked at. The "
                "count of planted patterns sitting in this backlog is a headline row of the "
                "evaluation rather than an omission."
            ),
            "typologies": [
                {
                    "typology_id": typology.typology_id,
                    "key": typology.key,
                    "title": typology.title,
                    "severity": typology.severity,
                    "question": typology.question,
                    "thresholds": typology.thresholds,
                    "counter_evidence": list(typology.counter_evidence_hints),
                }
                for typology in TYPOLOGIES
            ],
            "rules": [
                {
                    "rule_id": spec.rule_id,
                    "family": spec.family,
                    "severity": spec.severity,
                    "title": spec.title,
                    "reason": spec.reason,
                    "reads": list(spec.reads),
                    "signal_id": spec.signal_key(),
                }
                for spec in RULES.values()
            ],
            "evaluation": aml_evaluation,
            "planted_patterns": len(population.planted),
        },
        "events": [event.as_row() for event in system.bus.events],
        "quarantined_events": [item.as_row() for item in system.bus.quarantine],
        "audit": system.audit.as_rows(),
        "ai_boundary": {
            "allowed": sorted(_ai_allowed()),
            "refused_examples": system.audit.refusals,
            "note": (
                "The copilot's permitted actions are the whole of its permission set in "
                "corridoros/core/authority.py. Its output object has no field in which a decision "
                "could be placed, and the audit log rejects it as the author of one."
            ),
        },
    }


def _ai_allowed() -> frozenset[str]:
    from ..core.authority import AI_ALLOWED

    return AI_ALLOWED


def write_snapshot(path: Path, world: World | None = None) -> Path:
    world = world or build_demo()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_snapshot(world), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path
