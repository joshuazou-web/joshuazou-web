"""The monitored transfer feed.

Transaction monitoring does not read the platform's own instruction table. It
reads the movements reported on the entity's accounts — the platform's own
payouts among them, but also collections from customers, funding from the
parent company, and anything else the bank feed carries. Monitoring only what
you yourself initiated finds nothing, because the shapes that matter are made
of other people's money arriving.

So this module holds a feed of `Transfer` records with two sources: the
platform's settled payments and collections, and the synthetic bank feed for
the same accounts (`scenario/population.py`). Detectors read the feed, never
the platform's objects.

**The provenance guard.** The generator marks the transfers it planted with
`scenario_id` and `scenario_role`. A detector that reads those columns would
report a recall of 1.000 and mean nothing by it. `MonitoringContext.blind()`
removes them, and the constructor raises if they are present — the guarantee is
structural rather than a matter of discipline. That check is ported from
RiskOps, where it was the reason its recall figures were measurements.

Ported without pandas: the domain layer here has no third-party dependency, so
the indexes are plain dicts built once. At the scale this demonstration runs
(tens of thousands of transfers) the difference is not worth a dependency.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import datetime

PROVENANCE_FIELDS = ("scenario_id", "scenario_role")

BENEFICIARY_INFORMATION_STATUSES = ("complete", "partial", "missing")


@dataclass(frozen=True)
class MonitoredEntity:
    """A party in the feed: a corridor entity, a supplier, a customer, a parent."""

    entity_id: str
    display_name: str
    entity_type: str  # corridor_entity | supplier | customer | parent | intermediary
    country: str
    industry: str = ""
    expected_monthly_usd: float = 0.0
    risk_rating: str = "standard"  # standard | elevated | high
    kyb_status: str = "approved"
    opened_at: datetime | None = None
    owner_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class Transfer:
    """One movement on a monitored account.

    `amount_usd_minor` is the normalised value every threshold is expressed in;
    the original currency and amount are kept beside it so an investigator sees
    what the business actually sent.
    """

    transfer_id: str
    timestamp: datetime
    payer_account: str
    beneficiary_account: str
    payer_entity_id: str
    beneficiary_entity_id: str
    amount_minor: int
    currency: str
    amount_usd_minor: int
    origin_country: str
    destination_country: str
    declared_purpose: str = ""
    beneficiary_information_status: str = "complete"
    channel: str = "bank_transfer"
    payment_id: str | None = None
    reversal_of: str | None = None
    # Generator provenance. Present on a raw feed, absent from anything a
    # detector is allowed to see.
    scenario_id: str | None = None
    scenario_role: str | None = None

    def blinded(self) -> Transfer:
        return replace(self, scenario_id=None, scenario_role=None)

    @property
    def is_planted(self) -> bool:
        return self.scenario_id is not None


@dataclass
class MonitoringContext:
    """Everything the detectors read, indexed once rather than per detector."""

    transfers: tuple[Transfer, ...]
    entities: dict[str, MonitoredEntity]
    accounts: dict[str, str]  # account_id -> entity_id
    now: datetime
    _blinded: bool = field(default=False, repr=False)

    by_payer: dict[str, list[Transfer]] = field(default_factory=dict, init=False)
    by_beneficiary: dict[str, list[Transfer]] = field(default_factory=dict, init=False)

    @classmethod
    def blind(
        cls,
        transfers: tuple[Transfer, ...],
        entities: dict[str, MonitoredEntity],
        accounts: dict[str, str],
        now: datetime,
    ) -> MonitoringContext:
        """Build a context the generator's provenance cannot reach.

        The pipeline uses this. Passing raw transfers would work, and would
        quietly make every recall number meaningless the first time someone
        wrote `transfer.scenario_id` inside a detector.
        """
        return cls(
            transfers=tuple(item.blinded() for item in transfers),
            entities=entities,
            accounts=accounts,
            now=now,
            _blinded=True,
        )

    def __post_init__(self) -> None:
        leaked = [item.transfer_id for item in self.transfers if item.is_planted]
        if leaked:
            raise ValueError(
                f"the detector context was given generator provenance on {len(leaked)} "
                "transfer(s); build it with MonitoringContext.blind() so recall measures "
                "detection rather than the label"
            )
        # Sorted once, here, so every detector walks the feed in the same order
        # and two runs over the same data produce identical alerts.
        self.transfers = tuple(
            sorted(self.transfers, key=lambda item: (item.timestamp, item.transfer_id))
        )

        by_payer: dict[str, list[Transfer]] = defaultdict(list)
        by_beneficiary: dict[str, list[Transfer]] = defaultdict(list)
        for transfer in self.transfers:
            by_payer[transfer.payer_account].append(transfer)
            by_beneficiary[transfer.beneficiary_account].append(transfer)
        self.by_payer = dict(by_payer)
        self.by_beneficiary = dict(by_beneficiary)

    # -- lookups -----------------------------------------------------------

    def entity_of(self, account_id: str) -> MonitoredEntity | None:
        entity_id = self.accounts.get(account_id)
        if entity_id is None:
            return None
        return self.entities.get(entity_id)

    def owners_of(self, account_id: str) -> frozenset[str]:
        entity = self.entity_of(account_id)
        return frozenset(entity.owner_references) if entity else frozenset()

    def ownership_status(self, account_id: str) -> str:
        entity = self.entity_of(account_id)
        if entity is None:
            return "missing"
        if not entity.owner_references:
            return "missing"
        return "verified" if entity.kyb_status == "approved" else "unverified"

    def monitored_accounts(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.by_payer) | set(self.by_beneficiary)))


def usd(minor: int) -> str:
    """Whole-dollar presentation for an explanation. Never used for comparison."""
    return f"{minor / 100:,.0f}"
