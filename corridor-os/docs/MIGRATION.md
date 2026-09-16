# Migration: four projects into one platform

## What was there before

| Source project | Form | Size |
| --- | --- | --- |
| China-to-Singapore Payment Corridor | two Markdown documents in the portfolio repository | ~420 lines, **no code** |
| CrossBorder AML RiskOps | Python + DuckDB + Streamlit, 11 views | ~14.6k lines of `src/riskops` |
| WealthGuard Proofline | FastAPI + React | ~3.6k lines of backend |
| ThinkBeforeClick FinSafe | browser-native JavaScript | ~1.1k lines |

The corridor — the one piece carrying the China–Singapore identity — was the one
piece with nothing behind it. The other three worked but shared no identifier,
no event, no audit log and no business story.

## Identifier mapping

| Before | Now | Note |
| --- | --- | --- |
| `riskops.merchant_id` | `business_id` | semantic change: merchant → outbound Chinese entity |
| `riskops.wallet_id` | `beneficiary_id` | semantic change: counterparty wallet → supplier payee |
| `riskops.transaction_id` | `payment_id` | renamed and prefixed |
| `riskops.case_id`, `decision_id` | unchanged | |
| `wealthguard.chunk_id` | `evidence_id` | checksum and page/paragraph location kept |
| `wealthguard.document_id` | `EvidenceItem.issuer` + `location` | demoted to fields |
| `wealthguard.session_id` | removed | context is now `payment_id` / `case_id` |
| `finsafe.input_id` | removed | the subject is a payment, not a pasted message |
| `finsafe.signal_id` | `RiskSignal.signal_id` | strings kept verbatim so the original cases still map |

## Kept, adapted, dropped

**Ported with the reasoning intact**

- `riskops/money.py` → `core/money.py` (unchanged)
- `riskops/audit/chain.py` → `core/audit.py` (unchanged algorithm, widened coverage)
- `riskops/ai/guardrails.py` → `evidence/guardrails.py` (corridor-specific patterns added)
- `riskops/statemachine.py` → `payments/payout.py` (acquiring lifecycle replaced by the B2B payout lifecycle; the ordering and amount checks kept)
- `finsafe/b2b-engine.js` → `intervention/engine.py` (amount floor, signal ceiling, the large-payee-change override, `why_not_weaker` / `why_not_stronger`)
- `finsafe/b2b-data.js` → `intervention/policy.py` (tiers restated in SGD; source identifiers kept)
- WealthGuard's evidence discipline → `evidence/` (checksums, locations, citation resolution, abstention)
- The corridor blueprint's control points, reconciliation taxonomy and object list → implemented in `payments/`

**Adapted**

- WealthGuard's suitability policy engine becomes evidence-completeness policy: `packet.REQUIRED_FOR_PURPOSE` and `REQUIRED_AFTER_BENEFICIARY_CHANGE`
- FinSafe's input changes from pasted text to a `PaymentInstruction` plus a `RiskAssessment` plus the state of the evidence
- RiskOps' cases generalise to `ReviewCase`, shared by AML investigation, KYB review and payment review

**Not carried over**

- RiskOps' Streamlit application and its 1,060-line i18n module (replaced by one console)
- WealthGuard's wealth-management surface: instruments, holdings, portfolio endpoints, investment arithmetic
- FinSafe's consumer anti-scam flow: ten scam categories, the nine-stage consumer model, micro-learning
- Three separate audit logs, three configuration systems, three test harnesses

The four source repositories are unchanged and remain readable as the originals.

## Phases

| Phase | Contents | Status |
| --- | --- | --- |
| P0 | core contracts: identifiers, objects, events, permissions, audit | **done** |
| P1 | Payment Core: KYB, collection, ledger, FX, payout, settlement, reconciliation | **done** |
| P4 | Pre-payment Intervention Engine | **done** |
| P5 | one console, snapshot export, FastAPI | **done** |
| — | end-to-end scenarios 1–7 | **done** |
| P2 | the rule set and the six AML typologies on the event stream; analyst workbench; queue evaluation | **done** |
| P3 | WealthGuard's official-source corpus as `EvidenceItem`s; retrieval evaluation | next |
| P6 | rewrite the portfolio README around one system; cross-link the source repositories | next |

### What phase P2 actually moved

| Source | Here | Change |
| --- | --- | --- |
| `riskops/aml/typology.py` | `risk/typologies.py` | Thresholds, severities and counter-evidence hints unchanged; explanations re-worded for suppliers and corridors instead of wallets |
| `riskops/aml/detect.py` | `risk/detect.py` | Six detectors, same matching conditions, rewritten against `Transfer` records instead of pandas frames — the domain layer keeps its zero dependencies |
| `riskops/aml/priority.py` | `risk/priority.py` | Eight factors, weights summing to 1.0 and asserted; KYC tier → KYB status, device breadth → counterparty-and-country breadth |
| `riskops/aml/aggregate.py` | `risk/aggregate.py` | Dedup window and case window unchanged; the forbidden case states carried over verbatim |
| `riskops/aml/world.py` | `scenario/population.py` | A corridor population instead of a wallet population, with **clear** and **borderline** planted patterns so recall reports which half moved |
| `riskops/risk/rules.py` (20) | `risk/rules.py` (21) | Adapted, not copied: eleven carry over with the subject changed, ten card-specific rules replaced by corridor equivalents, one added for instruction-text patterns |
| `riskops/eval/runner.py` | `risk/evaluate.py` | Recall split by difficulty, precision raw and at capacity, and the planted patterns left in the backlog as a headline row |

The provenance guard came with them: the generator marks what it planted, and
`MonitoringContext.blind()` removes those marks before any detector sees the feed. Without it the
recall figures would restate the label instead of measuring detection.

**Still ahead (P3).** WealthGuard's 13 official documents and 1,714 checksummed evidence chunks
become `EvidenceItem`s, with its citation-trace evaluation re-run here.
