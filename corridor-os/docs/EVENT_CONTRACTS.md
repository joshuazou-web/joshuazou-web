# Event contracts

Twelve event types. Publishing anything else raises.

| Event | Published by | Read by |
| --- | --- | --- |
| `business.submitted` | `payments.kyb` | console |
| `business.approved` | `payments.kyb` | payout gate (`may_move_money`) |
| `payment.created` | `payments.payout` | `risk`, `evidence` |
| `beneficiary.changed` | `payments.beneficiaries` | `risk`, `intervention` |
| `risk.assessed` | `risk.assess` | `intervention`, console |
| `intervention.required` | `platform` (from `intervention.decide`) | `payments.payout`, console |
| `case.opened` | `risk.cases` | `payments.payout` (blocks submission) |
| `payment.approved` | `payments.payout` | console, audit |
| `payment.submitted` | `payments.payout` | settlement, console |
| `payment.settled` | `payments.payout` | `reconciliation` |
| `reconciliation.failed` | `payments.reconciliation` | exception queue |
| `exception.resolved` | `payments.reconciliation` | console |

## The envelope

```json
{
  "event_id": "evt_…",
  "seq": 7,
  "type": "payment.approved",
  "occurred_at": "2026-09-14T12:35:00+00:00",
  "actor_role": "payment_approver",
  "actor_id": "approver.lim",
  "subject": { "payment": "pay_…", "business": "biz_…" },
  "payload": { "approvals": ["dec_…"], "required_approvals": 2 }
}
```

`subject` keys are object kinds, and each value is validated against that kind,
so an event cannot carry a `business_id` in the `payment` slot.

## Three guarantees, enforced in `core/events.py`

**Append-only with a monotonic sequence.** Nothing is edited; a correction is a
later event.

**Idempotency by key.** A repeated delivery returns the first event and changes
nothing. This is the mechanism behind "a retry never creates a second payout" —
the payout engine relies on it rather than reimplementing it.

**Ordering by lifecycle rank.** Within one payment,
`created(1) → risk.assessed(2) → intervention.required(3) → approved(4) →
submitted(5) → settled(6) → reconciliation.failed(7)`. An event that arrives
early or repeats a rank is **quarantined** — not applied, not dropped. An
operator can see it in the Audit section. Dropping it loses information;
applying it corrupts the ledger.

Events outside that map (a beneficiary change, a case opening) may legitimately
arrive at any point and are not ordered against the lifecycle.
