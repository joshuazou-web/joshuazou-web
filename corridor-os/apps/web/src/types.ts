/* The shapes the console reads. They mirror `corridoros.scenario.snapshot`,
 * which is a projection of the platform's own objects — so a change in the
 * domain surfaces here as a type error rather than as an empty panel. */

export interface MoneyView {
  minor_units: number;
  currency: string;
  display: string;
}

export interface SignalView {
  signal_id: string;
  severity: string;
  summary: string;
  facts: Record<string, unknown>;
}

export interface InterventionView {
  payment_id: string;
  selected_level: number;
  amount_tier: string;
  amount_floor: number;
  payee_known: boolean;
  drivers: string[];
  signal_ids: string[];
  required_approvals: number;
  required_verifications: string[];
  policy: string;
  why_not_weaker: string;
  why_not_stronger: string;
  engine_version: string;
}

export interface EvidenceView {
  evidence_id: string;
  kind: string;
  title: string;
  issuer: string;
  issued_at: string | null;
  location: string;
  excerpt: string;
  checksum: string;
  business_id: string | null;
  payment_id: string | null;
  beneficiary_id: string | null;
  status: string;
}

export interface PaymentView {
  payment: {
    payment_id: string;
    business_id: string;
    beneficiary_id: string;
    amount_display: string;
    purpose_code: string;
    business_instruction_id: string;
    state: string;
    intervention_level: number | null;
    required_approvals: number;
    approvals: string[];
    required_verifications: string[];
    completed_verifications: string[];
    outstanding_verifications: string[];
    blocking_cases: string[];
    case_ids: string[];
    created_at: string;
    settled_at: string | null;
  };
  business: { business_id: string; legal_name: string; uen: string; review_status: string };
  beneficiary: {
    beneficiary_id: string;
    display_name: string;
    bank_country: string;
    account_last4: string;
    previous_account_last4: string | null;
    last_changed_at: string | null;
    verified_at: string | null;
    verification_is_current: boolean;
  };
  assessment: {
    assessment_id: string;
    band: string;
    score: number;
    rules_version: string;
    signals: SignalView[];
  } | null;
  intervention: InterventionView | null;
  evidence: {
    subject_id: string;
    evidence_ids: string[];
    required_kinds: string[];
    missing_kinds: string[];
    complete: boolean;
  };
  evidence_items: EvidenceView[];
  cases: {
    case_id: string;
    kind: string;
    title: string;
    priority: number;
    state: string;
    sla_due_at: string;
    closure_reason: string | null;
  }[];
  settlement: {
    settlement_id: string;
    gross: string;
    fee: string;
    net: string;
    value_date: string;
    provider_reference: string;
  } | null;
  timeline: {
    event_id: string;
    seq: number;
    type: string;
    occurred_at: string;
    actor_role: string;
    actor_id: string;
    subject: Record<string, string>;
    payload: Record<string, unknown>;
  }[];
  audit: {
    entry_id: string;
    seq: number;
    occurred_at: string;
    actor_role: string;
    actor_id: string;
    action: string;
    summary: string;
    entry_hash: string;
  }[];
}

export interface BusinessView {
  business_id: string;
  legal_name: string;
  uen: string;
  entity_country: string;
  review_status: string;
  submitted_at: string;
  decided_at: string | null;
  decided_by: string | null;
  expected_monthly_volume: MoneyView | null;
  missing_evidence: string[];
  evidence_ids: string[];
  balances: Record<string, MoneyView | null>;
}

export interface CaseView {
  case_id: string;
  kind: string;
  title: string;
  priority: number;
  state: string;
  sla_due_at: string;
  payment_id: string | null;
  signal_ids: string[];
  closure_reason: string | null;
}

export interface ContributionView {
  factor: string;
  label: string;
  raw: number;
  weight: number;
  points: number;
  detail: string;
}

export interface AmlAlertView {
  alert_id: string;
  typology_id: string;
  severity: string;
  subject_account: string;
  transfer_count: number;
  total_usd_minor: number;
  explanation: string;
  counter_evidence: string[];
  window_start: string;
  window_end: string;
}

export interface AmlCaseView {
  case_key: string;
  subject_account: string;
  subject_name: string;
  state: string;
  priority_score: number;
  priority_band: string;
  queue_position: number;
  within_capacity: boolean;
  sla_due_at: string | null;
  alert_count: number;
  duplicates_absorbed: number;
  typologies: string[];
  typology_keys: string[];
  max_severity: string;
  transfer_count: number;
  total_usd_minor: number;
  merge_rationale: string;
  contributions: ContributionView[];
  alerts: AmlAlertView[];
}

export interface TypologyView {
  typology_id: string;
  key: string;
  title: string;
  severity: string;
  question: string;
  thresholds: Record<string, number>;
  counter_evidence: string[];
}

export interface RuleView {
  rule_id: string;
  family: string;
  severity: string;
  title: string;
  reason: string;
  reads: string[];
  signal_id: string;
}

export interface Spread {
  mean: number;
  stdev: number;
  min: number;
  max: number;
  n_seeds: number;
}

export interface AmlSection {
  run: {
    run_at: string;
    raw_alerts: number;
    deduplicated_alerts: number;
    duplicates_removed: number;
    cases: number;
    capacity: number;
    within_capacity: number;
    backlog: number;
    aggregation_version: string;
  };
  monitored_transfers: number;
  monitored_accounts: number;
  platform_movements_in_feed: number;
  queue: AmlCaseView[];
  backlog: {
    case_key: string;
    subject_name: string;
    subject_account: string;
    priority_score: number;
    priority_band: string;
    queue_position: number;
    typology_keys: string[];
    alert_count: number;
  }[];
  backlog_note: string;
  typologies: TypologyView[];
  rules: RuleView[];
  planted_patterns: number;
  evaluation: {
    eval_version: string;
    typology_version: string;
    dataset: { seeds: number[]; transfers_per_seed: number; review_capacity: number; caveat: string };
    headline: Record<string, Spread>;
    recall_by_typology: Record<string, Spread>;
    boundary: string;
  } | null;
}

export interface Snapshot {
  generated_at: string;
  disclaimer: string;
  overview: {
    businesses: number;
    payments: number;
    settled_payments: number;
    open_cases: number;
    open_exceptions: number;
    events: number;
    audit_entries: number;
    audit_status: string;
    audit_head: string;
    audit_summary: string;
    ledger_balanced: boolean;
    ai_refusals: number;
    quarantined_events: number;
    duplicate_attempts: number;
    flagship_payment_id: string;
  };
  demo_transcript: string[];
  businesses: BusinessView[];
  beneficiaries: {
    beneficiary_id: string;
    display_name: string;
    bank_country: string;
    account_last4: string;
    previous_account_last4: string | null;
    last_changed_at: string | null;
    verified_at: string | null;
    verification_is_current: boolean;
    change_count: number;
  }[];
  payments: PaymentView[];
  cases: { within_capacity: CaseView[]; backlog: CaseView[]; capacity: number };
  evidence: EvidenceView[];
  ledger: {
    balanced: boolean;
    journals: {
      journal_id: string;
      posted_at: string;
      description: string;
      payment_id: string | null;
      legs: { account: string; amount: MoneyView | null; memo: string }[];
    }[];
  };
  reconciliation: {
    settlements: {
      settlement_id: string;
      payment_id: string;
      gross: MoneyView | null;
      fee: MoneyView | null;
      net: MoneyView | null;
      value_date: string;
      provider_reference: string;
    }[];
    exceptions: {
      exception_id: string;
      exception_type: string;
      summary: string;
      owner: string;
      state: string;
      opened_at: string;
      due_at: string;
      payment_id: string | null;
      difference: MoneyView | null;
      resolution_code: string | null;
    }[];
  };
  events: {
    event_id: string;
    seq: number;
    type: string;
    occurred_at: string;
    actor_role: string;
    actor_id: string;
    subject: Record<string, string>;
    payload: Record<string, unknown>;
  }[];
  quarantined_events: Record<string, unknown>[];
  audit: {
    entry_id: string;
    seq: number;
    occurred_at: string;
    actor_role: string;
    actor_id: string;
    action: string;
    object_type: string;
    object_id: string;
    summary: string;
    entry_hash: string;
    previous_hash: string;
  }[];
  aml: AmlSection;
  ai_boundary: {
    allowed: string[];
    refused_examples: Record<string, unknown>[];
    note: string;
  };
}

export type SectionId =
  | "overview"
  | "businesses"
  | "payments"
  | "risk"
  | "evidence"
  | "reconciliation"
  | "audit";
