"""The monitored feed: the platform's own money movements, plus the population.

Transaction monitoring reads the bank feed, not the instruction table. So the
feed the detectors see is the union of two things:

  * every movement CorridorOS itself produced — each settled payout and each
    attributed collection, carrying its `payment_id` so an alert can be walked
    straight back to the payment screen;
  * the synthetic population in `population.py`, which is the rest of the
    corridor's traffic: other entities, their suppliers, their customers, and
    the planted patterns the evaluation measures against.

Keeping both in one feed is the point. The flagship SGD 12,500 payment appears
in the AML queue's world rather than in a separate demonstration, which is the
thing four separate projects could not do.
"""

from __future__ import annotations

from datetime import datetime

from ..platform import CorridorOS
from ..risk.aggregate import QueueResult, run_queue
from ..risk.detect import run_all
from ..risk.monitoring import MonitoredEntity, MonitoringContext, Transfer
from .population import AS_OF, DEFAULT_SEED, USD_RATES, Population, build_population


def _usd_minor(amount_minor: int, currency: str) -> int:
    return int(round(amount_minor * USD_RATES.get(currency, 1.0)))


def platform_transfers(system: CorridorOS) -> tuple[list[Transfer], dict[str, MonitoredEntity], dict[str, str]]:
    """Everything the platform itself moved, as feed records."""
    entities: dict[str, MonitoredEntity] = {}
    accounts: dict[str, str] = {}
    transfers: list[Transfer] = []

    for business in system.businesses.all:
        entities[business.business_id] = MonitoredEntity(
            entity_id=business.business_id,
            display_name=business.legal_name,
            entity_type="corridor_entity",
            country=business.entity_country,
            industry="wholesale_trade",
            expected_monthly_usd=_usd_minor(
                business.expected_monthly_volume.minor_units,
                business.expected_monthly_volume.currency,
            )
            / 100,
            kyb_status=business.review_status,
            owner_references=(f"OWN-{business.business_id}",),
        )
        accounts[f"ACC-{business.business_id}"] = business.business_id

    for beneficiary in system.beneficiaries.all:
        entities[beneficiary.beneficiary_id] = MonitoredEntity(
            entity_id=beneficiary.beneficiary_id,
            display_name=beneficiary.display_name,
            entity_type="supplier",
            country=beneficiary.bank_country,
            industry="wholesale_trade",
            owner_references=(f"OWN-{beneficiary.beneficiary_id}",),
        )
        accounts[f"ACC-{beneficiary.beneficiary_id}"] = beneficiary.beneficiary_id

    for intent in system.collections.all:
        if intent.attributed_amount is None:
            continue
        payer_entity = f"CUSTOMER-{intent.reference}"
        entities[payer_entity] = MonitoredEntity(
            entity_id=payer_entity,
            display_name=f"Customer on {intent.reference}",
            entity_type="customer",
            country="SG",
            owner_references=(f"OWN-{payer_entity}",),
        )
        accounts[f"ACC-{payer_entity}"] = payer_entity
        transfers.append(
            Transfer(
                transfer_id=f"PLT-{intent.intent_id}",
                timestamp=intent.created_at,
                payer_account=f"ACC-{payer_entity}",
                beneficiary_account=f"ACC-{intent.business_id}",
                payer_entity_id=payer_entity,
                beneficiary_entity_id=intent.business_id,
                amount_minor=intent.attributed_amount.minor_units,
                currency=intent.attributed_amount.currency,
                amount_usd_minor=_usd_minor(
                    intent.attributed_amount.minor_units, intent.attributed_amount.currency
                ),
                origin_country="SG",
                destination_country="SG",
                declared_purpose="customer_settlement",
                channel="paynow_corporate",
            )
        )

    for payment in system.payouts.all:
        if payment.state not in ("submitted", "accepted", "settled"):
            continue
        beneficiary = system.beneficiaries.get(payment.beneficiary_id)
        packet_complete = not payment.outstanding_verifications
        transfers.append(
            Transfer(
                transfer_id=f"PLT-{payment.payment_id}",
                timestamp=payment.submitted_at or payment.created_at,
                payer_account=f"ACC-{payment.business_id}",
                beneficiary_account=f"ACC-{payment.beneficiary_id}",
                payer_entity_id=payment.business_id,
                beneficiary_entity_id=payment.beneficiary_id,
                amount_minor=payment.amount.minor_units,
                currency=payment.amount.currency,
                amount_usd_minor=_usd_minor(payment.amount.minor_units, payment.amount.currency),
                origin_country="SG",
                destination_country=beneficiary.bank_country,
                declared_purpose=payment.purpose_code.lower(),
                beneficiary_information_status="complete" if packet_complete else "partial",
                payment_id=payment.payment_id,
            )
        )

    return transfers, entities, accounts


def build_feed(
    system: CorridorOS | None = None,
    *,
    seed: int = DEFAULT_SEED,
    now: datetime = AS_OF,
) -> tuple[MonitoringContext, Population]:
    """The population and the platform's own movements, as one blinded context."""
    population = build_population(seed)
    transfers = list(population.transfers)
    entities = dict(population.entities)
    accounts = dict(population.accounts)

    if system is not None:
        platform_rows, platform_entities, platform_accounts = platform_transfers(system)
        transfers.extend(platform_rows)
        entities.update(platform_entities)
        accounts.update(platform_accounts)

    context = MonitoringContext.blind(tuple(transfers), entities, accounts, now)
    return context, population


def run_monitoring(
    system: CorridorOS | None = None,
    *,
    seed: int = DEFAULT_SEED,
    capacity: int = 12,
    now: datetime = AS_OF,
) -> tuple[QueueResult, MonitoringContext, Population]:
    """A day's monitoring run over the whole corridor."""
    context, population = build_feed(system, seed=seed, now=now)
    alerts = run_all(context)
    queue = run_queue(context, alerts, capacity=capacity, now=now)
    return queue, context, population
