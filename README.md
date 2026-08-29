<h1 align="center">Josh — Developer Experience & AI Engineering</h1>

<p align="center">
  Building bilingual developer tools, trustworthy AI demos, and reviewable agent workflows.<br>
  Singapore · NUS MSc Digital Financial Technology · Mandarin / English
</p>

<p align="center">
  <a href="mailto:zouzhihuajosh@outlook.com">Email</a> ·
  <a href="https://github.com/joshuazou-web?tab=repositories">Repositories</a> ·
  <a href="ABOUT_JOSH.md">Beyond the portfolio</a>
</p>

<img align="right" width="145" src="assets/avatar-josh-500.png" alt="Josh" />

## What I build

I turn unclear developer and product problems into runnable examples, explicit
system rules, and evidence that another person can verify.

- **Developer experience:** Python and TypeScript quick starts, API debugging,
  demos, technical documentation, evals, and failure analysis.
- **AI safety and reliability:** credential redaction, approval gates,
  deterministic fallbacks, rate controls, audit trails, and human review.
- **Bilingual communication:** Mandarin-first explanations with English parity
  for developers, product teams, founders, and regional communities.

I am currently completing an **MSc in Digital Financial Technology at the
National University of Singapore**, expected January 2027.

<br clear="right" />

## Featured builds

### 1. OpsSignal — AI-Assisted Operational Workload Intelligence

An operational analytics system for an internal Business Technology queue. It
turns an inconsistent multi-channel ticket feed into a versioned taxonomy, a
validated warehouse, a six-page dashboard, and an AI triage policy that routes
its own uncertainty to a human.

- **Definitions first:** taxonomy v1.1.0 — 6 dimensions, 51 values, 257 source
  aliases — each with a definition, a worked example, and the boundary case
  people actually confuse. It lives in code, the documentation is generated from
  it, and a test fails if the two drift apart.
- **Pipeline:** raw → staging → marts → audit on DuckDB. Idempotent, incremental,
  19 severity-tiered validation checks, and automatic rollback to the last good
  dataset on failure, proven by a fault-injection drill. 166 automated tests.
- **Analytics:** 21 mart tables covering backlog ageing, P50/P90 cycle time, SLA
  compliance and breach drivers, Pareto workload analysis, repeated-request
  clusters, and data-quality health — each metric defined exactly once, in SQL.
- **Classifier:** TF-IDF + logistic regression, 0.842 accuracy / 0.836 macro F1
  on a held-out split, at a confidence threshold selected on validation that
  auto-classifies 84% of tickets. Held-out agreement is 92.3% on auto-accepted
  tickets versus 50.0% on the review queue — the evidence that the policy sends
  the harder work to a person rather than into the metrics.
- **Human review:** append-only audit trail; corrections outrank the model,
  survive refreshes and retrains, and flow back into the reported numbers.
- **Data boundary:** every ticket is **synthetic** and labelled as such on each
  dashboard page. The single efficiency figure is an explicitly assumption-based
  estimate, never presented as a business benefit.

**[Source and quick start](https://github.com/joshuazou-web/opssignal)** ·
**[Case study](https://github.com/joshuazou-web/opssignal/blob/main/CASE_STUDY.md)**

### 2. DecisiveEval — Coding-Agent Evaluation Stability

An auditable Python research system for testing whether a Coding Agent decision
survives defensible changes to grading, runtime, failure handling, cost, and
latency policy. The v0.1 checkpoint ships a real CLI, immutable evidence
receipts, repeated-run/bootstrap paths, 26 public JSON Schemas, and 103 passing
tests. It also publishes failed experiments and explicitly leaves real-world
hypothesis validation open rather than claiming a premature result.

**[Source, protocol, and quick start](https://github.com/joshuazou-web/decisive-eval)**
### 3. DEBUG.CN — Mandarin OpenAI API Debugging Copilot

A bilingual, safety-first workbench that turns OpenAI API and SDK failures into
reviewable evidence, root causes, minimal fixes, and verification checks.

- React + FastAPI with server-side secret redaction and a deterministic fallback.
- Eight error categories, 24 backend tests, and a public 20-case eval passing 20/20.
- Source-level controls: 3 live calls/client/minute, 25/process/UTC day,
  1,600 output tokens, 30-second upstream timeout, and `store=false`.
- **Validation boundary:** the Structured Outputs integration path is implemented;
  successful real-model validation remains pending account quota.

**[Source](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot)** ·
**[Public demo](https://ctkhkof0ez.feishuapp.com/app/app_17c3qmjxcq2)** ·
**[3-minute bilingual video](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot/releases/download/v0.1.0/DEBUG-CN-3min-bilingual-demo-subtitled.mp4)**

### 4. Agent Control Plane

A Python governance CLI for agent workflows with machine-checkable authority,
approval gates, append-only traces, resumable task folders, and reproducible
propose-check-execute-record-escalate examples.

**[Source and quick start](https://github.com/joshuazou-web/agent-control-plane)**

### 5. ThinkBeforeClick — Security Learning SaaS

A Singapore-localized security-learning product connecting learner feedback
with enterprise analytics and follow-up. A five-person team shipped an AWS
prototype; the course-project evaluation involved 23 participants and received
an Honourable Mention at a computing project showcase.

**[Case study](https://github.com/joshuazou-web/think-before-click-product-case)** ·
**[Safe demo](https://joshuazou-web.github.io/think-before-click-product-case/)**

### 6. Risk-Based DeFi Lending

A product and engineering case translating external risk signals into explicit
LTV, interest-rate, liquidation-threshold, and health-factor rules, backed by a
Python/Flask scoring service and documented trust boundaries.

**[Case study](https://github.com/joshuazou-web/risk-based-defi-lending-case-study)** ·
**[Interactive demo](https://joshuazou-web.github.io/risk-based-defi-lending-case-study/)**

<details>
<summary><strong>More product engineering work</strong></summary>

### Algorithmic FX Trading & Monitoring

An explainable trading-product workflow covering regime logic, causal
validation, turnover costs, monitoring, and fail-closed practice execution.

**[Case study](https://github.com/joshuazou-web/algorithmic-fx-product-case)** ·
**[Interactive demo](https://joshuazou-web.github.io/algorithmic-fx-product-case/)**

</details>

## How I work

```text
Developer or market signal
    → reproducible problem
    → explicit assumptions and constraints
    → smallest useful prototype
    → tests, evals, and failure analysis
    → documentation and feedback
    → next iteration
```

| Build | Validate | Communicate |
| --- | --- | --- |
| Python, TypeScript, React, FastAPI, Flask, SQL, AWS, Solidity | Tests, evals, redaction, rate limits, fail-safe controls, audit trails | Mandarin/English demos, quick starts, technical content, product handoffs |

## Experience signals

- Worked across product and engineering on blockchain-enabled financial-product
  workflows, backend validation, data reconciliation, and test priorities.
- Built and reviewed AI, FinTech, cloud, cybersecurity, lending, and trading
  prototypes with explicit safety and trust boundaries.
- Conducted startup sourcing, market research, and cross-functional stakeholder
  work across financial services, commerce, and manufacturing contexts.
- Use Codex, Claude Code, and Cursor as reviewable engineering systems, with
  acceptance criteria, tests, diffs, runtime checks, and human approval.

## Public-work boundary

Public repositories contain portfolio-safe code, architecture, validation, and
reviewed examples. Team-owned implementations, credentials, private data, and
restricted configuration remain private. Full employment and education details
are available directly to recruiters.

---

<p align="center">
  Interested in developer experience, applied AI, and technical product work in Singapore and APAC.
</p>
