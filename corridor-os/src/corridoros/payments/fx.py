"""FX quoting and conversion.

One behaviour justifies this module existing separately from the ledger: an
expired quote **fails closed**. It does not silently refresh, it does not
execute at "today's rate", and it does not round the difference into a fee. The
treasury operator is sent back to request a new quote, because a rate the
customer never saw is not a rate the customer agreed to.

The rate is carried as a decimal string end to end, never a float, and the
conversion returns its rounding remainder (see `core.money.convert`). That
remainder is what makes an FX reconciliation break explainable later: the cent
that rounding created is recorded rather than absorbed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from ..core.audit import AuditLog
from ..core.errors import FxError
from ..core.ids import IdFactory
from ..core.money import Conversion, Money, convert

DEFAULT_QUOTE_TTL = timedelta(minutes=15)


@dataclass(frozen=True)
class FxQuote:
    quote_id: str
    sell_currency: str
    buy_currency: str
    rate: str
    fee: Money
    quoted_at: datetime
    expires_at: datetime
    business_id: str

    def is_expired(self, now: datetime) -> bool:
        return now > self.expires_at

    def seconds_remaining(self, now: datetime) -> int:
        return max(0, int((self.expires_at - now).total_seconds()))


@dataclass(frozen=True)
class FxExecution:
    quote_id: str
    conversion: Conversion
    executed_at: datetime
    fee: Money


class FxDesk:
    def __init__(self, audit: AuditLog, ids: IdFactory | None = None) -> None:
        self._audit = audit
        self._ids = ids or IdFactory("fxq")
        self._quotes: dict[str, FxQuote] = {}
        self._executions: dict[str, FxExecution] = {}

    def quote(
        self,
        *,
        business_id: str,
        sell_currency: str,
        buy_currency: str,
        rate: str,
        fee: Money,
        quoted_at: datetime,
        ttl: timedelta = DEFAULT_QUOTE_TTL,
        actor_role: str = "treasury_operator",
        actor_id: str = "treasury.ops",
    ) -> FxQuote:
        if isinstance(rate, float):
            raise FxError("refusing to quote a float rate; pass the exact decimal string")
        if Decimal(str(rate)) <= 0:
            raise FxError(f"fx rate must be positive, got {rate}")
        quote = FxQuote(
            quote_id=self._ids.next("quote"),
            sell_currency=sell_currency.upper(),
            buy_currency=buy_currency.upper(),
            rate=str(rate),
            fee=fee,
            quoted_at=quoted_at,
            expires_at=quoted_at + ttl,
            business_id=business_id,
        )
        self._quotes[quote.quote_id] = quote
        self._audit.record(
            occurred_at=quoted_at,
            actor_role=actor_role,
            actor_id=actor_id,
            action="fx.quote",
            object_type="quote",
            object_id=quote.quote_id,
            summary=f"quoted {quote.sell_currency}->{quote.buy_currency} at {quote.rate}",
            payload={"rate": quote.rate, "expires_at": quote.expires_at.isoformat()},
        )
        return quote

    def get(self, quote_id: str) -> FxQuote:
        try:
            return self._quotes[quote_id]
        except KeyError:
            raise FxError(f"unknown quote {quote_id}") from None

    def execute(
        self,
        quote_id: str,
        amount: Money,
        *,
        now: datetime,
        actor_role: str,
        actor_id: str,
    ) -> FxExecution:
        """Convert at the quoted rate, or refuse. There is no third outcome."""
        quote = self.get(quote_id)
        if quote_id in self._executions:
            raise FxError(f"quote {quote_id} has already been executed")
        if amount.currency != quote.sell_currency:
            raise FxError(
                f"quote {quote_id} sells {quote.sell_currency}, not {amount.currency}"
            )
        if quote.is_expired(now):
            # Fail closed. Nothing is posted, nothing is refreshed.
            self._audit.record(
                occurred_at=now,
                actor_role=actor_role,
                actor_id=actor_id,
                action="fx.quote",
                object_type="quote",
                object_id=quote_id,
                summary="execution refused: quote had expired",
                payload={"expired_at": quote.expires_at.isoformat()},
            )
            raise FxError(
                f"quote {quote_id} expired at {quote.expires_at.isoformat()}; "
                "request a new quote — CorridorOS will not execute at a rate the payer did not see"
            )
        execution = FxExecution(
            quote_id=quote_id,
            conversion=convert(amount, quote.buy_currency, quote.rate),
            executed_at=now,
            fee=quote.fee,
        )
        self._executions[quote_id] = execution
        self._audit.record(
            occurred_at=now,
            actor_role=actor_role,
            actor_id=actor_id,
            action="fx.execute",
            object_type="quote",
            object_id=quote_id,
            summary=(
                f"converted {amount.format()} to "
                f"{execution.conversion.target.format()} at {quote.rate}"
            ),
            payload=execution.conversion.as_row(),
        )
        return execution

    @property
    def quotes(self) -> tuple[FxQuote, ...]:
        return tuple(self._quotes.values())

    @property
    def executions(self) -> tuple[FxExecution, ...]:
        return tuple(self._executions.values())
