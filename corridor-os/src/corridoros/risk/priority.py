"""Investigation priority: which case a person should open next, and why.

Ported from `crossborder-riskops/src/riskops/aml/priority.py`. Its reasoning is
unchanged and worth restating:

    This is an ordering, not a verdict. Priority answers "given that we can
    review N cases today, which N?" — it says nothing about whether any of them
    is laundering, and a case that never reaches capacity has not been cleared,
    it has only not been looked at yet.

    A single opaque number would be useless here for a practical reason as well
    as a principled one. An investigator who disagrees with the ordering has to
    see *which factor* pushed a case up, and an analyst tuning the queue has to
    see which factor is dominating it. So every factor's contribution is
    computed separately, stored on the case, and rendered as a breakdown.

Each factor is normalised to 0..1 and multiplied by a weight. The weights are
declared here, sum to 1.0, and are asserted to — a table that silently stopped
summing to one would rescale every score and change the queue without changing
any threshold anyone could see.

Two factors were re-expressed for the corridor: RiskOps scored a customer's KYC
tier and account age, where this scores the entity's KYB status and risk rating;
and its device-based network breadth is counterparty-and-country breadth here,
because a corridor feed has no device.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

PRIORITY_VERSION = "1.0.0"

WEIGHTS: dict[str, float] = {
    "signal_strength": 0.20,  # how severe the typologies are
    "corroboration": 0.18,  # independent typologies agreeing
    "amount": 0.15,  # value at stake
    "velocity": 0.12,  # how fast the money moved
    "network_breadth": 0.12,  # how many counterparties and countries
    "information_gaps": 0.10,  # what we cannot see
    "entity_history": 0.08,  # the entity's own risk rating and KYB state
    "waiting_time": 0.05,  # queue fairness: age must eventually win
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "priority weights must sum to 1.0"

FACTOR_LABELS: dict[str, str] = {
    "signal_strength": "Signal strength",
    "corroboration": "Corroborating typologies",
    "amount": "Amount involved",
    "velocity": "Movement speed",
    "network_breadth": "Network breadth",
    "information_gaps": "Missing information",
    "entity_history": "Entity risk history",
    "waiting_time": "Time waiting in queue",
}

# Money is scored on a log scale between these two points: at or below the floor
# the amount factor contributes nothing, at or above the ceiling it contributes
# its full weight. A linear scale would let one very large case dominate the
# queue and flatten every difference below it.
AMOUNT_FLOOR_USD = 5_000.0
AMOUNT_CEILING_USD = 500_000.0

# Bands cut against the distribution these factors produce on the seeded world.
# They are not universal constants: a different population needs them re-cut, and
# the evaluation report prints the resulting band mix so a reader can see whether
# they still describe the data.
BANDS: tuple[tuple[float, str], ...] = (
    (0.45, "critical"),
    (0.36, "high"),
    (0.25, "medium"),
    (0.0, "low"),
)

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class Contribution:
    factor: str
    raw: float  # 0..1 before weighting
    weight: float
    points: float  # raw * weight — what it added to the score
    detail: str

    @property
    def label(self) -> str:
        return FACTOR_LABELS.get(self.factor, self.factor)

    def as_row(self) -> dict[str, object]:
        return {
            "factor": self.factor,
            "label": self.label,
            "raw": round(self.raw, 4),
            "weight": self.weight,
            "points": round(self.points, 4),
            "detail": self.detail,
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _contribution(factor: str, raw: float, detail: str) -> Contribution:
    weight = WEIGHTS[factor]
    raw = _clamp(raw)
    return Contribution(factor, raw, weight, raw * weight, detail)


def band_for(score: float) -> str:
    for cut, name in BANDS:
        if score >= cut:
            return name
    return "low"


def score(
    *,
    severities: tuple[str, ...],
    typology_keys: tuple[str, ...],
    total_usd_minor: int,
    span_hours: float,
    transfer_count: int,
    counterparties: int,
    countries: int,
    missing_information: bool,
    entity_risk_rating: str,
    entity_kyb_status: str,
    oldest_alert_at: datetime,
    now: datetime,
) -> tuple[float, tuple[Contribution, ...]]:
    """Score one case and return the factors that produced the number."""
    ranks = [SEVERITY_RANK.get(item, 1) for item in severities] or [1]
    strongest = max(ranks)
    contributions = [
        _contribution(
            "signal_strength",
            (strongest - 1) / 3,
            f"strongest typology severity: {max(severities, key=lambda s: SEVERITY_RANK.get(s, 1))}",
        ),
        _contribution(
            "corroboration",
            0.0 if len(set(typology_keys)) <= 1 else min(1.0, (len(set(typology_keys)) - 1) / 2),
            f"{len(set(typology_keys))} distinct typology/typologies on this subject",
        ),
    ]

    usd = total_usd_minor / 100
    if usd <= AMOUNT_FLOOR_USD:
        amount_raw = 0.0
    else:
        amount_raw = math.log(usd / AMOUNT_FLOOR_USD) / math.log(
            AMOUNT_CEILING_USD / AMOUNT_FLOOR_USD
        )
    contributions.append(_contribution("amount", amount_raw, f"{usd:,.0f} USD across the case"))

    per_day = transfer_count / max(1.0, span_hours / 24)
    contributions.append(
        _contribution(
            "velocity",
            min(1.0, per_day / 6.0),
            f"{transfer_count} transfers over {span_hours / 24:.1f} day(s)",
        )
    )
    contributions.append(
        _contribution(
            "network_breadth",
            min(1.0, (counterparties / 12) * 0.7 + (countries / 5) * 0.3),
            f"{counterparties} counterparties across {countries} country/countries",
        )
    )
    contributions.append(
        _contribution(
            "information_gaps",
            1.0 if missing_information else 0.0,
            "beneficiary information or purpose is absent"
            if missing_information
            else "nothing required is missing",
        )
    )

    history = {"high": 1.0, "elevated": 0.6, "standard": 0.2}.get(entity_risk_rating, 0.2)
    if entity_kyb_status != "approved":
        history = max(history, 0.8)
    contributions.append(
        _contribution(
            "entity_history",
            history,
            f"risk rating {entity_risk_rating}, KYB {entity_kyb_status}",
        )
    )

    waited_hours = max(0.0, (now - oldest_alert_at).total_seconds() / 3600)
    contributions.append(
        _contribution(
            "waiting_time",
            min(1.0, waited_hours / (24 * 14)),
            f"oldest alert is {waited_hours / 24:.1f} day(s) old",
        )
    )

    total = sum(item.points for item in contributions)
    return total, tuple(contributions)
