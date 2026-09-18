/* The console: one entry point, seven sections, one payment traceable through
 * all of them.
 *
 * The navigation is the product argument. Before the merge a reader had to open
 * four demos and take on trust that they described one operation. Here the same
 * `payment_id` appears in Payments, in Risk, in Evidence, in Reconciliation and
 * in the Audit Log, because there is one of it.
 */
import { useEffect, useMemo, useState } from "react";
import { loadSnapshot } from "./data";
import type {
  AmlCaseView,
  CaseView,
  PaymentView,
  SectionId,
  Snapshot,
  TypologyView,
} from "./types";

const SECTIONS: { id: SectionId; label: string; blurb: string }[] = [
  { id: "overview", label: "Overview", blurb: "What happened, and what the platform refuses to do" },
  { id: "businesses", label: "Businesses & KYB", blurb: "Entities, evidence and approval state" },
  { id: "payments", label: "Payments & Treasury", blurb: "Instructions, controls, balances" },
  { id: "risk", label: "Risk & Compliance", blurb: "Signals, cases, queue capacity" },
  { id: "evidence", label: "Evidence & Cases", blurb: "Documents, citations, what is missing" },
  { id: "reconciliation", label: "Reconciliation", blurb: "Three views of the same money" },
  { id: "audit", label: "Audit Log", blurb: "Hash-chained record of every consequential act" },
];

const LEVEL_WORDS = ["no intervention", "reminder", "reflect", "verify", "stop"];

function Banner({ text }: { text: string }) {
  return <p className="banner">{text}</p>;
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className={`stat ${tone ?? ""}`}>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

function Pill({ text, tone }: { text: string; tone?: string }) {
  return <span className={`pill ${tone ?? ""}`}>{text}</span>;
}

function stateTone(state: string): string {
  if (state === "settled") return "good";
  if (state === "failed" || state === "returned") return "bad";
  if (state.startsWith("awaiting")) return "warn";
  return "";
}

function levelTone(level: number | null): string {
  if (level === null) return "";
  if (level >= 4) return "bad";
  if (level >= 2) return "warn";
  return "good";
}

/* --- sections ---------------------------------------------------------- */

function Overview({ snapshot, onOpen }: { snapshot: Snapshot; onOpen: (id: string) => void }) {
  const o = snapshot.overview;
  return (
    <>
      <div className="stats">
        <Stat label="businesses onboarded" value={String(o.businesses)} />
        <Stat label="payments" value={String(o.payments)} />
        <Stat label="settled" value={String(o.settled_payments)} tone="good" />
        <Stat label="open cases" value={String(o.open_cases)} tone={o.open_cases ? "warn" : ""} />
        <Stat label="open exceptions" value={String(o.open_exceptions)} />
        <Stat label="events published" value={String(o.events)} />
        <Stat label="audit entries" value={String(o.audit_entries)} />
        <Stat
          label="copilot refusals"
          value={String(o.ai_refusals)}
          tone={o.ai_refusals ? "good" : ""}
        />
        <Stat label="alerts today" value={String(snapshot.aml.run.raw_alerts)} />
        <Stat label="cases opened" value={String(snapshot.aml.run.within_capacity)} tone="good" />
        <Stat label="waiting, not cleared" value={String(snapshot.aml.run.backlog)} tone="warn" />
      </div>

      <section className="card">
        <h3>The payment this platform was built to handle</h3>
        <ol className="transcript">
          {snapshot.demo_transcript.map((line, index) => (
            <li key={index}>{line}</li>
          ))}
        </ol>
        {o.flagship_payment_id ? (
          <button className="link" onClick={() => onOpen(o.flagship_payment_id)}>
            Open {o.flagship_payment_id} →
          </button>
        ) : null}
      </section>

      <section className="card">
        <h3>What the copilot may do — and what it has no code path to do</h3>
        <div className="two-up">
          <div>
            <h4 className="good">Permitted</h4>
            <ul>
              {snapshot.ai_boundary.allowed.map((action) => (
                <li key={action}>
                  <code>{action}</code>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="bad">Refused</h4>
            <ul>
              <li>approve a KYB case</li>
              <li>change the ledger</li>
              <li>execute FX</li>
              <li>submit or release a payment</li>
              <li>clear an AML alert</li>
              <li>close an investigation or an exception</li>
            </ul>
          </div>
        </div>
        <p className="note">{snapshot.ai_boundary.note}</p>
      </section>
    </>
  );
}

function Businesses({ snapshot }: { snapshot: Snapshot }) {
  return (
    <>
      {snapshot.businesses.map((business) => (
        <section className="card" key={business.business_id}>
          <header className="card-head">
            <div>
              <h3>{business.legal_name}</h3>
              <p className="muted">
                UEN {business.uen} · {business.entity_country} · <code>{business.business_id}</code>
              </p>
            </div>
            <Pill
              text={business.review_status}
              tone={business.review_status === "approved" ? "good" : "warn"}
            />
          </header>
          <dl className="kv">
            <div>
              <dt>Submitted</dt>
              <dd>{business.submitted_at.slice(0, 10)}</dd>
            </div>
            <div>
              <dt>Decided</dt>
              <dd>
                {business.decided_at ? `${business.decided_at.slice(0, 10)} by ${business.decided_by}` : "—"}
              </dd>
            </div>
            <div>
              <dt>Missing evidence</dt>
              <dd>{business.missing_evidence.join(", ") || "none"}</dd>
            </div>
            <div>
              <dt>Available balance</dt>
              <dd>{business.balances.available?.display ?? "—"}</dd>
            </div>
          </dl>
          <p className="note">
            Approval is refused while a required document is absent — the button that would produce
            an approval resting on nothing does not exist.
          </p>
        </section>
      ))}

      <section className="card">
        <h3>Counterparties</h3>
        <table>
          <thead>
            <tr>
              <th>Supplier</th>
              <th>Account</th>
              <th>Last changed</th>
              <th>Verification</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.beneficiaries.map((beneficiary) => (
              <tr key={beneficiary.beneficiary_id}>
                <td>
                  {beneficiary.display_name}
                  <br />
                  <code className="muted">{beneficiary.beneficiary_id}</code>
                </td>
                <td>
                  …{beneficiary.account_last4}
                  {beneficiary.previous_account_last4 ? (
                    <span className="muted"> (was …{beneficiary.previous_account_last4})</span>
                  ) : null}
                </td>
                <td>{beneficiary.last_changed_at?.slice(0, 10) ?? "never"}</td>
                <td>
                  <Pill
                    text={beneficiary.verification_is_current ? "current" : "not current"}
                    tone={beneficiary.verification_is_current ? "good" : "warn"}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function PaymentCard({ view, onOpen }: { view: PaymentView; onOpen: (id: string) => void }) {
  const p = view.payment;
  return (
    <button className="row-card" onClick={() => onOpen(p.payment_id)}>
      <span className="row-main">
        <strong>{p.amount_display}</strong> to {view.beneficiary.display_name}
        <span className="muted"> · {p.business_instruction_id}</span>
      </span>
      <span className="row-tags">
        <Pill text={p.state} tone={stateTone(p.state)} />
        {p.intervention_level !== null ? (
          <Pill
            text={`L${p.intervention_level} ${LEVEL_WORDS[p.intervention_level]}`}
            tone={levelTone(p.intervention_level)}
          />
        ) : null}
        {view.assessment ? <Pill text={view.assessment.band} /> : null}
      </span>
    </button>
  );
}

function PaymentDetail({ view }: { view: PaymentView }) {
  const p = view.payment;
  return (
    <>
      <section className="card">
        <header className="card-head">
          <div>
            <h3>
              {p.amount_display} → {view.beneficiary.display_name}
            </h3>
            <p className="muted">
              <code>{p.payment_id}</code> · {p.purpose_code} · instruction {p.business_instruction_id}
            </p>
          </div>
          <Pill text={p.state} tone={stateTone(p.state)} />
        </header>
        <dl className="kv">
          <div>
            <dt>Payer</dt>
            <dd>{view.business.legal_name}</dd>
          </div>
          <div>
            <dt>Beneficiary account</dt>
            <dd>
              …{view.beneficiary.account_last4}
              {view.beneficiary.previous_account_last4
                ? ` (changed from …${view.beneficiary.previous_account_last4})`
                : ""}
            </dd>
          </div>
          <div>
            <dt>Approvals</dt>
            <dd>
              {p.approvals.length} of {p.required_approvals}
            </dd>
          </div>
          <div>
            <dt>Outstanding verifications</dt>
            <dd>{p.outstanding_verifications.join(", ") || "none"}</dd>
          </div>
        </dl>
      </section>

      {view.intervention ? (
        <section className="card">
          <header className="card-head">
            <h3>Pre-payment intervention</h3>
            <Pill
              text={`level ${view.intervention.selected_level} — ${
                LEVEL_WORDS[view.intervention.selected_level]
              }`}
              tone={levelTone(view.intervention.selected_level)}
            />
          </header>
          <p>{view.intervention.policy}</p>
          <dl className="kv">
            <div>
              <dt>Amount tier</dt>
              <dd>
                {view.intervention.amount_tier} (floor {view.intervention.amount_floor})
              </dd>
            </div>
            <div>
              <dt>Payee verified</dt>
              <dd>{view.intervention.payee_known ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Drivers</dt>
              <dd>{view.intervention.drivers.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt>Required of a person</dt>
              <dd>
                {view.intervention.required_approvals} approver(s);{" "}
                {view.intervention.required_verifications.join(", ") || "no verification"}
              </dd>
            </div>
          </dl>
          <p className="note">Why not weaker: {view.intervention.why_not_weaker}</p>
          <p className="note">Why not stronger: {view.intervention.why_not_stronger}</p>
        </section>
      ) : null}

      {view.assessment ? (
        <section className="card">
          <header className="card-head">
            <h3>Risk assessment</h3>
            <Pill text={`${view.assessment.band} · score ${view.assessment.score}`} />
          </header>
          <ul className="signals">
            {view.assessment.signals.map((signal) => (
              <li key={signal.signal_id}>
                <code>{signal.signal_id}</code> <Pill text={signal.severity} />
                <p>{signal.summary}</p>
              </li>
            ))}
          </ul>
          <p className="note">
            Deterministic rules version {view.assessment.rules_version}. No model participates in
            detection, prioritisation or routing.
          </p>
        </section>
      ) : null}

      <section className="card">
        <header className="card-head">
          <h3>Evidence</h3>
          <Pill
            text={view.evidence.complete ? "complete" : `${view.evidence.missing_kinds.length} missing`}
            tone={view.evidence.complete ? "good" : "warn"}
          />
        </header>
        <ul className="evidence">
          {view.evidence_items.map((item) => (
            <li key={item.evidence_id}>
              <strong>{item.title}</strong> <span className="muted">· {item.issuer}</span>
              <p>{item.excerpt}</p>
              <p className="muted mono">
                {item.evidence_id} · {item.location} · sha256 {item.checksum.slice(0, 12)}…
              </p>
            </li>
          ))}
        </ul>
        {view.evidence.missing_kinds.length ? (
          <p className="note warn-text">Still missing: {view.evidence.missing_kinds.join(", ")}</p>
        ) : null}
      </section>

      {view.cases.length ? (
        <section className="card">
          <h3>Cases</h3>
          {view.cases.map((item) => (
            <p key={item.case_id}>
              <code>{item.case_id}</code> · priority {item.priority} · {item.state}
              {item.closure_reason ? ` · ${item.closure_reason}` : ""}
              <br />
              {item.title}
            </p>
          ))}
        </section>
      ) : null}

      {view.settlement ? (
        <section className="card">
          <h3>Settlement</h3>
          <dl className="kv">
            <div>
              <dt>Gross</dt>
              <dd>{view.settlement.gross}</dd>
            </div>
            <div>
              <dt>Fee</dt>
              <dd>{view.settlement.fee}</dd>
            </div>
            <div>
              <dt>Net</dt>
              <dd>{view.settlement.net}</dd>
            </div>
            <div>
              <dt>Provider reference</dt>
              <dd>{view.settlement.provider_reference}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      <section className="card">
        <h3>Timeline</h3>
        <ol className="timeline">
          {view.timeline.map((event) => (
            <li key={event.event_id}>
              <span className="mono muted">{event.occurred_at.slice(0, 16).replace("T", " ")}</span>
              <code>{event.type}</code>
              <span className="muted">
                {event.actor_role}/{event.actor_id}
              </span>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}

function Payments({
  snapshot,
  selected,
  onOpen,
}: {
  snapshot: Snapshot;
  selected: string | null;
  onOpen: (id: string | null) => void;
}) {
  const view = snapshot.payments.find((item) => item.payment.payment_id === selected);
  if (view) {
    return (
      <>
        <button className="link" onClick={() => onOpen(null)}>
          ← all payments
        </button>
        <PaymentDetail view={view} />
      </>
    );
  }
  const balances = snapshot.businesses[0]?.balances ?? {};
  return (
    <>
      <div className="stats">
        {Object.entries(balances).map(([bucket, money]) => (
          <Stat key={bucket} label={bucket} value={money?.display ?? "—"} />
        ))}
        <Stat
          label="ledger balanced"
          value={snapshot.ledger.balanced ? "yes" : "no"}
          tone={snapshot.ledger.balanced ? "good" : "bad"}
        />
        <Stat label="duplicate attempts refused" value={String(snapshot.overview.duplicate_attempts)} />
      </div>
      <section className="card">
        <h3>Payment instructions</h3>
        {snapshot.payments.map((item) => (
          <PaymentCard key={item.payment.payment_id} view={item} onOpen={onOpen} />
        ))}
      </section>
      <section className="card">
        <h3>Ledger journals</h3>
        <table>
          <thead>
            <tr>
              <th>Posted</th>
              <th>Description</th>
              <th>Legs</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.ledger.journals.map((journal) => (
              <tr key={journal.journal_id}>
                <td className="mono">{journal.posted_at.slice(0, 10)}</td>
                <td>{journal.description}</td>
                <td className="mono">
                  {journal.legs.map((leg) => (
                    <div key={leg.account}>
                      {leg.account} {leg.amount?.display}
                    </div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="note">
          Every journal balances per currency or it is refused whole. A correction is a reversal;
          nothing is edited.
        </p>
      </section>
    </>
  );
}

function CaseRow({ item, onOpen }: { item: CaseView; onOpen: (id: string) => void }) {
  return (
    <div className="row-card static">
      <span className="row-main">
        <strong>P{item.priority}</strong> {item.title}
        <br />
        <span className="muted mono">
          {item.case_id} · due {item.sla_due_at.slice(0, 16).replace("T", " ")}
        </span>
      </span>
      <span className="row-tags">
        <Pill text={item.state} tone={item.state === "closed" ? "good" : "warn"} />
        {item.payment_id ? (
          <button className="link" onClick={() => onOpen(item.payment_id as string)}>
            payment →
          </button>
        ) : null}
      </span>
    </div>
  );
}

function usd(minor: number): string {
  return `${(minor / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })} USD`;
}

function bandTone(band: string): string {
  if (band === "critical") return "bad";
  if (band === "high") return "warn";
  return "";
}

function AmlCaseCard({ item }: { item: AmlCaseView }) {
  const [open, setOpen] = useState(false);
  const top = [...item.contributions].sort((a, b) => b.points - a.points).slice(0, 4);
  return (
    <div className="row-card static aml-case">
      <div className="aml-case-body">
        <button className="aml-case-head" onClick={() => setOpen(!open)}>
          <span>
            <strong>P{item.queue_position}</strong> {item.subject_name}
            <span className="muted"> · {item.typology_keys.join(", ")}</span>
            <br />
            <span className="muted mono">
              {item.alert_count} alert(s) · {item.transfer_count} transfers · {usd(item.total_usd_minor)}
              {item.duplicates_absorbed ? ` · ${item.duplicates_absorbed} duplicate observation(s) absorbed` : ""}
            </span>
          </span>
          <span className="row-tags">
            <Pill text={`${item.priority_band} ${item.priority_score.toFixed(3)}`} tone={bandTone(item.priority_band)} />
            <span className="muted">{open ? "hide" : "why"}</span>
          </span>
        </button>

        <div className="factors">
          {top.map((factor) => (
            <div key={factor.factor} className="factor" title={factor.detail}>
              <span className="factor-label">{factor.label}</span>
              <span className="factor-bar">
                <span style={{ width: `${Math.round((factor.points / 0.2) * 100)}%` }} />
              </span>
              <span className="factor-points mono">+{factor.points.toFixed(3)}</span>
            </div>
          ))}
        </div>

        {open ? (
          <div className="aml-detail">
            <p className="note">{item.merge_rationale}</p>
            <h4>All eight priority factors</h4>
            <table>
              <tbody>
                {item.contributions.map((factor) => (
                  <tr key={factor.factor}>
                    <td>{factor.label}</td>
                    <td className="muted">{factor.detail}</td>
                    <td className="mono">
                      {factor.raw.toFixed(2)} × {factor.weight} = {factor.points.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {item.alerts.map((alert) => (
              <div key={alert.alert_id} className="alert">
                <p>
                  <code>{alert.alert_id}</code> <Pill text={alert.severity} tone={bandTone(alert.severity)} />
                </p>
                <p>{alert.explanation}</p>
                <h4>What would argue against this</h4>
                <ul>
                  {alert.counter_evidence.map((line) => (
                    <li key={line} className="muted">
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function TypologyTable({
  typologies,
  recall,
}: {
  typologies: TypologyView[];
  recall: Record<string, { mean: number; stdev: number }> | null;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Typology</th>
          <th>Fires when</th>
          <th>Severity</th>
          <th>Recall</th>
        </tr>
      </thead>
      <tbody>
        {typologies.map((typology) => {
          const measured = recall?.[typology.typology_id];
          return (
            <tr key={typology.typology_id}>
              <td>
                <strong>{typology.title}</strong>
                <br />
                <span className="muted">{typology.question}</span>
              </td>
              <td className="mono muted">
                {Object.entries(typology.thresholds)
                  .map(([key, value]) => `${key}=${value}`)
                  .join(", ")}
              </td>
              <td>
                <Pill text={typology.severity} tone={bandTone(typology.severity)} />
              </td>
              <td className="mono">
                {measured ? `${measured.mean.toFixed(3)} ± ${measured.stdev.toFixed(3)}` : "—"}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function Risk({ snapshot, onOpen }: { snapshot: Snapshot; onOpen: (id: string) => void }) {
  const aml = snapshot.aml;
  const headline = aml.evaluation?.headline ?? null;
  const [showRules, setShowRules] = useState(false);

  const families = useMemo(() => {
    const grouped = new Map<string, typeof aml.rules>();
    for (const rule of aml.rules) {
      grouped.set(rule.family, [...(grouped.get(rule.family) ?? []), rule]);
    }
    return [...grouped.entries()];
  }, [aml.rules]);

  return (
    <>
      <div className="stats">
        <Stat label="monitored transfers" value={aml.monitored_transfers.toLocaleString()} />
        <Stat label="raw alerts" value={String(aml.run.raw_alerts)} />
        <Stat label="after deduplication" value={String(aml.run.deduplicated_alerts)} />
        <Stat label="cases" value={String(aml.run.cases)} />
        <Stat label="review capacity" value={String(aml.run.capacity)} tone="good" />
        <Stat label="backlog" value={String(aml.run.backlog)} tone="warn" />
      </div>

      <section className="card">
        <header className="card-head">
          <div>
            <h3>Investigation queue</h3>
            <p className="muted">
              {aml.run.raw_alerts} alerts → {aml.run.deduplicated_alerts} after deduplication →{" "}
              {aml.run.cases} cases → {aml.run.capacity} a team of this size can open today.
            </p>
          </div>
          <Pill text={`capacity ${aml.run.capacity}`} />
        </header>
        {aml.queue.map((item) => (
          <AmlCaseCard key={item.case_key} item={item} />
        ))}
      </section>

      <section className="card">
        <h3 className="warn-text">Below the capacity line — {aml.backlog.length} case(s), not cleared</h3>
        <p className="note">{aml.backlog_note}</p>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Subject</th>
              <th>Typologies</th>
              <th>Priority</th>
            </tr>
          </thead>
          <tbody>
            {aml.backlog.map((item) => (
              <tr key={item.case_key}>
                <td className="mono">P{item.queue_position}</td>
                <td>{item.subject_name}</td>
                <td className="muted">{item.typology_keys.join(", ")}</td>
                <td className="mono">
                  {item.priority_band} {item.priority_score.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <header className="card-head">
          <h3>Six typologies, deterministic, no model</h3>
          {headline ? (
            <Pill
              text={`recall ${headline.recall_clear.mean.toFixed(3)} clear / ${headline.recall_borderline.mean.toFixed(
                3
              )} borderline`}
            />
          ) : null}
        </header>
        <TypologyTable typologies={aml.typologies} recall={aml.evaluation?.recall_by_typology ?? null} />
        {headline ? (
          <p className="note">
            Alert precision is {headline.raw_alert_precision.mean.toFixed(3)} raw and{" "}
            {headline.precision_at_capacity.mean.toFixed(3)} at review capacity — the ordering is the
            product. {headline.planted_patterns_left_in_backlog.mean.toFixed(0)} planted patterns are
            sitting in the backlog, which is a headline row rather than an omission. Synthetic
            evaluation over {aml.evaluation?.dataset.seeds.length} seeded worlds; the population is
            deliberately enriched, so neither figure transfers to production traffic.
          </p>
        ) : null}
      </section>

      <section className="card">
        <header className="card-head">
          <div>
            <h3>Payment-review cases</h3>
            <p className="muted">Opened by the payment controls, not by monitoring.</p>
          </div>
          <Pill text={`capacity ${snapshot.cases.capacity}`} />
        </header>
        {snapshot.cases.within_capacity.map((item) => (
          <CaseRow key={item.case_id} item={item} onOpen={onOpen} />
        ))}
        {snapshot.cases.within_capacity.length === 0 ? (
          <p className="note">No open payment-review case in this run.</p>
        ) : null}
      </section>

      <section className="card">
        <header className="card-head">
          <h3>{aml.rules.length} deterministic rules over one payment</h3>
          <button className="link" onClick={() => setShowRules(!showRules)}>
            {showRules ? "hide" : "show catalogue"}
          </button>
        </header>
        <p className="note">
          A signal is a reason to investigate, not a finding of wrongdoing. Every rule names the
          fields it read, so an operator can argue with it.
        </p>
        {showRules
          ? families.map(([family, rules]) => (
              <div key={family}>
                <h4>{family.replace("_", " ")}</h4>
                <table>
                  <tbody>
                    {rules.map((rule) => (
                      <tr key={rule.rule_id}>
                        <td className="mono">{rule.rule_id}</td>
                        <td>
                          <strong>{rule.title}</strong>
                          <br />
                          <span className="muted">{rule.reason}</span>
                        </td>
                        <td>
                          <Pill text={rule.severity} tone={bandTone(rule.severity)} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))
          : null}
      </section>
    </>
  );
}


function Evidence({ snapshot, onOpen }: { snapshot: Snapshot; onOpen: (id: string) => void }) {
  return (
    <section className="card">
      <h3>Evidence register</h3>
      <p className="note">
        Every item carries an issuer, a location inside the source, an excerpt and a SHA-256 of that
        excerpt. A citation the copilot produces must resolve to one of these identifiers or the
        statement is dropped and counted.
      </p>
      <table>
        <thead>
          <tr>
            <th>Document</th>
            <th>Kind</th>
            <th>Linked to</th>
            <th>Checksum</th>
          </tr>
        </thead>
        <tbody>
          {snapshot.evidence.map((item) => (
            <tr key={item.evidence_id}>
              <td>
                <strong>{item.title}</strong>
                <br />
                <span className="muted">{item.excerpt}</span>
                <br />
                <code className="muted">{item.evidence_id}</code>
              </td>
              <td>{item.kind}</td>
              <td>
                {item.payment_id ? (
                  <button className="link" onClick={() => onOpen(item.payment_id as string)}>
                    {item.payment_id}
                  </button>
                ) : (
                  <span className="muted">{item.business_id ?? item.beneficiary_id ?? "—"}</span>
                )}
              </td>
              <td className="mono">{item.checksum.slice(0, 12)}…</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function Reconciliation({ snapshot, onOpen }: { snapshot: Snapshot; onOpen: (id: string) => void }) {
  const { settlements, exceptions } = snapshot.reconciliation;
  return (
    <>
      <section className="card">
        <h3>Settlements</h3>
        <table>
          <thead>
            <tr>
              <th>Payment</th>
              <th>Gross</th>
              <th>Fee</th>
              <th>Net</th>
              <th>Provider reference</th>
            </tr>
          </thead>
          <tbody>
            {settlements.map((item) => (
              <tr key={item.settlement_id}>
                <td>
                  <button className="link" onClick={() => onOpen(item.payment_id)}>
                    {item.payment_id}
                  </button>
                </td>
                <td>{item.gross?.display}</td>
                <td>{item.fee?.display}</td>
                <td>{item.net?.display}</td>
                <td className="mono">{item.provider_reference}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="note">
          The product ledger, the provider advice and the bank statement are compared as three
          independent views. A run with an unexplained difference cannot be marked reconciled — the
          call raises rather than warning.
        </p>
      </section>

      <section className="card">
        <h3>Exceptions</h3>
        {exceptions.length ? (
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Summary</th>
                <th>Owner</th>
                <th>Due</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {exceptions.map((item) => (
                <tr key={item.exception_id}>
                  <td>
                    <Pill text={item.exception_type} tone="warn" />
                  </td>
                  <td>{item.summary}</td>
                  <td>{item.owner}</td>
                  <td className="mono">{item.due_at.slice(0, 16).replace("T", " ")}</td>
                  <td>{item.state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="note">
            No open exception in this run. Every difference the engine can find is typed, owned and
            given a due time; there is no untyped “unreconciled” bucket.
          </p>
        )}
      </section>
    </>
  );
}

function Audit({ snapshot }: { snapshot: Snapshot }) {
  const o = snapshot.overview;
  return (
    <>
      <div className="stats">
        <Stat label="entries" value={String(o.audit_entries)} />
        <Stat
          label="chain"
          value={o.audit_status}
          tone={o.audit_status === "verified" ? "good" : "bad"}
        />
        <Stat label="copilot refusals" value={String(o.ai_refusals)} />
        <Stat label="quarantined events" value={String(o.quarantined_events)} />
      </div>
      <section className="card">
        <h3>Every consequential act, in one chain</h3>
        <p className="note">{o.audit_summary}</p>
        <p className="note">
          What this proves and does not prove: it makes a partial edit detectable. Someone who can
          rewrite the whole table can recompute every link. Real non-repudiation needs the head
          anchored where the editor cannot reach, which this project does not do.
        </p>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>When</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Summary</th>
              <th>Hash</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.audit.map((entry) => (
              <tr key={entry.entry_id}>
                <td className="mono">{entry.seq}</td>
                <td className="mono">{entry.occurred_at.slice(0, 16).replace("T", " ")}</td>
                <td>
                  <span className="muted">{entry.actor_role}</span>
                  <br />
                  {entry.actor_id}
                </td>
                <td>
                  <code>{entry.action}</code>
                </td>
                <td>{entry.summary}</td>
                <td className="mono muted">{entry.entry_hash.slice(0, 10)}…</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

/* --- shell -------------------------------------------------------------- */

export default function App() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [source, setSource] = useState<"api" | "static">("static");
  const [error, setError] = useState<string | null>(null);
  const [section, setSection] = useState<SectionId>("overview");
  const [selectedPayment, setSelectedPayment] = useState<string | null>(null);

  useEffect(() => {
    loadSnapshot()
      .then(({ snapshot: data, source: from }) => {
        setSnapshot(data);
        setSource(from);
      })
      .catch((cause: unknown) => setError(String(cause)));
  }, []);

  function openPayment(id: string | null) {
    setSelectedPayment(id);
    if (id) setSection("payments");
  }

  if (error) return <main className="shell"><p className="banner bad">{error}</p></main>;
  if (!snapshot) return <main className="shell"><p className="muted">Loading…</p></main>;

  return (
    <div className="shell">
      <aside>
        <h1>
          Corridor<span>OS</span>
        </h1>
        <p className="muted small">China–Singapore payment operations</p>
        <nav>
          {SECTIONS.map((item) => (
            <button
              key={item.id}
              className={item.id === section ? "active" : ""}
              onClick={() => {
                setSection(item.id);
                if (item.id !== "payments") setSelectedPayment(null);
              }}
            >
              <span>{item.label}</span>
              <small>{item.blurb}</small>
            </button>
          ))}
        </nav>
        <p className="muted small">
          data source: {source === "api" ? "live API" : "published snapshot"}
          <br />
          generated {snapshot.generated_at.slice(0, 10)}
        </p>
      </aside>

      <main>
        <Banner text={snapshot.disclaimer} />
        {section === "overview" && <Overview snapshot={snapshot} onOpen={openPayment} />}
        {section === "businesses" && <Businesses snapshot={snapshot} />}
        {section === "payments" && (
          <Payments snapshot={snapshot} selected={selectedPayment} onOpen={openPayment} />
        )}
        {section === "risk" && <Risk snapshot={snapshot} onOpen={openPayment} />}
        {section === "evidence" && <Evidence snapshot={snapshot} onOpen={openPayment} />}
        {section === "reconciliation" && (
          <Reconciliation snapshot={snapshot} onOpen={openPayment} />
        )}
        {section === "audit" && <Audit snapshot={snapshot} />}
      </main>
    </div>
  );
}
