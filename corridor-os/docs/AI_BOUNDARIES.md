# What the AI may do, and what it cannot

## The six it may do

| Capability | Where |
| --- | --- |
| Assemble an evidence packet from existing records | `evidence/packet.py` |
| Write a case summary from an assembled packet | `Copilot.summarise_payment` |
| Name the documents a decision still lacks | `Copilot.identify_missing` |
| Answer a reviewer's question with citations | `Copilot.answer` |
| Draft an information request for a person to send | `Copilot.draft_information_request` |
| Abstain when the evidence will not carry an answer | any of the above |

## The six it cannot do

Approve a KYB case · change the ledger · execute FX · submit or release a
payment · clear an AML alert · close an investigation or an exception.

## How that is enforced — four independent mechanisms

**1. The permission matrix.** `core/authority.py` holds one row per role.
`AI_COPILOT`'s row is exactly `AI_ALLOWED`, six entries, and an assertion at
import time fails the build if it ever intersects `CONSEQUENTIAL_ACTIONS`. Every
write in the platform calls `require()` before changing anything.

**2. The object refuses.** `ApprovalDecision.__post_init__` raises if
`actor_role == "ai_copilot"`. A caller that builds a decision by hand and
inserts it directly still cannot make the copilot the author of one.

**3. The audit log refuses.** `AuditLog.record_decision` rejects the copilot
explicitly, records the attempt in `refusals`, and writes nothing to the chain.
The flagship demonstration contains one such refusal, and the console's
"copilot refusals" figure counts real ones.

**4. The output has nowhere to put a decision.** `CaseBrief` has no
`decision`, `recommendation`, `action`, `verdict`, `approval`, `level` or
`score` field. `tests/test_ai_boundary.py` asserts the absence. A prompt cannot
force a field that does not exist, and a caller cannot read one.

## The gates around the copilot

Ported from RiskOps' two-gate design.

**Input gate.** Supplier emails and payment notes are attacker-controlled. Text
addressing an automated reader rather than a person is quarantined before
composition — the brief is still written, just without that paragraph in it.

**Output gate.** Every statement must cite an `evidence_id` that resolves inside
the packet; one that does not is dropped and counted. Language claiming the
copilot performed an action is rejected. PII-shaped strings are redacted.

## What no model does here

Detection, scoring, prioritisation, routing, intervention levels and every
lifecycle transition are deterministic. **No language model is called anywhere
in this repository**, and no figure in it was produced by one. The composer in
`evidence/copilot.py` is templated; if a model replaced that step, its output
would pass through the same output gate, and that would be the only step it
touched.
