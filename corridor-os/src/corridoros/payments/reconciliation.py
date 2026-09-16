"""Three-way reconciliation.

The product ledger, the provider's settlement advice and the bank statement are
three *independent* accounts of the same money. Comparing two of them tells you
that something is wrong; comparing three usually tells you which one is wrong,
which is the difference between an exception an operator can act on and an
exception they can only escalate.

Two rules make this honest:

**Differences are typed, not summed.** A fee difference, a timing difference
and a duplicate credit are different problems with different owners, so each
becomes an `ExceptionCase` with a type, an owner, a due time and a reason code.
A single "unreconciled: 3" number hides exactly the information the operator
needs.

**A run with an unexplained difference cannot be marked reconciled.** This is
enforced in `mark_reconciled`, which raises. The corridor blueprint listed
"unexplained ledger difference: must be 0" as a guardrail metric; a guardrail
that a person can click past is a label, so it is a refusal instead.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from ..core.audit import AuditLog
from ..core.domain import ExceptionCase, SettlementRecord
from ..core.errors import CorridorError
from ..core.events import EventBus
from ..core.ids import IdFactory
from ..core.money import Money
from .ledger import Ledger

# How long an exception of each type may sit before it is overdue.
SLA_HOURS: dict[str, int] = {
    "timing": 48,
    "fee": 24,
    "fx": 24,
    "duplicate": 4,
    "missing_record": 8,
    "amount": 8,
    "beneficiary": 4,
    "state": 8,
}

OWNER_BY_TYPE: dict[str, str] = {
    "timing": "payment_operations",
    "fee": "finance",
    "fx": "treasury",
    "duplicate": "payment_operations",
    "missing_record": "payment_operations",
    "amount": "finance",
    "beneficiary": "compliance",
    "state": "payment_operations",
}


@dataclass(frozen=True)
class BankStatementLine:
    """One line of the bank's own statement — the third, independent view."""

    bank_reference: str
    amount: Money
    value_date: datetime
    narrative: str = ""


@dataclass(frozen=True)
class ReconciliationResult:
    run_at: datetime
    matched_payment_ids: tuple[str, ...]
    exceptions: tuple[ExceptionCase, ...]
    unexplained: Money
    checked: int = 0
    reconciled: bool = False

    @property
    def is_clean(self) -> bool:
        return not self.exceptions and self.unexplained.is_zero()


class ReconciliationEngine:
    def __init__(
        self,
        bus: EventBus,
        audit: AuditLog,
        ledger: Ledger,
        ids: IdFactory | None = None,
    ) -> None:
        self._bus = bus
        self._audit = audit
        self._ledger = ledger
        self._ids = ids or IdFactory("exc")
        self._exceptions: dict[str, ExceptionCase] = {}
        self._runs: list[ReconciliationResult] = []

    @property
    def exceptions(self) -> tuple[ExceptionCase, ...]:
        return tuple(self._exceptions.values())

    def open_exceptions(self) -> tuple[ExceptionCase, ...]:
        return tuple(item for item in self._exceptions.values() if item.state == "open")

    def _open_exception(
        self,
        *,
        exception_type: str,
        summary: str,
        opened_at: datetime,
        payment_id: str | None,
        settlement_id: str | None,
        difference: Money | None,
        currency: str,
    ) -> ExceptionCase:
        exception = ExceptionCase(
            exception_id=self._ids.next("exception"),
            exception_type=exception_type,
            summary=summary,
            opened_at=opened_at,
            due_at=opened_at + timedelta(hours=SLA_HOURS[exception_type]),
            owner=OWNER_BY_TYPE[exception_type],
            payment_id=payment_id,
            settlement_id=settlement_id,
            difference=difference if difference is not None else Money.zero(currency),
        )
        self._exceptions[exception.exception_id] = exception
        self._audit.record(
            occurred_at=opened_at,
            actor_role="system",
            actor_id="reconciliation.engine",
            action="exception.open",
            object_type="exception",
            object_id=exception.exception_id,
            summary=summary,
            payload={"type": exception_type, "payment_id": payment_id},
        )
        return exception

    def run(
        self,
        *,
        run_at: datetime,
        settlements: tuple[SettlementRecord, ...],
        bank_lines: tuple[BankStatementLine, ...],
        currency: str = "SGD",
        actor_role: str = "finance_operator",
        actor_id: str = "finance.ops",
    ) -> ReconciliationResult:
        """Compare the three views and type every difference."""
        self._audit.record(
            occurred_at=run_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="reconciliation.run",
            object_type="reconciliation",
            object_id=f"run-{run_at.date().isoformat()}",
            summary=f"three-way reconciliation over {len(settlements)} settlement(s)",
            payload={"settlements": len(settlements), "bank_lines": len(bank_lines)},
        )

        by_reference: dict[str, list[BankStatementLine]] = {}
        for line in bank_lines:
            by_reference.setdefault(line.bank_reference, []).append(line)

        matched: list[str] = []
        exceptions: list[ExceptionCase] = []
        unexplained = Money.zero(currency)

        for settlement in settlements:
            ledger_out = self._ledger_outflow(settlement.payment_id, currency)
            lines = by_reference.get(settlement.provider_reference, [])

            if not lines:
                exceptions.append(
                    self._open_exception(
                        exception_type="missing_record",
                        summary=(
                            f"provider reports {settlement.net.format()} settled for "
                            f"{settlement.payment_id}, the bank statement has no matching line"
                        ),
                        opened_at=run_at,
                        payment_id=settlement.payment_id,
                        settlement_id=settlement.settlement_id,
                        difference=settlement.net,
                        currency=currency,
                    )
                )
                unexplained = unexplained + settlement.net
                continue

            if len(lines) > 1:
                extra = Money(
                    sum(line.amount.minor_units for line in lines[1:]), currency
                )
                exceptions.append(
                    self._open_exception(
                        exception_type="duplicate",
                        summary=(
                            f"{len(lines)} bank lines carry reference {settlement.provider_reference}; "
                            "one payment cannot have settled twice"
                        ),
                        opened_at=run_at,
                        payment_id=settlement.payment_id,
                        settlement_id=settlement.settlement_id,
                        difference=extra,
                        currency=currency,
                    )
                )
                unexplained = unexplained + extra

            line = lines[0]
            bank_difference = line.amount - settlement.net
            if not bank_difference.is_zero():
                # A difference that equals the fee is a fee-booking problem, not
                # a missing payment; naming it correctly puts it on the right desk.
                kind = "fee" if abs(bank_difference) == abs(settlement.fee) else "amount"
                exceptions.append(
                    self._open_exception(
                        exception_type=kind,
                        summary=(
                            f"bank line {line.bank_reference} is {line.amount.format()}, "
                            f"provider net is {settlement.net.format()}"
                        ),
                        opened_at=run_at,
                        payment_id=settlement.payment_id,
                        settlement_id=settlement.settlement_id,
                        difference=bank_difference,
                        currency=currency,
                    )
                )
                unexplained = unexplained + bank_difference
                self._bus.publish(
                    "reconciliation.failed",
                    occurred_at=run_at,
                    actor_role="system",
                    actor_id="reconciliation.engine",
                    subject={"payment": settlement.payment_id},
                    payload={
                        "difference_minor": bank_difference.minor_units,
                        "currency": currency,
                        "exception_type": kind,
                    },
                    idempotency_key=f"reconciliation.failed:{settlement.settlement_id}",
                )
                continue

            ledger_difference = ledger_out - settlement.gross
            if not ledger_difference.is_zero():
                exceptions.append(
                    self._open_exception(
                        exception_type="amount",
                        summary=(
                            f"ledger moved {ledger_out.format()} for {settlement.payment_id}, "
                            f"provider gross is {settlement.gross.format()}"
                        ),
                        opened_at=run_at,
                        payment_id=settlement.payment_id,
                        settlement_id=settlement.settlement_id,
                        difference=ledger_difference,
                        currency=currency,
                    )
                )
                unexplained = unexplained + ledger_difference
                self._bus.publish(
                    "reconciliation.failed",
                    occurred_at=run_at,
                    actor_role="system",
                    actor_id="reconciliation.engine",
                    subject={"payment": settlement.payment_id},
                    payload={
                        "difference_minor": ledger_difference.minor_units,
                        "currency": currency,
                        "exception_type": "amount",
                    },
                    idempotency_key=f"reconciliation.failed:ledger:{settlement.settlement_id}",
                )
                continue

            if line.value_date.date() != settlement.value_date.date():
                exceptions.append(
                    self._open_exception(
                        exception_type="timing",
                        summary=(
                            f"value dates differ: provider {settlement.value_date.date()}, "
                            f"bank {line.value_date.date()}; the amount agrees"
                        ),
                        opened_at=run_at,
                        payment_id=settlement.payment_id,
                        settlement_id=settlement.settlement_id,
                        difference=Money.zero(currency),
                        currency=currency,
                    )
                )
                matched.append(settlement.payment_id)
                continue

            matched.append(settlement.payment_id)

        result = ReconciliationResult(
            run_at=run_at,
            matched_payment_ids=tuple(matched),
            exceptions=tuple(exceptions),
            unexplained=unexplained,
            checked=len(settlements),
        )
        self._runs.append(result)
        return result

    def _ledger_outflow(self, payment_id: str, currency: str) -> Money:
        """What the product's own books say left the business for this payment."""
        total = Money.zero(currency)
        for entry in self._ledger.entries_for_payment(payment_id):
            if entry.account.endswith(":payable") and entry.amount.minor_units < 0:
                total = total + abs(entry.amount)
        return total

    def mark_reconciled(self, result: ReconciliationResult) -> ReconciliationResult:
        """Close a run. Refuses while any difference is unexplained."""
        if not result.unexplained.is_zero():
            raise CorridorError(
                f"cannot mark this run reconciled: {result.unexplained.format()} is unexplained "
                f"across {len(result.exceptions)} exception(s). Resolve them first."
            )
        return replace(result, reconciled=True)

    def resolve(
        self,
        exception_id: str,
        *,
        occurred_at: datetime,
        actor_role: str,
        actor_id: str,
        resolution_code: str,
        note: str = "",
    ) -> ExceptionCase:
        exception = self._exceptions[exception_id]
        self._audit.record(
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="exception.resolve",
            object_type="exception",
            object_id=exception_id,
            summary=f"{actor_id} resolved {exception.exception_type} exception: {resolution_code}",
            payload={"resolution_code": resolution_code, "note": note},
        )
        resolved = replace(
            exception,
            state="closed",
            resolution_code=resolution_code,
            resolved_at=occurred_at,
            resolved_by=actor_id,
        )
        self._exceptions[exception_id] = resolved
        self._bus.publish(
            "exception.resolved",
            occurred_at=occurred_at,
            actor_role=actor_role,
            actor_id=actor_id,
            subject=({"payment": exception.payment_id} if exception.payment_id else {}),
            payload={
                "exception_id": exception_id,
                "exception_type": exception.exception_type,
                "resolution_code": resolution_code,
            },
            idempotency_key=f"exception.resolved:{exception_id}",
        )
        return resolved
