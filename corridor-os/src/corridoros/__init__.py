"""CorridorOS — China–Singapore cross-border payment operations platform.

One product, four modules, one set of identifiers:

    corridoros.core          the eleven objects, twelve events, permissions, audit
    corridoros.payments      Payment Core: KYB, collection, ledger, FX, payout,
                             settlement, reconciliation
    corridoros.risk          Risk & Compliance: deterministic signals, cases, SLA
    corridoros.intervention  Pre-payment Intervention Engine
    corridoros.evidence      Evidence & Policy Copilot

Every business, supplier, payment, document and number in this package is
synthetic and produced by a seeded generator. Nothing here has run in
production, holds a licence, or is connected to a bank.
"""

__version__ = "0.1.0"
