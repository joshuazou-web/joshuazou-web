"""Double-entry ledger.

The corridor blueprint specified this and never implemented it. It is the piece
that makes the rest of the platform arguable rather than decorative: without a
ledger, "the payment settled" is a status field, and a status field cannot
disagree with a bank statement.

Four rules, all of them enforced rather than described:

**Balances are derived, never stored.** A balance is the sum of the entries.
There is no row to update, so there is no row to update wrongly.

**A journal must balance per currency.** Debits equal credits or the posting is
refused whole. A partially applied journal is the failure mode that makes a
reconciliation break impossible to explain afterwards.

**Entries are immutable.** A correction is a reversal — a new journal with the
signs flipped and a reference to what it reverses. The original stays. This is
what "corrections occur through reversal, never silent editing" means in code.

**Buckets are separate accounts, not attributes.** `available`, `pending`,
`reserved` and `payable` are different accounts for the same business and
currency, so "reserved for a payment awaiting approval" is a posting between
two accounts and shows up in the journal, rather than a flag that some other
code has to remember to check.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.errors import LedgerError
from ..core.ids import IdFactory, validate
from ..core.money import Money

BUCKETS = ("available", "pending", "reserved", "payable", "fx_suspense", "external")


def account_id(business_id: str, currency: str, bucket: str) -> str:
    """Accounts are named, not numbered: an operator reads them in a journal."""
    if bucket not in BUCKETS:
        raise LedgerError(f"unknown ledger bucket {bucket!r}; known: {BUCKETS}")
    if bucket == "external":
        return f"EXTERNAL:{currency.upper()}"
    validate(business_id, "business")
    return f"{business_id}:{currency.upper()}:{bucket}"


@dataclass(frozen=True)
class Leg:
    """One side of a journal. Positive is a debit, negative a credit."""

    account: str
    amount: Money
    memo: str = ""


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    journal_id: str
    account: str
    amount: Money
    posted_at: datetime
    memo: str
    reverses_journal_id: str | None = None
    payment_id: str | None = None


@dataclass(frozen=True)
class Journal:
    journal_id: str
    posted_at: datetime
    description: str
    entries: tuple[LedgerEntry, ...]
    reverses_journal_id: str | None = None
    payment_id: str | None = None


class Ledger:
    def __init__(self, ids: IdFactory | None = None) -> None:
        self._ids = ids or IdFactory("led")
        self._journals: list[Journal] = []
        self._entries: list[LedgerEntry] = []
        self._reversed: set[str] = set()

    # -- posting -----------------------------------------------------------

    def post(
        self,
        legs: list[Leg],
        *,
        posted_at: datetime,
        description: str,
        payment_id: str | None = None,
        reverses_journal_id: str | None = None,
    ) -> Journal:
        if len(legs) < 2:
            raise LedgerError("a journal needs at least two legs; one leg cannot balance")

        totals: dict[str, int] = {}
        for leg in legs:
            totals[leg.amount.currency] = totals.get(leg.amount.currency, 0) + leg.amount.minor_units
        unbalanced = {code: total for code, total in totals.items() if total != 0}
        if unbalanced:
            detail = ", ".join(f"{code} off by {total}" for code, total in sorted(unbalanced.items()))
            raise LedgerError(f"journal does not balance ({detail}); nothing was posted")

        journal_id = self._ids.next("ledger_entry")
        entries = tuple(
            LedgerEntry(
                entry_id=self._ids.next("ledger_entry"),
                journal_id=journal_id,
                account=leg.account,
                amount=leg.amount,
                posted_at=posted_at,
                memo=leg.memo or description,
                reverses_journal_id=reverses_journal_id,
                payment_id=payment_id,
            )
            for leg in legs
        )
        journal = Journal(
            journal_id=journal_id,
            posted_at=posted_at,
            description=description,
            entries=entries,
            reverses_journal_id=reverses_journal_id,
            payment_id=payment_id,
        )
        self._journals.append(journal)
        self._entries.extend(entries)
        return journal

    def reverse(self, journal_id: str, *, posted_at: datetime, reason: str) -> Journal:
        """Post the mirror image of `journal_id`. The original is untouched."""
        if journal_id in self._reversed:
            raise LedgerError(f"journal {journal_id} has already been reversed")
        original = self.journal(journal_id)
        self._reversed.add(journal_id)
        return self.post(
            [Leg(entry.account, -entry.amount, f"reversal: {reason}") for entry in original.entries],
            posted_at=posted_at,
            description=f"Reversal of {journal_id}: {reason}",
            payment_id=original.payment_id,
            reverses_journal_id=journal_id,
        )

    # -- reading -----------------------------------------------------------

    def journal(self, journal_id: str) -> Journal:
        for item in self._journals:
            if item.journal_id == journal_id:
                return item
        raise LedgerError(f"unknown journal {journal_id}")

    @property
    def journals(self) -> tuple[Journal, ...]:
        return tuple(self._journals)

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def balance(self, account: str, currency: str) -> Money:
        total = Money.zero(currency)
        for entry in self._entries:
            if entry.account == account and entry.amount.currency == currency:
                total = total + entry.amount
        return total

    def balances(self, business_id: str, currency: str) -> dict[str, Money]:
        return {
            bucket: self.balance(account_id(business_id, currency, bucket), currency)
            for bucket in ("available", "pending", "reserved", "payable")
        }

    def entries_for_payment(self, payment_id: str) -> tuple[LedgerEntry, ...]:
        return tuple(entry for entry in self._entries if entry.payment_id == payment_id)

    def is_balanced(self) -> bool:
        """Every currency across every account nets to zero, always."""
        totals: dict[str, int] = {}
        for entry in self._entries:
            code = entry.amount.currency
            totals[code] = totals.get(code, 0) + entry.amount.minor_units
        return all(total == 0 for total in totals.values())
