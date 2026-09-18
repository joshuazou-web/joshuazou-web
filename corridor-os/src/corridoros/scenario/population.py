"""The monitored population: entities, accounts, and ninety days of transfers.

RiskOps generated a world of wallets and merchants. This generator produces the
same *kind* of world for the corridor: Singapore operating entities of Chinese
parents, their suppliers across Southeast Asia, the customers paying them, and
the parent companies funding them — plus a small set of intermediaries, because
some of the shapes worth detecting need somewhere for money to pass through.

Three properties it has to have, or the evaluation that runs on it means
nothing:

**Seeded and deterministic.** The same seed produces the same world, so a
recall figure can be recomputed.

**Enriched with planted patterns that are marked.** Each planted scenario
carries a `scenario_id` and a role on every transfer it owns. That marking is
the ground truth — and `MonitoringContext.blind()` removes it before any
detector sees the feed, so recall measures detection rather than the label.

**Noisy in the ways that produce false positives honestly.** A collection
account legitimately receives from many unrelated customers, which is the funnel
shape; a corridor entity legitimately pays its suppliers within a day of being
funded, which is the rapid-movement shape. Those are left in. A world scrubbed
of its innocent look-alikes would report a precision nobody could get.

Every figure downstream of this file is therefore a **synthetic evaluation**,
and the enrichment means both recall and precision are far higher than any real
monitoring system would see. Neither number transfers to production traffic.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..risk.monitoring import MonitoredEntity, Transfer

WORLD_VERSION = "1.0.0"
DEFAULT_SEED = 20260914

# The feed's own clock. Fixed so the demonstration and its screenshots stay true.
AS_OF = datetime(2026, 9, 16, 7, 0, tzinfo=timezone.utc)
HISTORY_DAYS = 90

# Local currency to USD, as exact decimal strings would be overkill here: these
# are the feed's own normalisation rates, carried on the record so a reviewer can
# see what was applied.
USD_RATES: dict[str, float] = {
    "USD": 1.0,
    "SGD": 0.74,
    "CNY": 0.14,
    "HKD": 0.128,
    "MYR": 0.21,
    "THB": 0.028,
    "IDR": 0.000061,
}

INDUSTRIES = (
    "wholesale_trade",
    "electronics_manufacturing",
    "software_services",
    "logistics",
    "consumer_goods",
)

ON_PROFILE_PURPOSES = (
    "supplier_invoice",
    "logistics",
    "salary",
    "rent",
    "customs_duty",
    "components",
    "marketing",
    "cloud_services",
    "contractor_fee",
    "fuel",
)

OFF_PROFILE_PURPOSES = ("consulting_fee", "loan_repayment", "investment", "royalty")

SUPPLIER_COUNTRIES = ("SG", "MY", "TH", "VN", "CN", "HK", "ID")


@dataclass(frozen=True)
class PlantedScenario:
    """One deliberately created pattern, and what it should be detected as.

    `difficulty` separates two honest questions. A **clear** pattern sits well
    inside its typology's thresholds: failing to detect one would mean the
    detector is broken. A **borderline** pattern sits just inside them — three
    transfers spanning seventy-one of a seventy-two hour window, a return leg at
    72% against a 70% floor — where the windowing can legitimately miss it.
    Reporting one recall number over both would hide which of the two a change
    actually moved.
    """

    scenario_id: str
    typology_key: str
    subject_account: str
    transfer_ids: tuple[str, ...]
    note: str
    difficulty: str = "clear"


@dataclass
class Population:
    entities: dict[str, MonitoredEntity]
    accounts: dict[str, str]
    transfers: list[Transfer]
    planted: list[PlantedScenario] = field(default_factory=list)
    seed: int = DEFAULT_SEED
    world_version: str = WORLD_VERSION

    @property
    def planted_by_typology(self) -> dict[str, list[PlantedScenario]]:
        out: dict[str, list[PlantedScenario]] = {}
        for scenario in self.planted:
            out.setdefault(scenario.typology_key, []).append(scenario)
        return out


class _Builder:
    def __init__(self, seed: int) -> None:
        self.random = random.Random(seed)
        self.seed = seed
        self.entities: dict[str, MonitoredEntity] = {}
        self.accounts: dict[str, str] = {}
        self.transfers: list[Transfer] = []
        self.planted: list[PlantedScenario] = []
        self._counter = 0

    # -- helpers -----------------------------------------------------------

    def entity(
        self,
        entity_id: str,
        display_name: str,
        entity_type: str,
        country: str,
        *,
        industry: str = "",
        expected_monthly_usd: float = 0.0,
        risk_rating: str = "standard",
        kyb_status: str = "approved",
        owners: tuple[str, ...] = (),
    ) -> str:
        self.entities[entity_id] = MonitoredEntity(
            entity_id=entity_id,
            display_name=display_name,
            entity_type=entity_type,
            country=country,
            industry=industry,
            expected_monthly_usd=expected_monthly_usd,
            risk_rating=risk_rating,
            kyb_status=kyb_status,
            opened_at=AS_OF - timedelta(days=self.random.randint(120, 900)),
            owner_references=owners,
        )
        account_id = f"ACC-{entity_id}"
        self.accounts[account_id] = entity_id
        return account_id

    def transfer(
        self,
        *,
        when: datetime,
        payer_account: str,
        beneficiary_account: str,
        usd_amount: float,
        currency: str = "SGD",
        purpose: str = "supplier_invoice",
        beneficiary_information_status: str = "complete",
        channel: str = "bank_transfer",
        scenario_id: str | None = None,
        scenario_role: str | None = None,
    ) -> Transfer:
        self._counter += 1
        rate = USD_RATES[currency]
        usd_minor = int(round(usd_amount * 100))
        local_minor = int(round(usd_amount / rate * 100))
        payer_entity = self.accounts.get(payer_account, "")
        beneficiary_entity = self.accounts.get(beneficiary_account, "")
        record = Transfer(
            transfer_id=f"TRF{self._counter:06d}",
            timestamp=when,
            payer_account=payer_account,
            beneficiary_account=beneficiary_account,
            payer_entity_id=payer_entity,
            beneficiary_entity_id=beneficiary_entity,
            amount_minor=local_minor,
            currency=currency,
            amount_usd_minor=usd_minor,
            origin_country=self._country(payer_entity),
            destination_country=self._country(beneficiary_entity),
            declared_purpose=purpose,
            beneficiary_information_status=beneficiary_information_status,
            channel=channel,
            scenario_id=scenario_id,
            scenario_role=scenario_role,
        )
        self.transfers.append(record)
        return record

    def _country(self, entity_id: str) -> str:
        entity = self.entities.get(entity_id)
        return entity.country if entity else "XX"

    def moment(self, days_ago: float, hour: int | None = None) -> datetime:
        when = AS_OF - timedelta(days=days_ago)
        hour = self.random.randint(1, 20) if hour is None else hour
        return when.replace(hour=hour, minute=self.random.randint(0, 59), second=0, microsecond=0)


def build_population(seed: int = DEFAULT_SEED) -> Population:
    """Ninety days of transfers over a corridor population, with planted patterns."""
    builder = _Builder(seed)
    rng = builder.random

    # --- the population ---------------------------------------------------
    corridor_accounts: list[str] = []
    for index in range(8):
        owner = f"OWN-{index:02d}"
        account = builder.entity(
            f"CORR{index:02d}",
            f"Corridor Entity {index:02d} Pte. Ltd.",
            "corridor_entity",
            "SG",
            industry=INDUSTRIES[index % len(INDUSTRIES)],
            expected_monthly_usd=float(rng.choice([80_000, 120_000, 160_000, 240_000])),
            owners=(owner,),
        )
        corridor_accounts.append(account)
        builder.entity(
            f"PARENT{index:02d}",
            f"Parent Group {index:02d} Ltd.",
            "parent",
            "CN",
            industry=INDUSTRIES[index % len(INDUSTRIES)],
            owners=(owner,),
        )

    supplier_accounts = [
        builder.entity(
            f"SUP{index:03d}",
            f"Supplier {index:03d}",
            "supplier",
            rng.choice(SUPPLIER_COUNTRIES),
            industry="wholesale_trade",
            owners=(f"OWN-S{index:03d}",),
        )
        for index in range(40)
    ]
    customer_accounts = [
        builder.entity(
            f"CUST{index:03d}",
            f"Customer {index:03d}",
            "customer",
            rng.choice(("SG", "MY", "ID", "TH", "HK")),
            owners=(f"OWN-C{index:03d}",),
        )
        for index in range(70)
    ]
    intermediary_accounts = [
        builder.entity(
            f"INT{index:02d}",
            f"Intermediary {index:02d}",
            "intermediary",
            rng.choice(("HK", "VN", "ID", "MY")),
            risk_rating="elevated",
            kyb_status="approved",
            owners=(f"OWN-I{index:02d}",),
        )
        for index in range(10)
    ]

    # --- background traffic ----------------------------------------------
    # Ordinary corridor life: customers pay in, parents fund, suppliers get paid.
    for account in corridor_accounts:
        entity = builder.entities[builder.accounts[account]]
        monthly = entity.expected_monthly_usd
        for day in range(HISTORY_DAYS):
            if rng.random() < 0.55:
                builder.transfer(
                    when=builder.moment(HISTORY_DAYS - day),
                    payer_account=rng.choice(customer_accounts),
                    beneficiary_account=account,
                    usd_amount=round(rng.uniform(1_500, monthly / 8), 2),
                    purpose="customer_settlement",
                )
            if rng.random() < 0.45:
                builder.transfer(
                    when=builder.moment(HISTORY_DAYS - day),
                    payer_account=account,
                    beneficiary_account=rng.choice(supplier_accounts),
                    usd_amount=round(rng.uniform(800, monthly / 10), 2),
                    purpose=rng.choice(ON_PROFILE_PURPOSES),
                    beneficiary_information_status="complete" if rng.random() > 0.04 else "partial",
                )
            if day % 30 == 7:
                builder.transfer(
                    when=builder.moment(HISTORY_DAYS - day, hour=9),
                    payer_account=f"ACC-PARENT{corridor_accounts.index(account):02d}",
                    beneficiary_account=account,
                    usd_amount=round(rng.uniform(40_000, 90_000), 2),
                    currency="CNY",
                    purpose="intercompany_funding",
                )

    # --- planted patterns -------------------------------------------------
    _plant_structuring(builder, corridor_accounts, supplier_accounts)
    _plant_rapid_movement(builder, corridor_accounts, intermediary_accounts, customer_accounts)
    _plant_funnel(builder, intermediary_accounts, customer_accounts)
    _plant_circular(builder, corridor_accounts, intermediary_accounts)
    _plant_profile_mismatch(builder, corridor_accounts, supplier_accounts)
    _plant_missing_information(builder, corridor_accounts, supplier_accounts)

    return Population(
        entities=builder.entities,
        accounts=builder.accounts,
        transfers=builder.transfers,
        planted=builder.planted,
        seed=seed,
    )


# --------------------------------------------------------------------------- #
# The planted patterns. Each one is built to the typology's own thresholds, so
# a threshold change makes the generator and the detector disagree loudly rather
# than quietly.
# --------------------------------------------------------------------------- #


def _plant_structuring(builder: _Builder, corridor: list[str], suppliers: list[str]) -> None:
    rng = builder.random
    for index in range(3):
        account = corridor[index]
        scenario_id = f"SC_STRUCT_{index:02d}"
        start = 60 - index * 12
        beneficiaries = rng.sample(suppliers, 2)
        ids: list[str] = []
        for leg in range(rng.randint(4, 6)):
            record = builder.transfer(
                when=builder.moment(start - leg * 0.6, hour=9 + leg % 8),
                payer_account=account,
                beneficiary_account=beneficiaries[leg % 2],
                usd_amount=round(rng.uniform(7_200, 9_800), 2),
                purpose="supplier_invoice",
                scenario_id=scenario_id,
                scenario_role="structured_leg",
            )
            ids.append(record.transfer_id)
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "structuring",
                account,
                tuple(ids),
                "Several transfers sized just below the 10,000 USD reporting threshold.",
            )
        )

    # Borderline: the minimum three legs, spread across most of the 72-hour
    # window and over a day boundary, at the very top of the band.
    for index in range(2):
        account = corridor[3 + index]
        scenario_id = f"SC_STRUCT_B{index:02d}"
        beneficiary = rng.choice(suppliers)
        ids = []
        for leg, offset in enumerate((0.0, 1.35, 2.92)):
            record = builder.transfer(
                when=builder.moment(52 - index * 7 - offset, hour=(7 + leg * 5) % 24),
                payer_account=account,
                beneficiary_account=beneficiary,
                usd_amount=round(rng.uniform(9_500, 9_960), 2),
                purpose="supplier_invoice",
                scenario_id=scenario_id,
                scenario_role="structured_leg",
            )
            ids.append(record.transfer_id)
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "structuring",
                account,
                tuple(ids),
                "Three legs at the top of the band, spanning most of the 72-hour window.",
                difficulty="borderline",
            )
        )


def _plant_rapid_movement(
    builder: _Builder, corridor: list[str], intermediaries: list[str], customers: list[str]
) -> None:
    rng = builder.random
    for index in range(3):
        account = intermediaries[index]
        scenario_id = f"SC_RAPID_{index:02d}"
        day = 45 - index * 9
        amount = round(rng.uniform(18_000, 45_000), 2)
        inbound = builder.transfer(
            when=builder.moment(day, hour=8),
            payer_account=rng.choice(corridor),
            beneficiary_account=account,
            usd_amount=amount,
            purpose="supplier_invoice",
            scenario_id=scenario_id,
            scenario_role="inbound_leg",
        )
        outbound = builder.transfer(
            when=builder.moment(day - 0.25, hour=14),
            payer_account=account,
            beneficiary_account=rng.choice(customers),
            usd_amount=round(amount * rng.uniform(0.86, 0.96), 2),
            purpose="consulting_fee",
            scenario_id=scenario_id,
            scenario_role="outbound_leg",
        )
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "rapid_movement",
                account,
                (inbound.transfer_id, outbound.transfer_id),
                "Most of an arriving amount forwarded onward within hours.",
            )
        )

    # Borderline: 81-83% forwarded, twenty-three hours later — just inside both
    # thresholds, and the kind of thing a treasury sweep also looks like.
    for index in range(2):
        account = intermediaries[3 + index]
        scenario_id = f"SC_RAPID_B{index:02d}"
        day = 38 - index * 6
        amount = round(rng.uniform(6_000, 9_000), 2)
        inbound = builder.transfer(
            when=builder.moment(day, hour=6),
            payer_account=rng.choice(corridor),
            beneficiary_account=account,
            usd_amount=amount,
            purpose="supplier_invoice",
            scenario_id=scenario_id,
            scenario_role="inbound_leg",
        )
        outbound = builder.transfer(
            when=builder.moment(day - 0.95, hour=5),
            payer_account=account,
            beneficiary_account=rng.choice(customers),
            usd_amount=round(amount * rng.uniform(0.81, 0.83), 2),
            purpose="consulting_fee",
            scenario_id=scenario_id,
            scenario_role="outbound_leg",
        )
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "rapid_movement",
                account,
                (inbound.transfer_id, outbound.transfer_id),
                "Just over the pass-through floor, nearly a full day later.",
                difficulty="borderline",
            )
        )


def _plant_funnel(builder: _Builder, intermediaries: list[str], customers: list[str]) -> None:
    rng = builder.random
    for index in range(2):
        account = intermediaries[5 + index]
        scenario_id = f"SC_FUNNEL_{index:02d}"
        senders = rng.sample(customers, 11)
        ids: list[str] = []
        for position, sender in enumerate(senders):
            record = builder.transfer(
                when=builder.moment(30 - index * 10 - position * 0.7),
                payer_account=sender,
                beneficiary_account=account,
                usd_amount=round(rng.uniform(2_400, 5_200), 2),
                purpose="consulting_fee",
                scenario_id=scenario_id,
                scenario_role="funnel_leg",
            )
            ids.append(record.transfer_id)
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "funnel",
                account,
                tuple(ids),
                "Many unrelated senders paying one account inside a fortnight.",
            )
        )

    # Borderline: exactly the minimum eight senders, spread over almost the
    # whole fourteen-day window, totalling just above the floor.
    account = intermediaries[8]
    scenario_id = "SC_FUNNEL_B00"
    senders = rng.sample(customers, 8)
    ids = []
    for position, sender in enumerate(senders):
        record = builder.transfer(
            when=builder.moment(34 - position * 1.65),
            payer_account=sender,
            beneficiary_account=account,
            usd_amount=round(rng.uniform(2_600, 2_900), 2),
            purpose="consulting_fee",
            scenario_id=scenario_id,
            scenario_role="funnel_leg",
        )
        ids.append(record.transfer_id)
    builder.planted.append(
        PlantedScenario(
            scenario_id,
            "funnel",
            account,
            tuple(ids),
            "Exactly eight senders across almost the whole window, just above the total floor.",
            difficulty="borderline",
        )
    )


def _plant_circular(builder: _Builder, corridor: list[str], intermediaries: list[str]) -> None:
    rng = builder.random
    for index in range(2):
        origin = corridor[4 + index]
        hops = [intermediaries[index * 2], intermediaries[index * 2 + 1]]
        scenario_id = f"SC_CIRCLE_{index:02d}"
        amount = round(rng.uniform(40_000, 70_000), 2)
        day = 20 - index * 6
        legs = []
        legs.append(
            builder.transfer(
                when=builder.moment(day, hour=9),
                payer_account=origin,
                beneficiary_account=hops[0],
                usd_amount=amount,
                purpose="supplier_invoice",
                scenario_id=scenario_id,
                scenario_role="cycle_leg_1",
            )
        )
        legs.append(
            builder.transfer(
                when=builder.moment(day - 1, hour=11),
                payer_account=hops[0],
                beneficiary_account=hops[1],
                usd_amount=round(amount * 0.95, 2),
                purpose="consulting_fee",
                scenario_id=scenario_id,
                scenario_role="cycle_leg_2",
            )
        )
        legs.append(
            builder.transfer(
                when=builder.moment(day - 2, hour=15),
                payer_account=hops[1],
                beneficiary_account=origin,
                usd_amount=round(amount * 0.88, 2),
                purpose="loan_repayment",
                scenario_id=scenario_id,
                scenario_role="cycle_return",
            )
        )
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "circular",
                origin,
                tuple(leg.transfer_id for leg in legs),
                "Funds returning to their origin through two intermediaries inside a week.",
            )
        )

    # Borderline: 72% returns against a 70% floor, six days later against a
    # seven-day ceiling.
    origin = corridor[3]
    hops = [intermediaries[6], intermediaries[7]]
    scenario_id = "SC_CIRCLE_B00"
    amount = round(rng.uniform(12_000, 18_000), 2)
    legs = [
        builder.transfer(
            when=builder.moment(11, hour=10),
            payer_account=origin,
            beneficiary_account=hops[0],
            usd_amount=amount,
            purpose="supplier_invoice",
            scenario_id=scenario_id,
            scenario_role="cycle_leg_1",
        ),
        builder.transfer(
            when=builder.moment(8.5, hour=13),
            payer_account=hops[0],
            beneficiary_account=hops[1],
            usd_amount=round(amount * 0.78, 2),
            purpose="consulting_fee",
            scenario_id=scenario_id,
            scenario_role="cycle_leg_2",
        ),
        builder.transfer(
            when=builder.moment(5.1, hour=16),
            payer_account=hops[1],
            beneficiary_account=origin,
            usd_amount=round(amount * 0.72, 2),
            purpose="loan_repayment",
            scenario_id=scenario_id,
            scenario_role="cycle_return",
        ),
    ]
    builder.planted.append(
        PlantedScenario(
            scenario_id,
            "circular",
            origin,
            tuple(leg.transfer_id for leg in legs),
            "72% returned against a 70% floor, six days out of a seven-day ceiling.",
            difficulty="borderline",
        )
    )


def _plant_profile_mismatch(builder: _Builder, corridor: list[str], suppliers: list[str]) -> None:
    rng = builder.random
    for index in range(2):
        account = corridor[6 + index]
        entity = builder.entities[builder.accounts[account]]
        scenario_id = f"SC_PROFILE_{index:02d}"
        target = entity.expected_monthly_usd * rng.uniform(5.0, 6.5)
        ids: list[str] = []
        legs = 9
        for leg in range(legs):
            record = builder.transfer(
                when=builder.moment(25 - leg * 2.4),
                payer_account=account,
                beneficiary_account=rng.choice(suppliers),
                usd_amount=round(target / legs, 2),
                purpose=rng.choice(OFF_PROFILE_PURPOSES),
                scenario_id=scenario_id,
                scenario_role="off_profile_leg",
            )
            ids.append(record.transfer_id)
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "profile_mismatch",
                account,
                tuple(ids),
                "A month far above the declared expectation, on purposes outside the declared activity.",
            )
        )

    # Borderline: 4.2x the declared expectation against a 4x floor, and only one
    # transfer off profile.
    account = corridor[5]
    entity = builder.entities[builder.accounts[account]]
    scenario_id = "SC_PROFILE_B00"
    target = entity.expected_monthly_usd * 4.2
    ids = []
    for leg in range(7):
        record = builder.transfer(
            when=builder.moment(27 - leg * 3.1),
            payer_account=account,
            beneficiary_account=rng.choice(suppliers),
            usd_amount=round(target / 7, 2),
            purpose="royalty" if leg == 3 else "supplier_invoice",
            scenario_id=scenario_id,
            scenario_role="off_profile_leg",
        )
        ids.append(record.transfer_id)
    builder.planted.append(
        PlantedScenario(
            scenario_id,
            "profile_mismatch",
            account,
            tuple(ids),
            "4.2x the declared expectation against a 4x floor, one transfer off profile.",
            difficulty="borderline",
        )
    )


def _plant_missing_information(
    builder: _Builder, corridor: list[str], suppliers: list[str]
) -> None:
    rng = builder.random
    for index in range(3):
        account = corridor[index + 1]
        scenario_id = f"SC_MISSING_{index:02d}"
        ids: list[str] = []
        for leg in range(4):
            record = builder.transfer(
                when=builder.moment(15 - index * 3 - leg),
                payer_account=account,
                beneficiary_account=rng.choice(suppliers),
                usd_amount=round(rng.uniform(2_200, 6_500), 2),
                purpose="" if leg % 2 else "supplier_invoice",
                beneficiary_information_status="missing" if leg % 2 else "partial",
                scenario_id=scenario_id,
                scenario_role="incomplete_leg",
            )
            ids.append(record.transfer_id)
        builder.planted.append(
            PlantedScenario(
                scenario_id,
                "missing_information",
                account,
                tuple(ids),
                "Transfers that cannot be judged because beneficiary information or purpose is absent.",
            )
        )

    # Borderline: exactly the minimum three affected transfers, totalling just
    # above the 5,000 USD floor.
    account = corridor[7]
    scenario_id = "SC_MISSING_B00"
    ids = []
    for leg in range(3):
        record = builder.transfer(
            when=builder.moment(9 - leg * 1.5),
            payer_account=account,
            beneficiary_account=rng.choice(suppliers),
            usd_amount=round(rng.uniform(1_750, 1_900), 2),
            purpose="supplier_invoice" if leg else "",
            beneficiary_information_status="partial",
            scenario_id=scenario_id,
            scenario_role="incomplete_leg",
        )
        ids.append(record.transfer_id)
    builder.planted.append(
        PlantedScenario(
            scenario_id,
            "missing_information",
            account,
            tuple(ids),
            "Exactly three affected transfers, just above the amount floor.",
            difficulty="borderline",
        )
    )
