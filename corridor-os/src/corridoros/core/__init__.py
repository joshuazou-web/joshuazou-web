"""The layer every other module depends on, and which depends on none of them."""

from .audit import AuditLog, ChainVerification, verify_entries
from .authority import AI_ALLOWED, CONSEQUENTIAL_ACTIONS, can, require, roles_for
from .domain import (
    ApprovalDecision,
    AuditEvent,
    Beneficiary,
    BusinessProfile,
    CollectionIntent,
    EvidenceItem,
    ExceptionCase,
    PaymentInstruction,
    ReviewCase,
    RiskAssessment,
    RiskSignal,
    SettlementRecord,
)
from .errors import (
    AuthorityError,
    CorridorError,
    EventError,
    EvidenceError,
    FxError,
    IdError,
    LedgerError,
    LifecycleError,
)
from .events import EVENT_TYPES, Event, EventBus
from .ids import IdFactory, make_id, validate
from .money import Money, convert

__all__ = [
    "AI_ALLOWED",
    "CONSEQUENTIAL_ACTIONS",
    "ApprovalDecision",
    "AuditEvent",
    "AuditLog",
    "AuthorityError",
    "Beneficiary",
    "BusinessProfile",
    "ChainVerification",
    "CollectionIntent",
    "CorridorError",
    "EVENT_TYPES",
    "Event",
    "EventBus",
    "EventError",
    "EvidenceError",
    "EvidenceItem",
    "ExceptionCase",
    "FxError",
    "IdError",
    "IdFactory",
    "LedgerError",
    "LifecycleError",
    "Money",
    "PaymentInstruction",
    "ReviewCase",
    "RiskAssessment",
    "RiskSignal",
    "SettlementRecord",
    "can",
    "convert",
    "make_id",
    "require",
    "roles_for",
    "validate",
    "verify_entries",
]
