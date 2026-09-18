# Evaluation — synthetic

Every figure on this page is a **synthetic evaluation**. The populations are
generated; the outcomes are simulated; none of it transfers to production
traffic, and no number here was produced by a language model.

## Measured in CorridorOS

| Figure | Value | How |
| --- | --- | --- |
| Automated tests | 124 | `python -m pytest` |
| End-to-end scenarios | 7 | `tests/e2e/test_scenarios.py` |
| Deterministic rules · AML typologies | 21 · 6 | `docs/AML_RULE_CATALOG.md` |
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

## The AML layer — measured in CorridorOS

Phase P2 ported CrossBorder RiskOps' six typologies and adapted its rule set onto this platform's
event stream, so these figures are **re-run here** rather than inherited. Regenerate with
`python -m corridoros.cli aml-eval`, which writes `reports/aml_evaluation.json`.

Three independently seeded worlds, 846-odd transfers each, review capacity
12. The population is **deliberately enriched** with planted patterns, so both recall and
precision are far higher than any real monitoring system would see, and neither transfers to
production traffic.

| Figure | Value | What it means |
| --- | --- | --- |
| Recall, clear patterns | **1.000 ± 0.000** | Patterns planted well inside their thresholds. Missing one would mean a detector is broken. |
| Recall, borderline patterns | **0.875 ± 0.000** | Patterns planted *just* inside them. This is the number a threshold change actually moves. |
| Alert precision, raw | **0.162 ± 0.016** | Alerts are mostly noise, as they are in every real monitoring system. |
| Precision at review capacity | **0.833 ± 0.068** | Of the cases a team of this size could open today. **The ordering is the product.** |
| Planted patterns left in the backlog | **8** | The honest half: cases below the capacity line were not cleared, they were not looked at. |

Alert funnel, per world: 334 raw alerts →
106 after deduplication →
31 cases → 12 opened,
19 waiting.

### Recall by typology

| | Typology | Thresholds | Recall |
| --- | --- | --- | --- |
| T01 | Structured transfers below a reporting threshold | threshold_usd=10000, band_low_usd=7000, window_hours=72, min_transfers=3 | 0.800 ± 0.000 |
| T02 | Funds forwarded cross-border shortly after arriving | max_hold_minutes=1440, min_passthrough_pct=80, min_amount_usd=5000 | 1.000 ± 0.000 |
| T03 | Many unrelated senders paying one account | min_senders=8, window_days=14, min_total_usd=20000 | 1.000 ± 0.000 |
| T04 | Funds returning to their origin through intermediaries | min_hops=3, max_hops=5, min_return_pct=70, max_elapsed_hours=168 | 1.000 ± 0.000 |
| T05 | Activity far above, or beside, what the entity declared | min_ratio=4, window_days=30, min_actual_usd=15000 | 1.000 ± 0.000 |
| T06 | Transfers that cannot be judged because information is absent | min_affected=3, min_affected_usd=5000 | 1.000 ± 0.000 |

The detectors never see the generator's labels: `MonitoringContext.blind()` strips them and the
constructor raises on a feed that still carries them, which `tests/test_aml.py` asserts. Without
that guarantee these numbers would be a restatement of the label rather than a measurement.

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

**Superseded for the AML layer by the section above.** These are the source project's own figures,
on its own acquiring population, kept for provenance. They are not CorridorOS results, and the
two are not comparable: a different population, a different subject, and a corridor rule set that
replaced ten of the twenty rules.

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
