# Truth and limitations

## Everything here is synthetic

Every company, supplier, invoice, purchase order, bank reference, amount, risk
signal and result in this repository was written for a demonstration. There is
no real entity, document, bank, payment or customer anywhere in it.

- CorridorOS **has never run in production**.
- It holds **no licence** of any kind and has not been reviewed by a regulator
  or a financial institution.
- It has **no bank, payment-institution or provider partner**, and no
  commercial relationship with any organisation named in a citation.
- **No real payment has ever passed through it**, in any currency.
- It has **no pilot, no user, and no customer**. No usability figure, adoption
  figure or operational result is claimed.

References to MAS, the Payment Services Act, PayNow Corporate or FAST are
starting points for product discovery, not legal analysis, and not a claim that
this design satisfies any requirement. A licensed institution or qualified
adviser would determine the actual regulated perimeter.

## What is implemented, and what is not

Implemented and tested: the domain model and identifiers, the twelve events with
idempotency and ordering, the permission matrix, the hash-chained audit log, the
double-entry ledger, KYB, collection, FX quoting with expiry, the payout
lifecycle with idempotency and dual approval, settlement, three-way
reconciliation with typed exceptions, the intervention ladder, the payment-risk
signal set, the evidence register with checksums, and the copilot with both
guardrail gates.

Not yet ported (phase P2, see `MIGRATION.md`): the twenty transaction-integrity
rules and six AML typologies from CrossBorder RiskOps, the analyst workbench,
and WealthGuard's official-source corpus. Where this repository shows a risk
queue, it is running the smaller signal set described in `risk/signals.py`, and
says so in the console.

## What the audit chain proves

It makes a **partial** edit detectable: changing one entry invalidates it and
every entry after it. It does not prove non-repudiation. Someone who can rewrite
the whole log can recompute every link. Real non-repudiation needs the head
anchored somewhere the editor does not control — signed, or published
externally. This project does not do that.

## What the numbers mean

See `EVALUATION.md`. In short: every figure is a **synthetic evaluation**. The
inherited figures from the four source projects are labelled with the project
and dataset that produced them, and are not restated as CorridorOS results.

## Architectural limits of a portfolio system

State lives in memory; there is no database, no queue, no authentication, no
tenancy and no key management. The event bus is synchronous and in-process. What
is being demonstrated is the contract, not the deployment.
