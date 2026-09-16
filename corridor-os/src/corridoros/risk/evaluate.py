"""Evaluation of the AML layer, on synthetic data, with its limits attached.

What is measured, and what each figure does and does not mean:

**Scenario recall** — of the patterns the generator planted, how many did the
detectors find from behaviour alone? The detectors never see `scenario_id`
(`MonitoringContext.blind()` removes it and the constructor refuses a feed that
still carries it), so this is a measurement rather than a restatement of the
label. It is reported split by difficulty: a **clear** pattern sits well inside
its thresholds, a **borderline** one just inside them. A single blended number
would let a threshold change look harmless while it quietly stopped catching
everything near the edge.

**Raw alert precision** — what share of alerts touch a planted pattern? It is
low, as it is in every real monitoring system, and that is the point: the
product is not the alert, it is the ordering.

**Precision at review capacity** — of the cases a team of this size could
actually open today, what share contain a planted pattern? The gap between this
and raw precision is what the queue is for.

**Planted patterns in the backlog** — the honest half. Cases below the capacity
line were **not cleared**; they were not looked at. Counting the planted
patterns sitting there is a headline row, not a footnote.

Every number here comes from a seeded synthetic world that is deliberately
enriched with patterns. Recall and precision are both far higher than any real
monitoring system would see, and neither transfers to production traffic.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..scenario.population import AS_OF, DEFAULT_SEED, WORLD_VERSION, Population, build_population
from .aggregate import AGGREGATION_VERSION, QueueResult, run_queue
from .detect import run_all
from .monitoring import MonitoringContext
from .priority import PRIORITY_VERSION
from .typologies import BY_ID, TYPOLOGIES, TYPOLOGY_VERSION

EVAL_VERSION = "1.0.0"
DEFAULT_SEEDS: tuple[int, ...] = (DEFAULT_SEED, DEFAULT_SEED + 1, DEFAULT_SEED + 2)
DEFAULT_CAPACITY = 12


@dataclass(frozen=True)
class SeedResult:
    seed: int
    transfers: int
    raw_alerts: int
    deduplicated_alerts: int
    duplicates_removed: int
    cases: int
    capacity: int
    backlog_cases: int
    planted: int
    detected: int
    recall_by_typology: dict[str, float]
    recall_clear: float
    recall_borderline: float
    raw_alert_precision: float
    precision_at_capacity: float
    planted_in_backlog: int
    band_mix: dict[str, int] = field(default_factory=dict)

    @property
    def scenario_recall(self) -> float:
        return self.detected / self.planted if self.planted else 0.0

    def as_row(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "transfers": self.transfers,
            "raw_alerts": self.raw_alerts,
            "deduplicated_alerts": self.deduplicated_alerts,
            "duplicates_removed": self.duplicates_removed,
            "cases": self.cases,
            "capacity": self.capacity,
            "backlog_cases": self.backlog_cases,
            "planted": self.planted,
            "detected": self.detected,
            "scenario_recall": round(self.scenario_recall, 4),
            "recall_clear": round(self.recall_clear, 4),
            "recall_borderline": round(self.recall_borderline, 4),
            "recall_by_typology": {k: round(v, 4) for k, v in self.recall_by_typology.items()},
            "raw_alert_precision": round(self.raw_alert_precision, 4),
            "precision_at_capacity": round(self.precision_at_capacity, 4),
            "planted_in_backlog": self.planted_in_backlog,
            "band_mix": self.band_mix,
        }


def _planted_transfer_index(population: Population) -> dict[str, set[str]]:
    """transfer_id -> the typology keys whose planted scenarios own that transfer."""
    index: dict[str, set[str]] = {}
    for scenario in population.planted:
        for transfer_id in scenario.transfer_ids:
            index.setdefault(transfer_id, set()).add(scenario.typology_key)
    return index


def evaluate_seed(
    seed: int = DEFAULT_SEED, *, capacity: int = DEFAULT_CAPACITY, now: datetime = AS_OF
) -> tuple[SeedResult, QueueResult, Population]:
    population = build_population(seed)
    context = MonitoringContext.blind(
        tuple(population.transfers), population.entities, population.accounts, now
    )
    alerts = run_all(context)
    queue = run_queue(context, alerts, capacity=capacity, now=now)

    planted_index = _planted_transfer_index(population)

    def attributable(alert) -> bool:
        key = BY_ID[alert.typology_id].key
        return any(key in planted_index.get(transfer_id, set()) for transfer_id in alert.transfer_ids)

    # Recall: a planted scenario is detected when an alert of the same typology
    # covers at least one of its transfers.
    detected_scenarios: set[str] = set()
    for alert in alerts:
        key = BY_ID[alert.typology_id].key
        for scenario in population.planted:
            if scenario.typology_key != key:
                continue
            if set(alert.transfer_ids) & set(scenario.transfer_ids):
                detected_scenarios.add(scenario.scenario_id)

    recall_by_typology: dict[str, float] = {}
    for typology in TYPOLOGIES:
        scenarios = [s for s in population.planted if s.typology_key == typology.key]
        if not scenarios:
            continue
        hit = sum(1 for s in scenarios if s.scenario_id in detected_scenarios)
        recall_by_typology[typology.key] = hit / len(scenarios)

    def _recall(difficulty: str) -> float:
        scenarios = [s for s in population.planted if s.difficulty == difficulty]
        if not scenarios:
            return 0.0
        return sum(1 for s in scenarios if s.scenario_id in detected_scenarios) / len(scenarios)

    raw_precision = (
        sum(1 for alert in alerts if attributable(alert)) / len(alerts) if alerts else 0.0
    )
    within = queue.within_capacity
    precision_at_capacity = (
        sum(1 for case in within if any(attributable(alert) for alert in case.alerts)) / len(within)
        if within
        else 0.0
    )

    # A planted scenario is "in the backlog" when nothing that covers it reached
    # the capacity line.
    reached: set[str] = set()
    for case in within:
        for alert in case.alerts:
            key = BY_ID[alert.typology_id].key
            for scenario in population.planted:
                if scenario.typology_key == key and set(alert.transfer_ids) & set(
                    scenario.transfer_ids
                ):
                    reached.add(scenario.scenario_id)
    planted_in_backlog = len(detected_scenarios - reached)

    band_mix: dict[str, int] = {}
    for case in queue.cases:
        band_mix[case.priority_band] = band_mix.get(case.priority_band, 0) + 1

    result = SeedResult(
        seed=seed,
        transfers=len(population.transfers),
        raw_alerts=len(alerts),
        deduplicated_alerts=len(queue.deduplicated),
        duplicates_removed=queue.duplicates_removed,
        cases=len(queue.cases),
        capacity=capacity,
        backlog_cases=len(queue.backlog),
        planted=len(population.planted),
        detected=len(detected_scenarios),
        recall_by_typology=recall_by_typology,
        recall_clear=_recall("clear"),
        recall_borderline=_recall("borderline"),
        raw_alert_precision=raw_precision,
        precision_at_capacity=precision_at_capacity,
        planted_in_backlog=planted_in_backlog,
        band_mix=band_mix,
    )
    return result, queue, population


def _spread(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(statistics.fmean(values), 4),
        "stdev": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "n_seeds": len(values),
    }


def evaluate(
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    *,
    capacity: int = DEFAULT_CAPACITY,
    now: datetime = AS_OF,
) -> dict[str, Any]:
    """Run the whole AML layer over several independently generated worlds."""
    results = [evaluate_seed(seed, capacity=capacity, now=now)[0] for seed in seeds]

    by_typology: dict[str, dict[str, float]] = {}
    for typology in TYPOLOGIES:
        values = [
            item.recall_by_typology[typology.key]
            for item in results
            if typology.key in item.recall_by_typology
        ]
        if values:
            by_typology[typology.typology_id] = _spread(values)

    return {
        "eval_version": EVAL_VERSION,
        "typology_version": TYPOLOGY_VERSION,
        "priority_version": PRIORITY_VERSION,
        "aggregation_version": AGGREGATION_VERSION,
        "world_version": WORLD_VERSION,
        "generated_at": now.isoformat(),
        "dataset": {
            "kind": "synthetic, seeded, deliberately enriched with planted patterns",
            "seeds": list(seeds),
            "transfers_per_seed": results[0].transfers,
            "review_capacity": capacity,
            "caveat": (
                "Every figure here was produced by corridoros.scenario.population. No real "
                "business, account, supplier or transfer is involved. The population is "
                "deliberately enriched, so recall and precision are both far higher than any "
                "real monitoring system would see, and neither transfers to production traffic."
            ),
        },
        "headline": {
            "scenario_recall": _spread([item.scenario_recall for item in results]),
            "recall_clear": _spread([item.recall_clear for item in results]),
            "recall_borderline": _spread([item.recall_borderline for item in results]),
            "raw_alert_precision": _spread([item.raw_alert_precision for item in results]),
            "precision_at_capacity": _spread([item.precision_at_capacity for item in results]),
            "planted_patterns_left_in_backlog": _spread(
                [float(item.planted_in_backlog) for item in results]
            ),
        },
        "funnel": {
            "raw_alerts": _spread([float(item.raw_alerts) for item in results]),
            "after_deduplication": _spread([float(item.deduplicated_alerts) for item in results]),
            "cases": _spread([float(item.cases) for item in results]),
            "within_capacity": _spread([float(item.capacity) for item in results]),
            "backlog_cases": _spread([float(item.backlog_cases) for item in results]),
        },
        "recall_by_typology": by_typology,
        "per_seed": [item.as_row() for item in results],
        "boundary": (
            "No model participates in detection, deduplication, aggregation or prioritisation. "
            "Every alert above is reproducible from the transfer feed alone."
        ),
    }
