"""Guardrails around the copilot.

Ported from `crossborder-riskops/src/riskops/ai/guardrails.py`, whose two-gate
design applies unchanged here:

    A deterministic pattern layer runs **first** and short-circuits, so an
    obvious attack never costs a model call, and only what survives it reaches
    anything expensive or probabilistic.

    **Input gate.** Supplier emails, payment notes and change requests are
    attacker-controlled. Text that addresses a model rather than a person is
    quarantined — removed from the packet and replaced with a marker — before
    any provider sees it. The case still gets a brief; it is simply a brief
    written without the attacker's paragraph in it.

    **Output gate.** Whatever comes back is treated as untrusted too: citations
    must resolve to identifiers the packet actually contains, a finding with no
    resolvable citation is dropped and counted, language claiming the model
    *performed* an action is rejected outright, and PII-shaped strings are
    redacted.

The pattern lists gained corridor-specific entries — a supplier email asking a
system to "update the account and release the payment" is the attack that
matters here, not a merchant appeal — and one CorridorOS rule is new: there is
no recommendation field to force. In RiskOps a forced output could at least
name an action. Here the brief has nowhere to put one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

GUARDRAIL_VERSION = "1.0.0"

QUARANTINE_MARKER = (
    "[quarantined: supplier free text contained instructions aimed at an automated reader "
    "and was withheld from the model]"
)

INJECTION_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", "override_instructions"),
    (r"disregard\s+(the\s+)?(risk\s+)?(signals|instructions|rules|warnings|checks)", "override_instructions"),
    (r"\b(system|assistant|developer)\s*[:>]", "role_impersonation"),
    (r"#{2,}\s*new\s+instructions", "instruction_injection"),
    (r"<!--.*?(assistant|system|ai)\b.*?-->", "hidden_instruction"),
    (r"you\s+are\s+now\s+in\s+\w+\s+mode", "mode_switch"),
    (r"(set|mark|force)\s+.{0,30}(intervention_level|level|action|verdict)\s*(=|to)\s*\w+", "output_forcing"),
    (
        r"(output|return|print|reveal|show)\s+.{0,40}(account\s+number|full\s+customer\s+record|"
        r"internal\s+risk\s+notes|api\s+key|password|credential)",
        "data_exfiltration",
    ),
    (r"skip\s+the\s+\w+\s+(section|check|callback)", "output_forcing"),
    (r"(release|approve|submit)\s+(the\s+)?payment\s+(now|immediately|without)", "output_forcing"),
    (r"no\s+(need\s+for\s+)?(callback|verification|second\s+approver)", "output_forcing"),
    (r"do\s+not\s+(open\s+a\s+case|review|hold)", "output_forcing"),
)

AUTHORITY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"pre[- ]?approved", "claimed_preapproval"),
    (r"already\s+(been\s+)?(reviewed|cleared|approved|verified)", "claimed_prior_review"),
    (r"policy\s+exception\b", "claimed_exception"),
    (r"\bexception\s+(was\s+|has\s+been\s+)?granted\b", "claimed_exception"),
    (
        r"(compliance|risk|treasury)\s+(team\s+)?(has\s+)?(already\s+)?(cleared|signed[- ]off|approved)",
        "claimed_signoff",
    ),
    (r"\bdo not (hold|review)\b", "instructed_no_review"),
    (r"close\s+the\s+(case|exception)", "instructed_closure"),
)

# Phrases in which the copilot claims to have *done* something. Distinct from
# describing: "the callback is outstanding" is its job; "I have released this
# payment" is a claim of authority it does not have.
AUTHORITY_CLAIM_PATTERNS: tuple[str, ...] = (
    r"\bi (have |'ve )?(released|blocked|held|approved|submitted|cleared|frozen|cancelled|canceled)\b",
    r"\b(the (payment|case|exception|business) (has been|was)) (released|approved|submitted|closed|cleared)\b",
    r"\bi (am |'m )?(releasing|approving|submitting|clearing|holding)\b",
    r"\b(i|we) (hereby )?(authorise|authorize|approve|clear)\b",
    r"\bcase (is )?(now )?closed\b",
    r"\bno human review (is )?(needed|required)\b",
    r"\bdecision:\s*(final|committed)\b",
)

PII_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:\d[ -]?){13,19}\b", "[redacted:card-like-number]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[redacted:email]"),
    (r"\b(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}\b", "[redacted:phone-like]"),
    (r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", "[redacted:iban-like]"),
)

_INJECTION_RE = tuple((re.compile(p, re.IGNORECASE | re.DOTALL), label) for p, label in INJECTION_PATTERNS)
_AUTHORITY_RE = tuple((re.compile(p, re.IGNORECASE), label) for p, label in AUTHORITY_PATTERNS)
_CLAIM_RE = tuple(re.compile(p, re.IGNORECASE) for p in AUTHORITY_CLAIM_PATTERNS)
_PII_RE = tuple((re.compile(p), replacement) for p, replacement in PII_PATTERNS)


def match_injection_patterns(text: str) -> list[str]:
    return sorted({label for pattern, label in _INJECTION_RE if pattern.search(text or "")})


def match_authority_patterns(text: str) -> list[str]:
    return sorted({label for pattern, label in _AUTHORITY_RE if pattern.search(text or "")})


def find_authority_claims(text: str) -> list[str]:
    return sorted({pattern.pattern for pattern in _CLAIM_RE if pattern.search(text or "")})


def redact_pii(text: str) -> tuple[str, int]:
    redactions = 0
    result = text or ""
    for pattern, replacement in _PII_RE:
        result, count = pattern.subn(replacement, result)
        redactions += count
    return result, redactions


@dataclass
class InputGateResult:
    verdict: str  # clean | quarantined
    labels: list[str] = field(default_factory=list)
    sanitised_text: str = ""
    original_length: int = 0

    @property
    def quarantined(self) -> bool:
        return self.verdict == "quarantined"


def screen_untrusted_text(text: str) -> InputGateResult:
    """The input gate. Runs before any provider call, deterministically."""
    raw = text or ""
    labels = sorted(set(match_injection_patterns(raw)) | set(match_authority_patterns(raw)))
    if not labels:
        return InputGateResult("clean", [], raw, len(raw))
    return InputGateResult("quarantined", labels, QUARANTINE_MARKER, len(raw))


@dataclass
class GuardrailReport:
    verdict: str = "pass"  # pass | modified | rejected
    reasons: list[str] = field(default_factory=list)
    dropped_findings: int = 0
    unresolved_citations: list[str] = field(default_factory=list)
    redactions: int = 0
    injection_verdict: str = "clean"
    injection_labels: list[str] = field(default_factory=list)
    guardrail_version: str = GUARDRAIL_VERSION

    def as_row(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "dropped_findings": self.dropped_findings,
            "unresolved_citations": list(self.unresolved_citations),
            "redactions": self.redactions,
            "injection_verdict": self.injection_verdict,
            "injection_labels": list(self.injection_labels),
            "guardrail_version": self.guardrail_version,
        }
