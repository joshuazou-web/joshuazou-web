# Evaluation — synthetic

Every figure on this page is a **synthetic evaluation**. The populations are
generated; the outcomes are simulated; none of it transfers to production
traffic, and no number here was produced by a language model.

## Measured in CorridorOS

| Figure | Value | How |
| --- | --- | --- |
| Automated tests | 65 | `python -m pytest` |
| End-to-end scenarios | 7 | `tests/e2e/test_scenarios.py` |
| Events in the flagship story | 16 | `corridoros demo` |
| Audit entries, chain status | 25, `verified` | `corridoros verify-audit` |
| Ledger balanced across every account and currency | yes | asserted in scenarios 1, 3, 5 |
| Second payouts created by a retry | **0** | scenario 3 |
| Executions against an expired quote | **0** | scenario 5 |
| Ledger postings from a refused FX execution | **0** | scenario 5 |
| Reconciliation runs marked clean while a difference was unexplained | **0** | scenario 7, the call raises |
| Copilot-authored decisions | **0** | `tests/test_ai_boundary.py`, enforced four ways |
| Copilot refusals recorded in the flagship story | 1 | `corridoros demo` |

The seven scenarios: normal payment · beneficiary account change · duplicate
payment · suspicious transaction · expired FX quote · duplicated and
out-of-order webhook · reconciliation mismatch.

## Inherited from the source projects

These were measured **in the projects named**, on their own synthetic datasets,
with their own rule versions. They are reproduced here for provenance and are
**not** restated as CorridorOS results. Where the corresponding code is ported
in phases P2 and P3, the figures will be re-run here and any difference reported.

### ThinkBeforeClick FinSafe — business payment pack

The intervention ladder in `intervention/` is a port of this engine.

| Metric | Value |
| --- | --- |
| Fixed business cases | 82 |
| Intervention-level accuracy | 1.000 |
| Over-intervention rate | 0.000 |
| Under-intervention rate | 0.000 |
| Baseline: uniform checklist | 0.220 accuracy |
| Baseline: amount only, no signals | 0.561 accuracy |

Consumer pack, same project: 161 fixed cases, 97.5% intervention accuracy with
rules owning the level against 29.2% for an LLM without them, at 95.2%
critical-signal recall.

### CrossBorder AML RiskOps

Ported so far: `money.py`, the audit chain, the guardrails. The rules and
typologies behind these figures arrive in P2.

| Metric | Value |
| --- | --- |
| Alert precision, raw | 0.223 ± 0.004 |
| Precision at review capacity | 0.870 ± 0.027 |
| Recall (5 independently generated worlds, 6,000 transactions) | 97.01% ± 0.42% |
| Deterministic rules · AML typologies | 20 · 6 |
| Automated tests in that project | 453 |

### WealthGuard Proofline

Ported so far: the evidence discipline. The corpus arrives in P3.

| Metric | Value |
| --- | --- |
| Official documents ingested | 13 |
| Evidence chunks with page/paragraph location and SHA-256 | 1,714 |
| Fixed-seed policy regression cases | 126, all passing |
| Citation-trace cases | 39, all passing |

### Not a CorridorOS figure, and not a FinSafe figure either

ThinkBeforeClick's original five-person NUS team prototype recorded 23
participants, 4.3/5 usability and an Honourable Mention. That tested the
**original prototype**, not FinSafe and not CorridorOS. It appears here only so
that it is never mistaken for one.
