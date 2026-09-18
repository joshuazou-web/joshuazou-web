"""The AML layer: typologies, deduplication, priority, queue capacity, evaluation.

The properties asserted here are the ones that make the figures in
`docs/EVALUATION.md` mean anything. The most important is the first: a detector
that could read the generator's labels would report perfect recall and measure
nothing.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from corridoros.risk.aggregate import (
    CASE_STATES,
    FORBIDDEN_STATES,
    deduplicate,
    run_queue,
)
from corridoros.risk.detect import run_all
from corridoros.risk.evaluate import DEFAULT_CAPACITY, evaluate, evaluate_seed
from corridoros.risk.monitoring import MonitoringContext
from corridoros.risk.priority import WEIGHTS, band_for
from corridoros.risk.typologies import BY_ID, TYPOLOGIES
from corridoros.scenario.population import AS_OF, build_population


@pytest.fixture(scope="module")
def world():
    population = build_population()
    context = MonitoringContext.blind(
        tuple(population.transfers), population.entities, population.accounts, AS_OF
    )
    alerts = run_all(context)
    return population, context, alerts


# --- the provenance guard -------------------------------------------------


def test_a_context_carrying_generator_provenance_is_refused():
    population = build_population()
    planted = [item for item in population.transfers if item.is_planted]
    assert planted, "the generator must plant something for this test to mean anything"
    with pytest.raises(ValueError, match="generator provenance"):
        MonitoringContext(
            transfers=tuple(planted),
            entities=population.entities,
            accounts=population.accounts,
            now=AS_OF,
        )


def test_blind_removes_the_labels_detectors_must_not_see(world):
    _population, context, _alerts = world
    assert all(not transfer.is_planted for transfer in context.transfers)
    assert all(transfer.scenario_id is None for transfer in context.transfers)


# --- detection ------------------------------------------------------------


@pytest.mark.parametrize("typology", TYPOLOGIES, ids=lambda item: item.key)
def test_every_typology_detects_its_clear_planted_patterns(world, typology):
    population, _context, alerts = world
    clear = [
        scenario
        for scenario in population.planted
        if scenario.typology_key == typology.key and scenario.difficulty == "clear"
    ]
    assert clear, f"no clear scenario planted for {typology.key}"

    covered = {
        transfer_id
        for alert in alerts
        if BY_ID[alert.typology_id].key == typology.key
        for transfer_id in alert.transfer_ids
    }
    for scenario in clear:
        assert covered & set(scenario.transfer_ids), (
            f"{scenario.scenario_id} was planted well inside {typology.key}'s thresholds "
            "and should have been detected"
        )


def test_alert_identifiers_are_stable_across_runs(world):
    population, context, alerts = world
    again = run_all(
        MonitoringContext.blind(
            tuple(population.transfers), population.entities, population.accounts, AS_OF
        )
    )
    assert [item.alert_id for item in alerts] == [item.alert_id for item in again]
    assert context.transfers  # the feed was indexed, not consumed


def test_an_alert_names_the_transfers_it_rests_on_and_what_would_argue_against_it(world):
    _population, _context, alerts = world
    for alert in alerts[:20]:
        assert alert.transfer_ids
        assert alert.explanation
        assert alert.counter_evidence, "every typology carries innocent explanations to look for"
        assert alert.thresholds, "the printed threshold is what makes a rule arguable"


# --- deduplication and aggregation ---------------------------------------


def test_repeated_observations_collapse_and_the_widest_one_survives(world):
    _population, _context, alerts = world
    deduped, removed = deduplicate(alerts)

    assert removed > 0, "a daily re-evaluating detector must produce repeats to collapse"
    assert len(deduped) + removed == len(alerts)
    absorbed = sum(
        int(alert.features.get("duplicate_observations_absorbed", 0)) for alert in deduped
    )
    assert absorbed == removed, "nothing is silently discarded"


def test_one_subject_over_one_window_is_one_case(world):
    _population, context, alerts = world
    queue = run_queue(context, alerts, capacity=DEFAULT_CAPACITY, now=AS_OF)

    assert queue.cases
    assert len(queue.cases) < len(queue.deduplicated), "cases group alerts, not mirror them"
    multi = [case for case in queue.cases if len(case.typology_keys) > 1]
    assert multi, "the world should produce at least one subject with corroborating typologies"
    assert str(len(multi[0].typology_keys)) in multi[0].merge_rationale


# --- priority and capacity -----------------------------------------------


def test_priority_weights_sum_to_one_and_every_factor_is_visible(world):
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    _population, context, alerts = world
    queue = run_queue(context, alerts, capacity=DEFAULT_CAPACITY, now=AS_OF)
    case = queue.within_capacity[0]

    assert len(case.contributions) == len(WEIGHTS)
    assert all(item.detail for item in case.contributions)
    assert abs(sum(item.points for item in case.contributions) - case.priority_score) < 1e-9
    assert band_for(case.priority_score) == case.priority_band


def test_the_queue_splits_at_capacity_and_the_backlog_is_not_cleared(world):
    _population, context, alerts = world
    queue = run_queue(context, alerts, capacity=5, now=AS_OF)

    assert len(queue.within_capacity) == 5
    assert queue.backlog, "a capacity smaller than the caseload must leave a backlog"
    assert all(case.state == "new" for case in queue.backlog), "not looked at, not cleared"
    assert all(case.state == "queued" for case in queue.within_capacity)

    ordered = [case.priority_score for case in queue.cases]
    assert ordered == sorted(ordered, reverse=True)
    assert queue.within_capacity[-1].priority_score >= queue.backlog[0].priority_score


def test_no_case_state_asserts_that_a_crime_occurred():
    """The system can say a pattern is present. It cannot say a crime happened."""
    for forbidden in FORBIDDEN_STATES:
        assert forbidden not in CASE_STATES


# --- evaluation -----------------------------------------------------------


def test_evaluation_is_reproducible():
    first = evaluate_seed()[0].as_row()
    second = evaluate_seed()[0].as_row()
    assert first == second


def test_clear_patterns_are_found_and_borderline_ones_are_reported_separately():
    report = evaluate()
    headline = report["headline"]

    assert headline["recall_clear"]["mean"] == 1.0
    assert 0.0 < headline["recall_borderline"]["mean"] <= 1.0
    assert headline["recall_borderline"]["mean"] < headline["recall_clear"]["mean"], (
        "a blended recall would hide which half a threshold change moved"
    )


def test_the_ordering_is_the_product_not_the_alert():
    headline = evaluate()["headline"]
    assert headline["raw_alert_precision"]["mean"] < 0.5, "raw alerts are mostly noise, as they are anywhere"
    assert (
        headline["precision_at_capacity"]["mean"] > headline["raw_alert_precision"]["mean"] * 3
    ), "prioritisation has to be worth a day of work"


def test_the_backlog_count_is_reported_rather_than_omitted():
    headline = evaluate()["headline"]
    assert "planted_patterns_left_in_backlog" in headline
    assert headline["planted_patterns_left_in_backlog"]["mean"] > 0, (
        "with a capacity smaller than the caseload, some planted patterns are not reached — "
        "and the honest report says how many"
    )


def test_the_report_carries_its_own_caveat_and_versions():
    report = evaluate()
    assert "synthetic" in report["dataset"]["kind"]
    assert "No real business" in report["dataset"]["caveat"]
    assert "No model participates" in report["boundary"]
    for key in ("typology_version", "priority_version", "aggregation_version", "world_version"):
        assert report[key]


# --- no model anywhere in the layer --------------------------------------


def test_nothing_in_an_alert_or_a_case_can_carry_a_decision(world):
    _population, context, alerts = world
    queue = run_queue(context, alerts, capacity=DEFAULT_CAPACITY, now=AS_OF)
    forbidden = {"decision", "recommendation", "verdict", "action", "approved", "disposition"}

    assert not (set(alerts[0].as_row()) & forbidden)
    assert not (set(queue.within_capacity[0].as_row()) & forbidden)


def test_a_detector_reads_the_feed_and_nothing_else(world):
    """Shifting a planted pattern's timestamps changes the alert, so the alert is
    a function of the transfers rather than of anything remembered elsewhere."""
    population, _context, _alerts = world
    shifted = tuple(
        replace(transfer, timestamp=transfer.timestamp - timedelta(days=400))
        if transfer.scenario_id and transfer.scenario_id.startswith("SC_STRUCT_00")
        else transfer
        for transfer in population.transfers
    )
    context = MonitoringContext.blind(shifted, population.entities, population.accounts, AS_OF)
    moved = run_all(context)
    original_keys = {alert.dedup_key for alert in _alerts}
    assert {alert.dedup_key for alert in moved} != original_keys
