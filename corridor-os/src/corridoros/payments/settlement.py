"""Settlement records.

A settlement is the provider's account of what left the platform: a gross
amount, a fee, a net, and a value date. It is deliberately a separate object
from the payment instruction, because the instruction is what the business
asked for and the settlement is what the provider says happened. Collapsing
them into one row is what makes a reconciliation difference impossible to
describe — there would be nothing left to compare against.

`SettlementRecord` enforces `net == gross - fee` in its constructor, so an
arithmetic error in a provider feed surfaces at ingestion with the record in
hand, rather than as an unexplained variance a week later.
"""

from __future__ import annotations

from datetime import datetime

from ..core.domain import SettlementRecord
from ..core.ids import IdFactory
from ..core.money import Money


class SettlementBook:
    def __init__(self, ids: IdFactory | None = None) -> None:
        self._ids = ids or IdFactory("stl")
        self._records: dict[str, SettlementRecord] = {}

    def record(
        self,
        *,
        payment_id: str,
        gross: Money,
        fee: Money,
        value_date: datetime,
        provider_reference: str,
        bank_reference: str | None = None,
    ) -> SettlementRecord:
        settlement = SettlementRecord(
            settlement_id=self._ids.next("settlement"),
            payment_id=payment_id,
            gross=gross,
            fee=fee,
            net=gross - fee,
            value_date=value_date,
            provider_reference=provider_reference,
            bank_reference=bank_reference,
        )
        self._records[settlement.settlement_id] = settlement
        return settlement

    def for_payment(self, payment_id: str) -> SettlementRecord | None:
        for record in self._records.values():
            if record.payment_id == payment_id:
                return record
        return None

    @property
    def all(self) -> tuple[SettlementRecord, ...]:
        return tuple(self._records.values())
