"""The six typology detectors. Deterministic, no model.

Ported from `crossborder-riskops/src/riskops/aml/detect.py`, thresholds and
matching conditions intact, rewritten against `monitoring.Transfer` instead of
a pandas frame.

Every alert is reproducible from the feed alone. That is not a stylistic
preference: an alert a person will act on has to be explainable to the person it
is about, and a rule with a printed threshold can be argued with in a way a
learned score cannot.

Each detector returns alerts keyed on a **subject account**, because that is
what an investigator opens. A transfer can support several alerts, and an alert
always names the transfers it rests on, so evidence is traceable in both
directions.

Alert identifiers are derived from what the alert is *about* rather than from a
counter, so two runs over the same data produce the same identifiers and a case
opened yesterday still resolves its evidence today. SHA-256 rather than `hash()`:
Python randomises string hashing per process, which would have made the
identifiers differ between two runs over identical data.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from datetime import time as dt_time

from . import typologies as typo
from .monitoring import MonitoringContext, Transfer, usd
from .typologies import (
    CIRCULAR_FLOW,
    FUNNEL_ACCOUNT,
    MISSING_INFORMATION,
    PROFILE_MISMATCH,
    RAPID_MOVEMENT,
    STRUCTURING,
    TYPOLOGY_VERSION,
)


@dataclass(frozen=True)
class AmlAlert:
    alert_id: str
    typology_id: str
    typology_version: str
    severity: str
    subject_account: str
    subject_entity_id: str
    triggered_at: datetime
    window_start: datetime
    window_end: datetime
    transfer_ids: tuple[str, ...]
    entity_ids: tuple[str, ...]
    total_usd_minor: int
    explanation: str
    counter_evidence: tuple[str, ...]
    features: dict[str, object] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    dedup_key: str = ""

    @property
    def transfer_count(self) -> int:
        return len(self.transfer_ids)

    def as_row(self) -> dict[str, object]:
        return {
            "alert_id": self.alert_id,
            "typology_id": self.typology_id,
            "typology_version": self.typology_version,
            "severity": self.severity,
            "subject_account": self.subject_account,
            "subject_entity_id": self.subject_entity_id,
            "triggered_at": self.triggered_at.isoformat(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "transfer_ids": list(self.transfer_ids),
            "transfer_count": self.transfer_count,
            "entity_ids": list(self.entity_ids),
            "total_usd_minor": self.total_usd_minor,
            "explanation": self.explanation,
            "counter_evidence": list(self.counter_evidence),
            "features": dict(self.features),
            "thresholds": dict(self.thresholds),
            "dedup_key": self.dedup_key,
        }


def _daily_windows(
    rows: list[Transfer], window: timedelta
) -> list[tuple[datetime, list[Transfer]]]:
    """Every window a daily batch job would evaluate, one per day new data arrived.

    This is what makes the deduplication figures mean something. A detector that
    reported only its single best window per subject would produce no duplicates
    at all, and the dedup step would be measuring nothing — but a real monitoring
    system re-evaluates its window every day, so a pattern that stays inside the
    lookback re-fires every day until it ages out. That flood is the actual
    problem alert deduplication exists to solve, so it is reproduced here rather
    than avoided.
    """
    if not rows:
        return []
    ordered = sorted(rows, key=lambda item: item.timestamp)
    out: list[tuple[datetime, list[Transfer]]] = []
    seen: set[tuple[str, ...]] = set()
    for date in sorted({item.timestamp.date() for item in ordered}):
        end = datetime.combine(date, dt_time.max, tzinfo=ordered[0].timestamp.tzinfo)
        start = end - window
        span = [item for item in ordered if start <= item.timestamp <= end]
        if not span:
            continue
        key = tuple(item.transfer_id for item in span)
        if key in seen:
            continue
        seen.add(key)
        out.append((end, span))
    return out


def _alert(
    context: MonitoringContext,
    typology: typo.Typology,
    subject_account: str,
    transfers: list[Transfer],
    features: dict[str, object],
    *,
    window: tuple[datetime, datetime],
    entity_ids: list[str],
    dedup_key: str,
) -> AmlAlert:
    entity = context.entity_of(subject_account)
    digest = hashlib.sha256(dedup_key.encode()).hexdigest()[:10].upper()
    return AmlAlert(
        alert_id=f"ALT_{typology.key.upper()[:6]}_{digest}",
        typology_id=typology.typology_id,
        typology_version=TYPOLOGY_VERSION,
        severity=typology.severity,
        subject_account=subject_account,
        subject_entity_id=entity.entity_id if entity else "",
        triggered_at=context.now,
        window_start=window[0],
        window_end=window[1],
        transfer_ids=tuple(item.transfer_id for item in transfers),
        entity_ids=tuple(sorted(set(entity_ids))),
        total_usd_minor=sum(item.amount_usd_minor for item in transfers),
        explanation=typo.render_explanation(typology, features),
        counter_evidence=typology.counter_evidence_hints,
        features=features,
        thresholds=dict(typology.thresholds),
        dedup_key=dedup_key,
    )


# --------------------------------------------------------------------------- #
# T01 Structuring
# --------------------------------------------------------------------------- #


def detect_structuring(context: MonitoringContext) -> list[AmlAlert]:
    threshold = STRUCTURING.thresholds["threshold_usd"]
    band_low = STRUCTURING.thresholds["band_low_usd"]
    window = timedelta(hours=STRUCTURING.thresholds["window_hours"])
    minimum = int(STRUCTURING.thresholds["min_transfers"])
    alerts: list[AmlAlert] = []

    for account_id, rows in context.by_payer.items():
        # Only transfers inside the band matter; a mixed history with three
        # banded transfers among two hundred ordinary ones is not the pattern,
        # so the window is walked over the banded subset.
        banded = [
            item for item in rows if band_low * 100 <= item.amount_usd_minor < threshold * 100
        ]
        if len(banded) < minimum:
            continue
        for anchor, span in _daily_windows(banded, window):
            if len(span) < minimum:
                continue
            beneficiaries = {item.beneficiary_account for item in span}
            total = sum(item.amount_usd_minor for item in span)
            elapsed = (span[-1].timestamp - span[0].timestamp).total_seconds() / 3600
            features = {
                "transfer_count": len(span),
                "total_usd": usd(total),
                "window_hours": f"{elapsed:.0f}",
                "under_threshold_count": len(span),
                "beneficiary_count": len(beneficiaries),
                "threshold": f"{threshold:,.0f}",
                "band_low": f"{band_low:,.0f}",
                "largest_usd": usd(max(item.amount_usd_minor for item in span)),
            }
            alerts.append(
                _alert(
                    context,
                    STRUCTURING,
                    account_id,
                    span,
                    features,
                    window=(span[0].timestamp, span[-1].timestamp),
                    entity_ids=[account_id, *beneficiaries],
                    dedup_key=f"structuring:{account_id}:{anchor:%Y-%m-%d}",
                )
            )
    return alerts


# --------------------------------------------------------------------------- #
# T02 Rapid movement
# --------------------------------------------------------------------------- #


def detect_rapid_movement(context: MonitoringContext) -> list[AmlAlert]:
    max_hold = timedelta(minutes=RAPID_MOVEMENT.thresholds["max_hold_minutes"])
    min_pct = RAPID_MOVEMENT.thresholds["min_passthrough_pct"]
    min_amount = RAPID_MOVEMENT.thresholds["min_amount_usd"] * 100
    alerts: list[AmlAlert] = []

    for account_id, inbound_rows in context.by_beneficiary.items():
        outbound_rows = context.by_payer.get(account_id, [])
        if not outbound_rows:
            continue
        for inbound in inbound_rows:
            if inbound.amount_usd_minor < min_amount:
                continue
            following = [
                item
                for item in outbound_rows
                if timedelta(0) < item.timestamp - inbound.timestamp <= max_hold
            ]
            if not following:
                continue
            # The best single onward leg, not the sum: a sum over a busy account
            # reaches 80% by accident, and the pattern being described is one
            # amount arriving and substantially the same amount leaving.
            outbound = max(following, key=lambda item: item.amount_usd_minor)
            pct = (
                outbound.amount_usd_minor / inbound.amount_usd_minor * 100
                if inbound.amount_usd_minor
                else 0.0
            )
            if pct < min_pct or pct > 130:
                continue
            hold = (outbound.timestamp - inbound.timestamp).total_seconds() / 60
            features = {
                "inbound_usd": usd(inbound.amount_usd_minor),
                "outbound_usd": usd(outbound.amount_usd_minor),
                "hold_minutes": f"{hold:.0f}",
                "passthrough_pct": f"{pct:.0f}",
                "retained_usd": usd(max(0, inbound.amount_usd_minor - outbound.amount_usd_minor)),
                "destination_country": outbound.destination_country,
                "inbound_transfer_id": inbound.transfer_id,
                "outbound_transfer_id": outbound.transfer_id,
            }
            alert = _alert(
                context,
                RAPID_MOVEMENT,
                account_id,
                [inbound, outbound],
                features,
                window=(inbound.timestamp, outbound.timestamp),
                entity_ids=[account_id, inbound.payer_account, outbound.beneficiary_account],
                dedup_key=f"rapid:{account_id}:{inbound.transfer_id}",
            )
            if pct > 100:
                # Above 100% the account paid out more than this transfer brought
                # in, so it was topped up from somewhere else. Still worth a look,
                # but calling it "forwarded" would misdescribe it, and an
                # investigator reading "retained 0 USD" would draw the wrong
                # picture of where the balance came from.
                alert = replace(
                    alert,
                    explanation=alert.explanation
                    + " More left than this transfer brought in, so the balance was funded "
                    "from elsewhere; this is not a straight pass-through.",
                )
            alerts.append(alert)
    return alerts


# --------------------------------------------------------------------------- #
# T03 Funnel account
# --------------------------------------------------------------------------- #


def _unrelated(context: MonitoringContext, senders: list[Transfer]) -> int:
    """Senders sharing no entity and no beneficial owner with another sender.

    "Unrelated" is the load-bearing word in this typology: many-to-one is
    ordinary, and it is the *absence of any connection between the senders* that
    makes the shape worth a look. Counting it explicitly also gives the
    investigator something falsifiable — they can go and find the connection.
    """
    seen_entities: set[str] = set()
    seen_owners: set[str] = set()
    unrelated = 0
    for transfer in senders:
        entity_id = transfer.payer_entity_id
        owners = context.owners_of(transfer.payer_account)
        if entity_id in seen_entities or (owners and owners & seen_owners):
            continue
        unrelated += 1
        seen_entities.add(entity_id)
        seen_owners |= owners
    return unrelated


def detect_funnel(context: MonitoringContext) -> list[AmlAlert]:
    min_senders = int(FUNNEL_ACCOUNT.thresholds["min_senders"])
    window = timedelta(days=FUNNEL_ACCOUNT.thresholds["window_days"])
    min_total = FUNNEL_ACCOUNT.thresholds["min_total_usd"] * 100
    alerts: list[AmlAlert] = []

    for account_id, rows in context.by_beneficiary.items():
        if len({item.payer_account for item in rows}) < min_senders:
            continue
        for anchor, span in _daily_windows(rows, window):
            senders = {item.payer_account for item in span}
            total = sum(item.amount_usd_minor for item in span)
            if len(senders) < min_senders or total < min_total:
                continue
            countries = {item.origin_country for item in span}
            features = {
                "sender_count": len(senders),
                "sender_country_count": len(countries),
                "total_usd": usd(total),
                "window_days": f"{(span[-1].timestamp - span[0].timestamp).days}",
                "unrelated_sender_count": _unrelated(context, span),
                "transfer_count": len(span),
            }
            alerts.append(
                _alert(
                    context,
                    FUNNEL_ACCOUNT,
                    account_id,
                    span,
                    features,
                    window=(span[0].timestamp, span[-1].timestamp),
                    entity_ids=[account_id, *senders],
                    dedup_key=f"funnel:{account_id}:{anchor:%Y-%m-%d}",
                )
            )
    return alerts


# --------------------------------------------------------------------------- #
# T04 Circular flow
# --------------------------------------------------------------------------- #


def detect_circular(context: MonitoringContext) -> list[AmlAlert]:
    """Walk forward from each transfer looking for a path back to its origin.

    Bounded depth-first search, not a graph library: the maximum hop count is
    five, so the search space is small, and keeping it explicit means the
    evidence can name every leg it walked. A cycle found here is a statement
    about these specific transfers, not about a component of a graph.
    """
    min_hops = int(CIRCULAR_FLOW.thresholds["min_hops"])
    max_hops = int(CIRCULAR_FLOW.thresholds["max_hops"])
    min_return = CIRCULAR_FLOW.thresholds["min_return_pct"]
    max_elapsed = timedelta(hours=CIRCULAR_FLOW.thresholds["max_elapsed_hours"])
    alerts: list[AmlAlert] = []
    seen_cycles: set[frozenset[str]] = set()

    for origin, first_legs in context.by_payer.items():
        for first in first_legs:
            if first.amount_usd_minor < 5_000 * 100:
                continue
            stack: list[tuple[Transfer, list[Transfer]]] = [(first, [first])]
            while stack:
                current, path = stack.pop()
                if len(path) > max_hops:
                    continue
                node = current.beneficiary_account
                elapsed = current.timestamp - first.timestamp
                if node == origin and len(path) >= min_hops:
                    pct = (
                        current.amount_usd_minor / first.amount_usd_minor * 100
                        if first.amount_usd_minor
                        else 0.0
                    )
                    if pct < min_return or elapsed > max_elapsed:
                        continue
                    key = frozenset(item.transfer_id for item in path)
                    if key in seen_cycles:
                        continue
                    seen_cycles.add(key)
                    countries = [item.origin_country for item in path]
                    countries.append(path[-1].destination_country)
                    features = {
                        "hop_count": len(path),
                        "total_usd": usd(sum(item.amount_usd_minor for item in path)),
                        "country_path": " → ".join(countries),
                        "return_target": origin,
                        "return_pct": f"{pct:.0f}",
                        "elapsed_hours": f"{elapsed.total_seconds() / 3600:.0f}",
                        "cycle_account_ids": ", ".join(
                            [origin, *[item.beneficiary_account for item in path[:-1]]]
                        ),
                    }
                    alerts.append(
                        _alert(
                            context,
                            CIRCULAR_FLOW,
                            origin,
                            path,
                            features,
                            window=(first.timestamp, current.timestamp),
                            entity_ids=[origin, *[item.beneficiary_account for item in path]],
                            dedup_key=f"circular:{origin}:{sorted(key)[0]}",
                        )
                    )
                    continue
                if elapsed > max_elapsed or len(path) == max_hops:
                    continue
                for nxt in context.by_payer.get(node, []):
                    gap = nxt.timestamp - current.timestamp
                    if timedelta(0) < gap <= max_elapsed:
                        stack.append((nxt, [*path, nxt]))
    return alerts


# --------------------------------------------------------------------------- #
# T05 Profile / purpose mismatch
# --------------------------------------------------------------------------- #

# What each declared industry ordinarily pays for. A purpose outside this set is
# not wrong — it is a question for the reviewer, and it is counted, not judged.
ON_PROFILE_PURPOSES: dict[str, tuple[str, ...]] = {
    "wholesale_trade": ("supplier_invoice", "logistics", "customs_duty", "salary", "rent"),
    "electronics_manufacturing": ("supplier_invoice", "components", "logistics", "salary", "rent"),
    "software_services": ("salary", "cloud_services", "contractor_fee", "rent", "marketing"),
    "logistics": ("fuel", "salary", "supplier_invoice", "customs_duty", "rent"),
    "consumer_goods": ("supplier_invoice", "marketing", "logistics", "salary", "rent"),
}


def detect_profile_mismatch(context: MonitoringContext) -> list[AmlAlert]:
    min_ratio = PROFILE_MISMATCH.thresholds["min_ratio"]
    window = timedelta(days=PROFILE_MISMATCH.thresholds["window_days"])
    min_actual = PROFILE_MISMATCH.thresholds["min_actual_usd"] * 100
    alerts: list[AmlAlert] = []

    for account_id, rows in context.by_payer.items():
        entity = context.entity_of(account_id)
        if entity is None or entity.expected_monthly_usd <= 0:
            continue
        on_profile = set(ON_PROFILE_PURPOSES.get(entity.industry, ()))

        for anchor, span in _daily_windows(rows, window):
            total = sum(item.amount_usd_minor for item in span)
            if total < min_actual:
                continue
            ratio = total / (entity.expected_monthly_usd * 100)
            if ratio < min_ratio:
                continue
            off = [
                item.declared_purpose
                for item in span
                if item.declared_purpose and item.declared_purpose not in on_profile
            ]
            features = {
                "actual_usd": usd(total),
                "expected_usd": f"{entity.expected_monthly_usd:,.0f}",
                "ratio": f"{ratio:.1f}",
                "declared_business": entity.industry or entity.entity_type,
                "observed_purposes": ", ".join(sorted(set(off))[:4]) or "none off-profile",
                "mismatch_count": len(off),
                "transfer_count": len(span),
                "window_days": int(PROFILE_MISMATCH.thresholds["window_days"]),
            }
            alerts.append(
                _alert(
                    context,
                    PROFILE_MISMATCH,
                    account_id,
                    span,
                    features,
                    window=(span[0].timestamp, span[-1].timestamp),
                    entity_ids=[account_id, entity.entity_id],
                    dedup_key=f"profile:{account_id}:{anchor:%Y-%m-%d}",
                )
            )
    return alerts


# --------------------------------------------------------------------------- #
# T06 Missing information
# --------------------------------------------------------------------------- #


def detect_missing_information(context: MonitoringContext) -> list[AmlAlert]:
    min_affected = int(MISSING_INFORMATION.thresholds["min_affected"])
    min_usd = MISSING_INFORMATION.thresholds["min_affected_usd"] * 100
    alerts: list[AmlAlert] = []

    for account_id, rows in context.by_payer.items():
        affected: list[Transfer] = []
        missing_fields: set[str] = set()
        for transfer in rows:
            gaps: set[str] = set()
            if transfer.beneficiary_information_status in ("missing", "partial"):
                gaps.add("beneficiary_information")
            if not transfer.declared_purpose.strip():
                gaps.add("declared_purpose")
            if gaps:
                affected.append(transfer)
                missing_fields |= gaps
        if len(affected) < min_affected:
            continue
        total = sum(item.amount_usd_minor for item in affected)
        if total < min_usd:
            continue

        entity = context.entity_of(account_id)
        ownership = context.ownership_status(account_id)
        if ownership in ("unverified", "missing"):
            missing_fields.add("beneficial_ownership")
        statuses = {item.beneficiary_information_status for item in affected}
        features = {
            "affected_count": len(affected),
            "transfer_count": len(rows),
            "affected_usd": usd(total),
            "missing_fields": ", ".join(sorted(missing_fields)),
            "beneficiary_status": ", ".join(sorted(statuses)),
            "ownership_status": ownership,
        }
        alerts.append(
            _alert(
                context,
                MISSING_INFORMATION,
                account_id,
                affected,
                features,
                window=(
                    min(item.timestamp for item in affected),
                    max(item.timestamp for item in affected),
                ),
                entity_ids=[account_id, entity.entity_id if entity else ""],
                dedup_key=f"missing:{account_id}",
            )
        )
    return alerts


DETECTORS = (
    detect_structuring,
    detect_rapid_movement,
    detect_funnel,
    detect_circular,
    detect_profile_mismatch,
    detect_missing_information,
)


def run_all(context: MonitoringContext) -> tuple[AmlAlert, ...]:
    """Every detector over the whole feed. Order is fixed, so output is stable."""
    alerts: list[AmlAlert] = []
    for detector in DETECTORS:
        alerts.extend(detector(context))
    return tuple(sorted(alerts, key=lambda item: (item.typology_id, item.subject_account, item.alert_id)))
