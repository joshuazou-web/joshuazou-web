"""Payment Core — the corridor blueprint, implemented.

Everything in this package produces the events the rest of the platform reads.
It contains no risk scoring, no intervention thresholds and no language model;
those live in `risk`, `intervention` and `evidence` and learn about payments
only through `core.events`.
"""

from .beneficiaries import BeneficiaryRegistry
from .collection import CollectionRegistry
from .fx import FxDesk, FxQuote
from .kyb import REQUIRED_EVIDENCE_KINDS, KybRegistry
from .ledger import Ledger, Leg, account_id
from .payout import PayoutEngine
from .reconciliation import BankStatementLine, ReconciliationEngine, ReconciliationResult
from .settlement import SettlementBook

__all__ = [
    "REQUIRED_EVIDENCE_KINDS",
    "BankStatementLine",
    "BeneficiaryRegistry",
    "CollectionRegistry",
    "FxDesk",
    "FxQuote",
    "KybRegistry",
    "Ledger",
    "Leg",
    "PayoutEngine",
    "ReconciliationEngine",
    "ReconciliationResult",
    "SettlementBook",
    "account_id",
]
