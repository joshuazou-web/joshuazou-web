"""The six typologies, as one shared vocabulary.

Ported from `crossborder-riskops/src/riskops/aml/typology.py`. The thresholds,
severities and counter-evidence hints are the originals; what changed is the
subject. In RiskOps a subject was a wallet or a customer account; here it is an
account belonging to a business in the corridor, so the explanations talk about
suppliers, corridors and entities rather than wallets.

The sentence the whole module is arranged around is unchanged:

    An unusual transaction is not a laundered transaction.

Nothing here concludes that a business is laundering money. A typology match
says a pattern is present that is worth a person's time, and names the transfers
and entities to look at. What it means is for an investigator to decide, and
nothing in the disposition vocabulary asserts a crime.

`counter_evidence_hints` is the list of innocent explanations a reviewer should
actively look for. The workbench renders them *beside* the evidence rather than
below it, because a queue under time pressure reads top-down and stops early.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Bumped when a threshold, window or matching condition changes — never for a
# wording change. Alerts carry the version that produced them, so a case opened
# last month can still be read against the rules that opened it.
TYPOLOGY_VERSION = "1.0.0"

SEVERITY_ORDER: dict[str, int] = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class Typology:
    typology_id: str
    key: str
    title: str
    severity: str
    question: str
    explanation_template: str
    evidence_fields: tuple[str, ...]
    counter_evidence_hints: tuple[str, ...]
    thresholds: dict[str, float] = field(default_factory=dict)

    @property
    def severity_rank(self) -> int:
        return SEVERITY_ORDER[self.severity]


STRUCTURING = Typology(
    typology_id="AML_T01_STRUCTURING",
    key="structuring",
    title="Structured transfers below a reporting threshold",
    severity="high",
    question="Were several transfers sized to stay under a threshold rather than sized by need?",
    explanation_template=(
        "{transfer_count} transfers totalling {total_usd} USD left this account in "
        "{window_hours} hours, {under_threshold_count} of them between {band_low} and "
        "{threshold} USD, to {beneficiary_count} beneficiary account(s). Individually each "
        "sits below the {threshold} USD reporting threshold."
    ),
    evidence_fields=(
        "transfer_count",
        "total_usd",
        "window_hours",
        "under_threshold_count",
        "beneficiary_count",
        "threshold",
        "band_low",
        "largest_usd",
    ),
    counter_evidence_hints=(
        "A payroll, rent or instalment schedule can produce similar amounts on a regular cadence.",
        "Per-transfer limits set by the business's own bank or the channel can cap amounts "
        "without any intent to avoid a threshold.",
        "Check whether the same pattern is present in the months before the alert window; a "
        "long-standing habit is weaker evidence than a new one.",
    ),
    thresholds={
        "threshold_usd": 10_000.0,
        "band_low_usd": 7_000.0,
        "window_hours": 72.0,
        "min_transfers": 3.0,
    },
)

RAPID_MOVEMENT = Typology(
    typology_id="AML_T02_RAPID_MOVEMENT",
    key="rapid_movement",
    title="Funds forwarded cross-border shortly after arriving",
    severity="high",
    question="Did this account hold the money, or only pass it on?",
    explanation_template=(
        "{outbound_usd} USD left this account within {hold_minutes} minutes of "
        "{inbound_usd} USD arriving, forwarding {passthrough_pct}% of what came in to "
        "{destination_country}. The account retained {retained_usd} USD."
    ),
    evidence_fields=(
        "inbound_usd",
        "outbound_usd",
        "hold_minutes",
        "passthrough_pct",
        "retained_usd",
        "destination_country",
        "inbound_transfer_id",
        "outbound_transfer_id",
    ),
    counter_evidence_hints=(
        "Treasury sweeps, supplier settlement and payroll runs are all fast by design.",
        "A named, consistent counterparty on both legs is a weaker signal than a new one.",
        "A corridor entity funded by its parent and paying suppliers the same week is the "
        "ordinary shape of this business, not a pass-through.",
    ),
    thresholds={
        "max_hold_minutes": 1440.0,
        "min_passthrough_pct": 80.0,
        "min_amount_usd": 5_000.0,
    },
)

FUNNEL_ACCOUNT = Typology(
    typology_id="AML_T03_FUNNEL_ACCOUNT",
    key="funnel",
    title="Many unrelated senders paying one account",
    severity="high",
    question="Why are these particular senders all paying the same account?",
    explanation_template=(
        "{sender_count} sending accounts across {sender_country_count} countries paid "
        "{total_usd} USD into this account over {window_days} days in {transfer_count} "
        "transfers. {unrelated_sender_count} of the senders share no entity, owner or "
        "device with any other."
    ),
    evidence_fields=(
        "sender_count",
        "sender_country_count",
        "total_usd",
        "window_days",
        "unrelated_sender_count",
        "transfer_count",
    ),
    counter_evidence_hints=(
        "A marketplace, a collection agent or a group treasury account receives from many "
        "unrelated parties by design.",
        "Check whether the senders are this entity's own customers — many-to-one is the "
        "normal shape of a collection account.",
        "A rising sender count that tracks a product launch is growth, not a funnel.",
    ),
    thresholds={"min_senders": 8.0, "window_days": 14.0, "min_total_usd": 20_000.0},
)

CIRCULAR_FLOW = Typology(
    typology_id="AML_T04_CIRCULAR_FLOW",
    key="circular",
    title="Funds returning to their origin through intermediaries",
    severity="critical",
    question="Did this money travel, or only appear to?",
    explanation_template=(
        "{total_usd} USD moved through {hop_count} hops along {country_path} and "
        "{return_pct}% of it returned to {return_target} within {elapsed_hours} hours. "
        "Accounts on the path: {cycle_account_ids}."
    ),
    evidence_fields=(
        "hop_count",
        "total_usd",
        "country_path",
        "return_target",
        "return_pct",
        "elapsed_hours",
        "cycle_account_ids",
    ),
    counter_evidence_hints=(
        "Intra-group treasury movements legitimately return to the parent; check whether every "
        "account on the path belongs to the same group.",
        "A refund or a reversed payment returns money by design — check whether a leg carries a "
        "reversal reference.",
        "Trade finance and back-to-back invoicing can produce a genuine loop.",
    ),
    thresholds={
        "min_hops": 3.0,
        "max_hops": 5.0,
        "min_return_pct": 70.0,
        "max_elapsed_hours": 168.0,
    },
)

PROFILE_MISMATCH = Typology(
    typology_id="AML_T05_PROFILE_MISMATCH",
    key="profile_mismatch",
    title="Activity far above, or beside, what the entity declared",
    severity="medium",
    question="Does this account behave like what the business said it was for?",
    explanation_template=(
        "{actual_usd} USD moved in {window_days} days against a declared expectation of "
        "{expected_usd} USD a month — {ratio}× — across {transfer_count} transfers. "
        "Declared activity: {declared_business}. Observed purposes off that profile: "
        "{observed_purposes} ({mismatch_count} transfer(s))."
    ),
    evidence_fields=(
        "actual_usd",
        "expected_usd",
        "ratio",
        "declared_business",
        "observed_purposes",
        "mismatch_count",
        "transfer_count",
        "window_days",
    ),
    counter_evidence_hints=(
        "A seasonal peak or a single large contract can lift a month far above the declared "
        "average without changing what the business does.",
        "The declared expectation was given at onboarding and may simply be stale — check when "
        "the KYB evidence was last refreshed.",
        "An off-profile purpose code may be a coding error at the payer's end rather than a "
        "change in activity.",
    ),
    thresholds={"min_ratio": 4.0, "window_days": 30.0, "min_actual_usd": 15_000.0},
)

MISSING_INFORMATION = Typology(
    typology_id="AML_T06_MISSING_INFORMATION",
    key="missing_information",
    title="Transfers that cannot be judged because information is absent",
    severity="medium",
    question="Can we say who is on both ends of this money, and why it moved?",
    explanation_template=(
        "{affected_count} of {transfer_count} transfers from this account, totalling "
        "{affected_usd} USD, are missing {missing_fields}. Beneficiary information status: "
        "{beneficiary_status}. Beneficial ownership: {ownership_status}."
    ),
    evidence_fields=(
        "affected_count",
        "transfer_count",
        "affected_usd",
        "missing_fields",
        "beneficiary_status",
        "ownership_status",
    ),
    counter_evidence_hints=(
        "A field absent from the feed is not the same as a field the business refused to give — "
        "check whether the channel carries it at all.",
        "Ownership may be on file in the KYB pack and simply not linked to these transfers.",
        "This typology is a reason a case cannot be decided yet, not evidence of wrongdoing.",
    ),
    thresholds={"min_affected": 3.0, "min_affected_usd": 5_000.0},
)

TYPOLOGIES: tuple[Typology, ...] = (
    STRUCTURING,
    RAPID_MOVEMENT,
    FUNNEL_ACCOUNT,
    CIRCULAR_FLOW,
    PROFILE_MISMATCH,
    MISSING_INFORMATION,
)

BY_ID: dict[str, Typology] = {item.typology_id: item for item in TYPOLOGIES}
BY_KEY: dict[str, Typology] = {item.key: item for item in TYPOLOGIES}


def render_explanation(typology: Typology, features: dict[str, object]) -> str:
    """Fill the template, and say plainly when a value was not available.

    A `KeyError` here would mean an alert with no explanation, which is worse
    than an explanation with a gap in it: the investigator can see what is
    missing and the evaluation can count it.
    """
    filled = {field: features.get(field, "unknown") for field in typology.evidence_fields}
    try:
        return typology.explanation_template.format(**filled)
    except (KeyError, IndexError):  # pragma: no cover - template/feature mismatch
        return (
            f"{typology.title}: explanation could not be rendered from "
            f"{sorted(features)}; the alert still names its transfers."
        )
