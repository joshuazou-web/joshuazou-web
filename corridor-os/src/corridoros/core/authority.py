"""Who may do what.

Three of the four merged projects promised the same boundary — the model
explains, a person decides — and enforced it three different ways, at three
different strengths. RiskOps was the strict one: its audit log refused an
`ai_copilot` actor outright, so the promise was a property of the code rather
than a paragraph in a prompt. This module generalises that approach and makes
it the single place the platform answers the question.

Two design choices are doing the work:

**The matrix is data, and it is the only source of truth.** The API layer, the
payments engine and the audit log all call `require()`. There is no second
place where a permission is decided, so there is no second place to forget.

**The AI role's permissions are checked at import time.** `AI_ALLOWED` lists
the six things the copilot may do. `CONSEQUENTIAL_ACTIONS` lists what moves
money, clears a risk finding, or closes a case. The assertion at the bottom of
this file fails the build if those sets ever intersect. Someone widening the
copilot's remit in a later refactor does not get a passing test suite.

What this does *not* claim: it is an authorisation model inside one process,
not an identity system. It has no notion of authentication, tenancy, session
lifetime or key custody, and it has never protected anything real.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AuthorityError

# --- roles ----------------------------------------------------------------

SYSTEM = "system"
COMPLIANCE_OFFICER = "compliance_officer"
TREASURY_OPERATOR = "treasury_operator"
PAYMENT_APPROVER = "payment_approver"
FINANCE_OPERATOR = "finance_operator"
RISK_ANALYST = "risk_analyst"
AI_COPILOT = "ai_copilot"
VIEWER = "viewer"

ROLES: tuple[str, ...] = (
    SYSTEM,
    COMPLIANCE_OFFICER,
    TREASURY_OPERATOR,
    PAYMENT_APPROVER,
    FINANCE_OPERATOR,
    RISK_ANALYST,
    AI_COPILOT,
    VIEWER,
)

HUMAN_ROLES: tuple[str, ...] = (
    COMPLIANCE_OFFICER,
    TREASURY_OPERATOR,
    PAYMENT_APPROVER,
    FINANCE_OPERATOR,
    RISK_ANALYST,
)


@dataclass(frozen=True)
class ActionSpec:
    action: str
    summary: str
    consequential: bool


def _spec(action: str, summary: str, consequential: bool = False) -> tuple[str, ActionSpec]:
    return action, ActionSpec(action, summary, consequential)


ACTIONS: dict[str, ActionSpec] = dict(
    (
        # entity onboarding
        _spec("business.submit", "Submit a business for KYB review"),
        _spec("business.request_information", "Ask the business for missing evidence"),
        _spec("business.approve", "Approve a business for collection and payout", True),
        _spec("business.reject", "Reject a business", True),
        # counterparties
        _spec("beneficiary.create", "Register a supplier bank account"),
        _spec("beneficiary.change", "Change a supplier's bank account", True),
        _spec("beneficiary.verify", "Record an independent verification of a beneficiary"),
        # money
        _spec("collection.attribute", "Attribute incoming funds to a collection intent"),
        _spec("ledger.post", "Post a journal entry", True),
        _spec("ledger.reverse", "Reverse a posted journal entry", True),
        _spec("fx.quote", "Request an FX quote"),
        _spec("fx.execute", "Execute a conversion against a live quote", True),
        _spec("payment.create", "Create a payment instruction"),
        _spec("payment.approve", "Approve a payment instruction", True),
        _spec("payment.submit", "Submit an approved payment to the rail", True),
        _spec("payment.cancel", "Cancel a payment before submission", True),
        _spec("payment.verify", "Record completion of a required pre-payment verification"),
        # risk and compliance
        _spec("risk.assess", "Run deterministic risk rules over a payment"),
        _spec("case.open", "Open an investigation or review case"),
        _spec("case.assign", "Assign a case to an analyst"),
        _spec("case.close", "Close an investigation case", True),
        _spec("alert.clear", "Clear an AML alert without a case", True),
        # operations
        _spec("exception.open", "Open a reconciliation or operational exception"),
        _spec("exception.resolve", "Resolve an exception case", True),
        _spec("reconciliation.run", "Run a three-way reconciliation"),
        _spec("reconciliation.adjust", "Post a reconciliation adjustment", True),
        # what the copilot is for
        _spec("evidence.assemble", "Assemble an evidence packet from existing records"),
        _spec("evidence.summarise", "Write a case summary from an assembled packet"),
        _spec("evidence.identify_missing", "Name the documents a decision still lacks"),
        _spec("evidence.answer", "Answer a reviewer's question with citations"),
        _spec("evidence.draft_request", "Draft an information request for a human to send"),
        _spec("evidence.abstain", "Decline to answer because the evidence is insufficient"),
    )
)

CONSEQUENTIAL_ACTIONS: frozenset[str] = frozenset(
    action for action, spec in ACTIONS.items() if spec.consequential
)

# The six things the copilot may do. Anything absent from this set it cannot do,
# and everything in it produces text or a reference — never a state change.
AI_ALLOWED: frozenset[str] = frozenset(
    {
        "evidence.assemble",
        "evidence.summarise",
        "evidence.identify_missing",
        "evidence.answer",
        "evidence.draft_request",
        "evidence.abstain",
    }
)

MATRIX: dict[str, frozenset[str]] = {
    SYSTEM: frozenset(
        {
            "collection.attribute",
            "ledger.post",
            "ledger.reverse",
            "fx.quote",
            "payment.create",
            "risk.assess",
            "case.open",
            "exception.open",
            "reconciliation.run",
            "evidence.assemble",
        }
    ),
    COMPLIANCE_OFFICER: frozenset(
        {
            "business.request_information",
            "business.approve",
            "business.reject",
            "beneficiary.verify",
            "payment.verify",
            "case.open",
            "case.assign",
            "case.close",
            "alert.clear",
            "evidence.assemble",
        }
    ),
    TREASURY_OPERATOR: frozenset(
        {
            "business.submit",
            "beneficiary.create",
            "beneficiary.change",
            # Treasury performs the callback, so treasury records that it happened.
            # The record is evidence of a check, not an approval of the payment.
            "beneficiary.verify",
            "payment.verify",
            "fx.quote",
            "fx.execute",
            "payment.create",
            "payment.cancel",
            "collection.attribute",
            "evidence.assemble",
        }
    ),
    PAYMENT_APPROVER: frozenset(
        {"payment.approve", "payment.submit", "payment.cancel", "payment.verify", "evidence.assemble"}
    ),
    FINANCE_OPERATOR: frozenset(
        {
            "reconciliation.run",
            "reconciliation.adjust",
            "exception.open",
            "exception.resolve",
            "ledger.post",
            "ledger.reverse",
            "evidence.assemble",
        }
    ),
    RISK_ANALYST: frozenset({"risk.assess", "case.open", "case.assign", "beneficiary.verify", "evidence.assemble"}),
    AI_COPILOT: AI_ALLOWED,
    VIEWER: frozenset(),
}


def can(role: str, action: str) -> bool:
    """Whether `role` may perform `action`. Unknown roles and actions are False."""
    return action in MATRIX.get(role, frozenset())


def require(role: str, action: str, *, context: str = "") -> None:
    """Raise `AuthorityError` unless `role` may perform `action`.

    Called before the state change, never after, so a refusal leaves nothing
    half-applied. The message names the role and the action because an operator
    reading a refused action in the audit log should not have to guess which of
    the two was wrong.
    """
    if action not in ACTIONS:
        raise AuthorityError(f"unknown action {action!r}")
    if role not in MATRIX:
        raise AuthorityError(f"unknown role {role!r}")
    if action in MATRIX[role]:
        return
    suffix = f" ({context})" if context else ""
    if role == AI_COPILOT:
        raise AuthorityError(
            f"the AI copilot may not {action!r}{suffix}. It may only "
            f"{', '.join(sorted(AI_ALLOWED))} — organising evidence and explaining it. "
            "Consequential decisions belong to an authorised person."
        )
    raise AuthorityError(f"role {role!r} may not {action!r}{suffix}")


def roles_for(action: str) -> tuple[str, ...]:
    """Which roles may perform `action` — used by the UI to say who to ask."""
    return tuple(role for role in ROLES if can(role, action))


def is_ai(role: str) -> bool:
    return role == AI_COPILOT


# The boundary, asserted rather than documented. If a later change gives the
# copilot an action that moves money or closes a finding, importing this module
# fails and so does every test.
_overlap = AI_ALLOWED & CONSEQUENTIAL_ACTIONS
if _overlap:  # pragma: no cover - a build-time guard, not a runtime branch
    raise AssertionError(
        f"the AI copilot has been granted consequential actions {sorted(_overlap)}; "
        "this is the one thing CorridorOS does not allow"
    )
if MATRIX[AI_COPILOT] != AI_ALLOWED:  # pragma: no cover - build-time guard
    raise AssertionError("the copilot's matrix row must be exactly AI_ALLOWED")
