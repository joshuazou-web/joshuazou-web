# Architecture

## The problem the structure has to solve

A Chinese company opening in Singapore has to complete entity onboarding, collect
SGD, convert currency, pay suppliers, pass risk checks, survive an AML
investigation, settle and reconcile — and be able to show, for every movement of
money and every compliance decision, what evidence was used and who was allowed
to decide.

Four separate demonstrations cannot show that, however good each one is,
because none of them can point at the others' objects. CorridorOS is those four
capabilities rebuilt around one set of identifiers.

## Layers

```
                    apps/web  — one console, seven sections
                          │  REST (or a published snapshot)
                    apps/api  — FastAPI, projections only
   ┌───────────────┬───────────────┬───────────────┬────────────────────┐
   │ payments      │ risk          │ evidence      │ intervention       │
   │ Payment Core  │ Risk &        │ Evidence &    │ Pre-payment        │
   │               │ Compliance    │ Policy Copilot│ Intervention Engine│
   └───────────────┴───────────────┴───────────────┴────────────────────┘
   ┌──────────────────────────────────────────────────────────────────┐
   │ core — 11 objects · 12 events · identifiers · money · RBAC · audit │
   └──────────────────────────────────────────────────────────────────┘
```

**Dependency rule.** Every module imports `core`. No module imports another
module. `corridoros/platform.py` is the only file that knows all four exist, and
all it does is wire them together. That rule is what keeps this a platform
rather than four packages in one repository.

Payments publishes events; risk, intervention and evidence read them.
`payments` contains no risk scoring and no thresholds; `risk` contains no ledger;
`intervention` decides a level and cannot apply it; `evidence` is called and
never calls.

## The modules

| Module | Comes from | Owns |
| --- | --- | --- |
| `core` | new, with `money.py` and `audit/chain.py` ported from CrossBorder RiskOps | identifiers, the eleven objects, the twelve events, the permission matrix, the hash-chained audit log |
| `payments` | the China-to-Singapore Corridor blueprint, implemented for the first time | KYB, collection, double-entry ledger, FX quoting, payout lifecycle, settlement, three-way reconciliation |
| `risk` | CrossBorder AML RiskOps | **two deterministic layers**: 21 rules over one payment, and 6 AML typologies over the monitored transfer feed — plus deduplication, case aggregation, eight-factor priority, SLA and an honest backlog |
| `intervention` | ThinkBeforeClick FinSafe (`b2b-engine.js`) | amount tiers, signal levels, the five-step ladder, required verifications |
| `evidence` | WealthGuard Proofline | the evidence register, packets, citation-validated briefs, guardrails, abstention |

## Two layers inside `risk`

```
one payment ──▶ rules.py (21 rules, 8 families) ──▶ RiskAssessment ──▶ intervention
                                                                  └──▶ payment-review case

the monitored feed ──▶ detect.py (6 typologies) ──▶ alerts
                                                     │  aggregate.py
                                                     ▼
                              deduplicate (7d) ──▶ cases (30d) ──▶ priority.py (8 factors)
                                                                          │
                                                          ┌───────────────┴───────────────┐
                                                     within capacity                  backlog
                                                     (a team's day)            (not cleared — not looked at)
```

The feed is the union of the platform's own settled movements and the synthetic corridor
population, so the flagship payment appears in the AML queue's world rather than in a separate
demonstration. `scenario/feed.py` builds it; `MonitoringContext.blind()` strips the generator's
labels before any detector sees it.

## Flow of one payment

```
payment.created ──▶ risk.assessed ──▶ intervention.required ──▶ case.opened
                                            │                        │
                                            ▼                        ▼
                                    requirements stored     payment held until
                                    on the instruction      a person closes it
                                            │
                          verifications completed by people
                                            │
                                            ▼
        payment.approved (n distinct approvers) ──▶ payment.submitted ──▶ payment.settled
                                                              │
                                                              ▼
                                        reconciliation.failed ──▶ exception.resolved
```

Money state and compliance state are separate throughout. An entity may be
approved while a single payout still needs information; a transfer may be
accepted by the rail while settlement remains unreconciled.

## Where state lives

There is no database. The platform holds its objects in memory and its history
in the event log and the audit chain, and the CLI projects both into
`data/snapshot.json`. That is a deliberate limit of a portfolio system, not a
claim about production architecture: what is being demonstrated is the contract
— typed events, idempotency, ordering, immutability, permissions, hash chaining
— which is the part that would survive being put behind Postgres and a broker.

## Running it

```bash
pip install -e '.[dev]'
python -m corridoros.cli demo          # the flagship story, printed
python -m corridoros.cli aml           # a day's transaction monitoring
python -m corridoros.cli aml-eval      # reports/aml_evaluation.json
python -m corridoros.cli snapshot      # data/snapshot.json
python -m pytest                       # the specification

pip install -e '.[api]'
uvicorn apps.api.main:app --reload     # http://127.0.0.1:8000/api/snapshot

cd apps/web && npm install && npm run dev
```

Without the API the console reads the published snapshot, so the static build
demonstrates the same flow with no backend.
