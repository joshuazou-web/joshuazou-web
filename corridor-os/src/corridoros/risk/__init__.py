"""Risk & Compliance — CrossBorder AML RiskOps, reading the platform's events.

Phase note: this package currently carries the payment-risk signals the
vertical slice needs. The twenty transaction-integrity rules and six AML
typologies from the source project are ported in phase P2; see
`docs/MIGRATION.md`.
"""

from .assess import Assessor
from .cases import CaseBook, priority_for
from .signals import RULES_VERSION, PaymentContext, band_of, evaluate, score_of

__all__ = [
    "Assessor",
    "CaseBook",
    "PaymentContext",
    "RULES_VERSION",
    "band_of",
    "evaluate",
    "priority_for",
    "score_of",
]
