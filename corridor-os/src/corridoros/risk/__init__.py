"""Risk & Compliance — CrossBorder AML RiskOps, reading the platform's events.

Two layers, both deterministic:

    rules.py       twenty-one rules over one payment, adapted from RiskOps'
                   twenty acquiring rules
    typologies.py  the six AML typologies, ported unchanged in threshold and
                   severity, over the monitored transfer feed

Neither involves a model. `aggregate.py` turns alerts into cases, `priority.py`
orders them with every factor visible, and `evaluate.py` measures the result on
seeded synthetic worlds.
"""

from .aggregate import AGGREGATION_VERSION, AmlCase, QueueResult, deduplicate, run_queue
from .assess import Assessor
from .cases import CaseBook, priority_for
from .detect import DETECTORS, AmlAlert, run_all
from .evaluate import EVAL_VERSION, evaluate_seed
from .evaluate import evaluate as evaluate_aml
from .monitoring import MonitoredEntity, MonitoringContext, Transfer
from .priority import PRIORITY_VERSION, WEIGHTS, band_for
from .rules import RULES, RULES_VERSION, PaymentContext, band_of, evaluate, score_of
from .typologies import TYPOLOGIES, TYPOLOGY_VERSION

__all__ = [
    "AGGREGATION_VERSION",
    "AmlAlert",
    "AmlCase",
    "Assessor",
    "CaseBook",
    "DETECTORS",
    "EVAL_VERSION",
    "MonitoredEntity",
    "MonitoringContext",
    "PRIORITY_VERSION",
    "PaymentContext",
    "QueueResult",
    "RULES",
    "RULES_VERSION",
    "TYPOLOGIES",
    "TYPOLOGY_VERSION",
    "Transfer",
    "WEIGHTS",
    "band_for",
    "band_of",
    "deduplicate",
    "evaluate",
    "evaluate_aml",
    "evaluate_seed",
    "priority_for",
    "run_all",
    "run_queue",
    "score_of",
]
