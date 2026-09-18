# Data dictionary

Every identifier is `<prefix>_<body><check>`; the check character is derived
from the prefix and body, so a mistyped, truncated or invented identifier does
not validate (`core/ids.py`).

| Object | Identifier | Key fields |
| --- | --- | --- |
| `BusinessProfile` | `business_id` (`biz_…`) | `legal_name`, `entity_country`, `uen`, `review_status`, `evidence_ids`, `evidence_version`, `decided_by` |
| `Beneficiary` | `beneficiary_id` (`ben_…`) | `display_name`, `bank_country`, `account_last4`, `previous_account_last4`, `last_changed_at`, `change_count`, `verified_at`, `verification_method` |
| `CollectionIntent` | `intent_id` (`col_…`) | `expected_amount`, `reference`, `expires_at`, `status`, `attributed_amount`, `provider_event_id` |
| `PaymentInstruction` | `payment_id` (`pay_…`) | `amount`, `purpose_code`, `business_instruction_id`, `idempotency_key`, `state`, `required_approvals`, `approval_decision_ids`, `required_verifications`, `completed_verifications`, `intervention_level`, `case_ids` |
| `RiskAssessment` | `assessment_id` (`ra_…`) | `band`, `score`, `signals`, `rules_version`, `evidence_complete`, `missing_evidence_kinds` |
| `EvidenceItem` | `evidence_id` (`ev_…`) | `kind`, `title`, `issuer`, `issued_at`, `checksum`, `location`, `excerpt`, `status`, `structured_facts` |
| `ReviewCase` | `case_id` (`case_…`) | `kind`, `priority`, `state`, `sla_due_at`, `owner`, `signal_ids`, `closure_reason` |
| `ApprovalDecision` | `decision_id` (`dec_…`) | `action`, `actor_role`, `actor_id`, `reason_code`, `note`, `ai_brief_id`, `agreed_with_ai` |
| `SettlementRecord` | `settlement_id` (`stl_…`) | `gross`, `fee`, `net`, `value_date`, `provider_reference`, `bank_reference` |
| `ExceptionCase` | `exception_id` (`exc_…`) | `exception_type`, `owner`, `due_at`, `state`, `difference`, `resolution_code` |
| `AuditEvent` | `entry_id` (`aud_…`) | `seq`, `actor_role`, `actor_id`, `action`, `object_type`, `object_id`, `summary`, `previous_hash`, `entry_hash` |

## Vocabularies

**KYB states** `draft → submitted → needs_information → approved / rejected`

**Payment states** `created → awaiting_intervention → awaiting_approval →
approved → submitted → accepted → settled`, with `failed`, `returned`,
`cancelled` as alternatives. Illegal transitions raise.

**Risk bands** `low` · `medium` · `high` · `critical` (score thresholds 20/45/70).

**Evidence kinds** `invoice`, `purchase_order`, `contract`, `bank_letter`,
`beneficiary_change_authorisation`, `incorporation_document`,
`ownership_declaration`, `official_source`, `callback_record`,
`provider_statement`.

**Exception types** `timing`, `fee`, `fx`, `duplicate`, `missing_record`,
`amount`, `beneficiary`, `state` — each with an owner and an SLA.

**Ledger buckets** `available`, `pending`, `reserved`, `payable`, plus
`fx_suspense` and `external`. They are separate accounts, not flags, so moving
between them is a journal entry a reader can see.

## Money

`Money(minor_units: int, currency: str)`. Floats are refused at construction, in
`from_major`, in `multiply` and in `convert`. Currency exponents are data
(`JPY` 0, `BHD` 3), not an assumed 2. Every conversion returns its rounding
remainder so the cent that rounding creates is recorded rather than absorbed.
