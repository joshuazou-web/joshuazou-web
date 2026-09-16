"""Turn alerts into cases: deduplicate, then group, then order.

Ported from `crossborder-riskops/src/riskops/aml/aggregate.py`, whose framing of
the problem is exactly the one this platform has:

    One rule firing on forty transfers produces forty alerts; six rules over one
    account produce six queues to work; and an investigator who has to
    reconstruct that they are all the same story does it forty-six times a day
    until they stop reading.

    So: an alert is not a case. A case is a *subject over a window*, carrying
    every alert that belongs to it, and the reason each alert was merged is
    written down. A merge is a judgement that two things are one story, and if
    it is wrong the investigator needs to see the reasoning to overturn it.

Nothing here decides anything about a business. Aggregation decides what lands
on one screen.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from .detect import AmlAlert
from .monitoring import MonitoringContext
from .priority import Contribution, band_for, score
from .typologies import BY_ID, SEVERITY_ORDER

AGGREGATION_VERSION = "1.0.0"

# Two alerts of the same typology on the same subject inside this window are the
# same finding observed twice, not two findings.
DEDUP_WINDOW = timedelta(days=7)

# Alerts on one subject within this window belong to one case. Longer than the
# dedup window because a case is a story about an account over a period, and a
# structuring burst on Monday plus a funnel pattern on Friday is one story.
CASE_WINDOW = timedelta(days=30)

CASE_STATES = (
    "new",
    "queued",
    "investigating",
    "awaiting_information",
    "monitoring",
    "escalated",
    "closed_no_action",
)

# Deliberately absent: any state asserting that laundering occurred. This system
# can say a pattern is present and that a person looked at it. It cannot say a
# crime happened, and a state named for that conclusion would invite the claim
# to be made by clicking.
FORBIDDEN_STATES = (
    "confirmed_money_laundering",
    "confirmed_fraud",
    "laundering",
    "guilty",
    "sar_filed",
    "reported_to_regulator",
    "account_frozen",
    "blacklisted",
)


@dataclass(frozen=True)
class AmlCase:
    case_key: str
    subject_account: str
    subject_entity_id: str
    subject_name: str
    alerts: tuple[AmlAlert, ...]
    window_start: datetime
    window_end: datetime
    priority_score: float
    priority_band: str
    contributions: tuple[Contribution, ...]
    duplicates_absorbed: int
    merge_rationale: str
    state: str = "new"
    queue_position: int = 0
    within_capacity: bool = False
    sla_due_at: datetime | None = None
    typology_keys: tuple[str, ...] = field(default_factory=tuple)
    # The exact sum of this case's distinct transfers. Summing the alerts would
    # double-count every transfer two typologies both fired on, which is most of
    # them on a case worth opening.
    total_usd_minor: int = 0

    @property
    def transfer_ids(self) -> tuple[str, ...]:
        out: list[str] = []
        for alert in self.alerts:
            for transfer_id in alert.transfer_ids:
                if transfer_id not in out:
                    out.append(transfer_id)
        return tuple(out)

    @property
    def max_severity(self) -> str:
        return max(
            (alert.severity for alert in self.alerts),
            key=lambda item: SEVERITY_ORDER.get(item, 0),
            default="low",
        )

    def as_row(self) -> dict[str, object]:
        return {
            "case_key": self.case_key,
            "subject_account": self.subject_account,
            "subject_entity_id": self.subject_entity_id,
            "subject_name": self.subject_name,
            "state": self.state,
            "priority_score": round(self.priority_score, 4),
            "priority_band": self.priority_band,
            "queue_position": self.queue_position,
            "within_capacity": self.within_capacity,
            "sla_due_at": self.sla_due_at.isoformat() if self.sla_due_at else None,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "alert_count": len(self.alerts),
            "duplicates_absorbed": self.duplicates_absorbed,
            "typologies": [BY_ID[alert.typology_id].title for alert in self.alerts],
            "typology_keys": list(self.typology_keys),
            "max_severity": self.max_severity,
            "transfer_count": len(self.transfer_ids),
            "total_usd_minor": self.total_usd_minor,
            "merge_rationale": self.merge_rationale,
            "contributions": [item.as_row() for item in self.contributions],
            "alerts": [alert.as_row() for alert in self.alerts],
        }


def deduplicate(alerts: tuple[AmlAlert, ...]) -> tuple[tuple[AmlAlert, ...], int]:
    """Collapse repeats of one finding, keeping the widest observation.

    The survivor is the alert covering the most transfers rather than the first
    or the largest: an investigator wants the fullest version of the pattern,
    and the count of what it absorbed is kept so nothing is silently discarded.
    """
    groups: dict[tuple[str, str], list[AmlAlert]] = defaultdict(list)
    for alert in alerts:
        groups[(alert.typology_id, alert.subject_account)].append(alert)

    kept: list[AmlAlert] = []
    removed = 0
    for members in groups.values():
        ordered = sorted(members, key=lambda item: item.window_start)
        cluster: list[AmlAlert] = []
        clusters: list[list[AmlAlert]] = []
        for alert in ordered:
            if cluster and (alert.window_start - cluster[0].window_start) > DEDUP_WINDOW:
                clusters.append(cluster)
                cluster = []
            cluster.append(alert)
        if cluster:
            clusters.append(cluster)

        for group in clusters:
            keeper = max(group, key=lambda item: (item.transfer_count, item.alert_id))
            absorbed = len(group) - 1
            removed += absorbed
            if absorbed:
                keeper = replace(
                    keeper,
                    features={**keeper.features, "duplicate_observations_absorbed": absorbed},
                )
            kept.append(keeper)

    return tuple(sorted(kept, key=lambda item: (item.typology_id, item.subject_account))), removed


def _case_key(subject_account: str, window_start: datetime) -> str:
    digest = hashlib.sha256(f"{subject_account}:{window_start:%Y-%m-%d}".encode()).hexdigest()
    return f"AMLC_{digest[:10].upper()}"


def _merge_rationale(subject_account: str, members: list[AmlAlert]) -> str:
    keys = sorted({BY_ID[alert.typology_id].key for alert in members})
    if len(keys) == 1:
        return (
            f"One typology ({keys[0]}) on {subject_account}, observed across "
            f"{len(members)} alert(s) inside one 30-day window."
        )
    return (
        f"{len(keys)} independent typologies ({', '.join(keys)}) fired on {subject_account} "
        "inside one 30-day window, so they are one story about this account rather than "
        f"{len(keys)} queues to work."
    )


def build_cases(
    alerts: tuple[AmlAlert, ...],
    context: MonitoringContext,
    *,
    now: datetime,
    capacity: int,
) -> tuple[AmlCase, ...]:
    """Group deduplicated alerts into cases, score them, and order the queue."""
    by_subject: dict[str, list[AmlAlert]] = defaultdict(list)
    for alert in alerts:
        by_subject[alert.subject_account].append(alert)

    cases: list[AmlCase] = []
    for subject_account, subject_alerts in by_subject.items():
        ordered = sorted(subject_alerts, key=lambda item: item.window_start)
        window: list[AmlAlert] = []
        windows: list[list[AmlAlert]] = []
        for alert in ordered:
            if window and (alert.window_start - window[0].window_start) > CASE_WINDOW:
                windows.append(window)
                window = []
            window.append(alert)
        if window:
            windows.append(window)

        for members in windows:
            cases.append(_build_case(subject_account, members, context, now=now))

    ranked = sorted(cases, key=lambda item: (-item.priority_score, item.case_key))
    return tuple(
        replace(
            case,
            queue_position=position + 1,
            within_capacity=position < capacity,
            state="queued" if position < capacity else "new",
        )
        for position, case in enumerate(ranked)
    )


def _build_case(
    subject_account: str,
    members: list[AmlAlert],
    context: MonitoringContext,
    *,
    now: datetime,
) -> AmlCase:
    entity = context.entity_of(subject_account)
    window_start = min(alert.window_start for alert in members)
    window_end = max(alert.window_end for alert in members)
    span_hours = max(1.0, (window_end - window_start).total_seconds() / 3600)

    transfer_ids: list[str] = []
    for alert in members:
        for transfer_id in alert.transfer_ids:
            if transfer_id not in transfer_ids:
                transfer_ids.append(transfer_id)
    by_id = {transfer.transfer_id: transfer for transfer in context.transfers}
    transfers = [by_id[item] for item in transfer_ids if item in by_id]

    counterparties = {
        item.beneficiary_account if item.payer_account == subject_account else item.payer_account
        for item in transfers
    }
    countries = {item.origin_country for item in transfers} | {
        item.destination_country for item in transfers
    }
    missing = any(
        item.beneficiary_information_status != "complete" or not item.declared_purpose.strip()
        for item in transfers
    )
    total_usd_minor = sum(item.amount_usd_minor for item in transfers)
    typology_keys = tuple(sorted({BY_ID[alert.typology_id].key for alert in members}))

    total, contributions = score(
        severities=tuple(alert.severity for alert in members),
        typology_keys=typology_keys,
        total_usd_minor=total_usd_minor,
        span_hours=span_hours,
        transfer_count=len(transfers),
        counterparties=len(counterparties),
        countries=len(countries),
        missing_information=missing,
        entity_risk_rating=entity.risk_rating if entity else "standard",
        entity_kyb_status=entity.kyb_status if entity else "missing",
        oldest_alert_at=window_start,
        now=now,
    )
    band = band_for(total)
    sla_hours = {"critical": 4, "high": 8, "medium": 24, "low": 72}[band]

    return AmlCase(
        total_usd_minor=total_usd_minor,
        case_key=_case_key(subject_account, window_start),
        subject_account=subject_account,
        subject_entity_id=entity.entity_id if entity else "",
        subject_name=entity.display_name if entity else subject_account,
        alerts=tuple(members),
        window_start=window_start,
        window_end=window_end,
        priority_score=total,
        priority_band=band,
        contributions=contributions,
        duplicates_absorbed=sum(
            int(alert.features.get("duplicate_observations_absorbed", 0)) for alert in members
        ),
        merge_rationale=_merge_rationale(subject_account, members),
        sla_due_at=now + timedelta(hours=sla_hours),
        typology_keys=typology_keys,
    )


@dataclass(frozen=True)
class QueueResult:
    """What a day's monitoring run produced, including what it could not reach."""

    raw_alerts: tuple[AmlAlert, ...]
    deduplicated: tuple[AmlAlert, ...]
    duplicates_removed: int
    cases: tuple[AmlCase, ...]
    capacity: int
    run_at: datetime

    @property
    def within_capacity(self) -> tuple[AmlCase, ...]:
        return tuple(case for case in self.cases if case.within_capacity)

    @property
    def backlog(self) -> tuple[AmlCase, ...]:
        """Cases below the capacity line. **Not cleared — not looked at.**"""
        return tuple(case for case in self.cases if not case.within_capacity)

    def as_row(self) -> dict[str, object]:
        return {
            "run_at": self.run_at.isoformat(),
            "raw_alerts": len(self.raw_alerts),
            "deduplicated_alerts": len(self.deduplicated),
            "duplicates_removed": self.duplicates_removed,
            "cases": len(self.cases),
            "capacity": self.capacity,
            "within_capacity": len(self.within_capacity),
            "backlog": len(self.backlog),
            "aggregation_version": AGGREGATION_VERSION,
        }


def run_queue(
    context: MonitoringContext, alerts: tuple[AmlAlert, ...], *, capacity: int, now: datetime
) -> QueueResult:
    deduplicated, removed = deduplicate(alerts)
    cases = build_cases(deduplicated, context, now=now, capacity=capacity)
    return QueueResult(
        raw_alerts=alerts,
        deduplicated=deduplicated,
        duplicates_removed=removed,
        cases=cases,
        capacity=capacity,
        run_at=now,
    )
