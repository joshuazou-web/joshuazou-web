"""The Evidence & Policy Copilot.

Six things it may do — assemble evidence, summarise a case, name what is
missing, answer a question with citations, draft a request for the missing
documents, and abstain. Everything else is absent, and absent in the strongest
sense available: **`CaseBrief` has no field in which a decision could be
placed.** Not a recommendation, not a level, not an action, not a score. A
prompt cannot force a field that does not exist, and a caller cannot read one.

This is the WealthGuard method — evidence first, citations that resolve,
deterministic composition, abstention when the evidence will not carry an
answer — applied to payment operations instead of investment research.

**On the provider.** The composer in this module is deterministic: it turns the
packet into sentences by template, and every sentence carries the identifier of
the item it came from. That is what the tests, the demo and any published
number run on. A language model could replace the composition step — it is the
one step where language is the product — and if it did, its output would pass
through the same output gate, which drops findings whose citations do not
resolve into `packet.evidence_ids`. No model is called here, and no figure in
this repository comes from one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from ..core.authority import AI_COPILOT, require
from ..core.domain import Beneficiary, PaymentInstruction, RiskAssessment
from .guardrails import (
    GuardrailReport,
    find_authority_claims,
    redact_pii,
    screen_untrusted_text,
)
from .packet import EvidencePacket

BRIEF_SCHEMA_VERSION = "1.0.0"

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")

# Human-readable names for the document kinds, used when drafting a request.
KIND_LABELS: dict[str, str] = {
    "invoice": "the supplier invoice",
    "purchase_order": "the matching purchase order",
    "contract": "the signed contract",
    "beneficiary_change_authorisation": "a signed account-change authorisation on company letterhead",
    "callback_record": "a record of the callback to a known contact",
    "incorporation_document": "the certificate of incorporation",
    "ownership_declaration": "the beneficial-ownership declaration",
    "bank_letter": "a bank letter confirming the account",
}


@dataclass(frozen=True)
class Finding:
    """One statement plus the evidence identifiers it rests on."""

    statement: str
    citations: tuple[str, ...] = ()

    def as_row(self) -> dict[str, object]:
        return {"statement": self.statement, "citations": list(self.citations)}


@dataclass
class CaseBrief:
    """The copilot's whole output.

    Deliberately missing: any field that could carry a decision, an approval, an
    intervention level, a risk score, or an instruction. If you are looking for
    where the copilot records what it thinks should happen — there is nowhere.
    """

    subject_type: str
    subject_id: str
    summary: str
    key_facts: list[Finding] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    questions_for_reviewer: list[str] = field(default_factory=list)
    abstained: bool = False
    abstention_reason: str = ""
    guardrails: GuardrailReport = field(default_factory=GuardrailReport)
    generated_at: datetime | None = None
    schema_version: str = BRIEF_SCHEMA_VERSION
    produced_by: str = AI_COPILOT

    def as_row(self) -> dict[str, object]:
        return {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "summary": self.summary,
            "key_facts": [item.as_row() for item in self.key_facts],
            "missing_information": list(self.missing_information),
            "questions_for_reviewer": list(self.questions_for_reviewer),
            "abstained": self.abstained,
            "abstention_reason": self.abstention_reason,
            "guardrails": self.guardrails.as_row(),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "schema_version": self.schema_version,
            "produced_by": self.produced_by,
        }


# The guarantee, asserted rather than promised. A field added later whose name
# suggests a decision fails this check, and with it the test suite.
FORBIDDEN_BRIEF_FIELDS: frozenset[str] = frozenset(
    {
        "decision",
        "recommendation",
        "recommended_action",
        "action",
        "verdict",
        "approval",
        "approved",
        "intervention_level",
        "level",
        "risk_score",
        "outcome",
        "release",
    }
)


def brief_fields() -> frozenset[str]:
    return frozenset(CaseBrief.__dataclass_fields__)


class Copilot:
    """Deterministic evidence assistant. Advisory, cited, and never authoritative."""

    def __init__(self, actor_id: str = "copilot") -> None:
        self.actor_id = actor_id

    # -- the output gate ---------------------------------------------------

    def _gate(
        self,
        brief: CaseBrief,
        allowed_citations: frozenset[str],
        input_gate_labels: list[str],
        input_verdict: str,
    ) -> CaseBrief:
        report = GuardrailReport(
            injection_verdict=input_verdict,
            injection_labels=list(input_gate_labels),
        )

        kept: list[Finding] = []
        for finding in brief.key_facts:
            unresolved = [
                citation for citation in finding.citations if citation not in allowed_citations
            ]
            if unresolved or not finding.citations:
                report.dropped_findings += 1
                report.unresolved_citations.extend(unresolved)
                continue
            claims = find_authority_claims(finding.statement)
            if claims:
                report.dropped_findings += 1
                report.reasons.append("a statement claimed the copilot had acted")
                continue
            redacted, count = redact_pii(finding.statement)
            report.redactions += count
            kept.append(Finding(redacted, finding.citations))

        summary, summary_redactions = redact_pii(brief.summary)
        report.redactions += summary_redactions
        if find_authority_claims(summary):
            summary = (
                "The summary was rejected because it claimed the copilot had acted on this payment."
            )
            report.reasons.append("summary claimed an action")
            report.verdict = "rejected"

        if report.dropped_findings or report.redactions:
            if report.verdict != "rejected":
                report.verdict = "modified"
        if input_verdict == "quarantined":
            report.reasons.append(
                "supplier free text addressed an automated reader and was withheld from composition"
            )
            if report.verdict == "pass":
                report.verdict = "modified"

        brief.key_facts = kept
        brief.summary = summary
        brief.guardrails = report
        return brief

    # -- the six permitted capabilities -----------------------------------

    def summarise_payment(
        self,
        packet: EvidencePacket,
        payment: PaymentInstruction,
        beneficiary: Beneficiary,
        assessment: RiskAssessment | None = None,
        *,
        now: datetime,
        untrusted_text: str = "",
    ) -> CaseBrief:
        """Turn an assembled packet into a cited brief for a reviewer."""
        require(AI_COPILOT, "evidence.summarise", context=payment.payment_id)
        gate = screen_untrusted_text(untrusted_text)

        facts: list[Finding] = []
        for item in packet.items:
            dated = f", dated {item.issued_at.date().isoformat()}" if item.issued_at else ""
            facts.append(
                Finding(
                    f"{item.title} ({item.issuer}{dated}) is on file: {item.excerpt}",
                    (item.evidence_id,),
                )
            )

        missing = [KIND_LABELS.get(kind, kind) for kind in packet.missing_kinds]
        questions: list[str] = []
        if assessment is not None and assessment.has("payee_account_change"):
            questions.append(
                "Was the account change confirmed by calling a number already on file, "
                "rather than one supplied in the request?"
            )
        if packet.missing_kinds:
            questions.append(
                f"Can {', '.join(missing)} be obtained before this payment is approved?"
            )

        if not packet.items:
            brief = CaseBrief(
                subject_type="payment",
                subject_id=payment.payment_id,
                summary="",
                abstained=True,
                abstention_reason=(
                    "No evidence is on file for this payment, so there is nothing to summarise. "
                    "Asking for a summary of an empty packet would produce a plausible paragraph "
                    "about nothing."
                ),
                generated_at=now,
            )
            return self._gate(brief, packet.evidence_ids, gate.labels, gate.verdict)

        summary = (
            f"{payment.amount.format()} to {beneficiary.display_name} "
            f"({beneficiary.bank_country}, account ending {beneficiary.account_last4}) "
            f"for {payment.purpose_code}. {len(packet.items)} evidence item(s) on file"
            + (
                f"; {len(packet.missing_kinds)} required document(s) still missing."
                if packet.missing_kinds
                else "; all required documents are present."
            )
        )
        brief = CaseBrief(
            subject_type="payment",
            subject_id=payment.payment_id,
            summary=summary,
            key_facts=facts,
            missing_information=missing,
            questions_for_reviewer=questions,
            generated_at=now,
        )
        return self._gate(brief, packet.evidence_ids, gate.labels, gate.verdict)

    def identify_missing(self, packet: EvidencePacket) -> tuple[str, ...]:
        """Name the documents a decision still lacks. A fact about the packet."""
        require(AI_COPILOT, "evidence.identify_missing", context=packet.subject_id)
        return tuple(KIND_LABELS.get(kind, kind) for kind in packet.missing_kinds)

    def answer(
        self,
        question: str,
        packet: EvidencePacket,
        *,
        now: datetime,
    ) -> CaseBrief:
        """Answer a reviewer's question from the packet, or abstain.

        The retrieval is a keyword overlap against the packet's own items, which
        keeps the answer inside evidence someone else selected. When nothing in
        the packet addresses the question, it abstains rather than composing a
        plausible sentence from general knowledge — the failure mode that makes
        a fluent assistant untrustworthy in an audit.
        """
        require(AI_COPILOT, "evidence.answer", context=packet.subject_id)
        gate = screen_untrusted_text(question)
        if gate.quarantined:
            brief = CaseBrief(
                subject_type=packet.subject_type,
                subject_id=packet.subject_id,
                summary="",
                abstained=True,
                abstention_reason=(
                    "The question contained instructions aimed at an automated reader rather than "
                    "a question about the evidence, so it was not answered."
                ),
                generated_at=now,
            )
            return self._gate(brief, packet.evidence_ids, gate.labels, gate.verdict)

        words = {word for word in _tokens(question) if len(word) > 3}
        scored: list[tuple[int, object]] = []
        for item in packet.items:
            haystack = _tokens(f"{item.title} {item.excerpt} {' '.join(item.structured_facts.values())}")
            overlap = len(words & set(haystack))
            if overlap:
                scored.append((overlap, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].evidence_id))

        if not scored:
            brief = CaseBrief(
                subject_type=packet.subject_type,
                subject_id=packet.subject_id,
                summary="",
                abstained=True,
                abstention_reason=(
                    "Nothing in this packet addresses the question. The honest answer is that the "
                    "evidence does not carry one."
                ),
                generated_at=now,
            )
            return self._gate(brief, packet.evidence_ids, gate.labels, gate.verdict)

        facts = [
            Finding(f"{item.title}: {item.excerpt}", (item.evidence_id,))
            for _score, item in scored[:3]
        ]
        brief = CaseBrief(
            subject_type=packet.subject_type,
            subject_id=packet.subject_id,
            summary=f"{len(facts)} item(s) in the packet bear on that question.",
            key_facts=facts,
            generated_at=now,
        )
        return self._gate(brief, packet.evidence_ids, gate.labels, gate.verdict)

    def draft_information_request(
        self, packet: EvidencePacket, *, recipient: str, now: datetime
    ) -> str:
        """Draft a request for the missing documents — for a person to send.

        It returns text. It does not send anything, and there is no send method
        on this class.
        """
        require(AI_COPILOT, "evidence.draft_request", context=packet.subject_id)
        if not packet.missing_kinds:
            return ""
        wanted = "\n".join(
            f"  - {KIND_LABELS.get(kind, kind)}" for kind in packet.missing_kinds
        )
        return (
            f"Draft — for review before sending to {recipient}\n\n"
            f"Regarding {packet.subject_type} {packet.subject_id}, we are unable to proceed until "
            "the following is on file:\n"
            f"{wanted}\n\n"
            "Please reply with the documents attached. Where bank details are concerned we will "
            "also confirm them by telephone on the number already on our file.\n\n"
            f"(Drafted {now.date().isoformat()} by the CorridorOS evidence copilot; "
            "a person reviews and sends this.)"
        )


def _tokens(text: str) -> list[str]:
    return [word.lower() for word in _WORD_RE.findall(text or "")]
