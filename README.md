<p align="left">
  <strong>English</strong> · <a href="README.zh-CN.md">中文</a>
</p>

<h1 align="center">Zou Zhihua (Josh) — FinTech AI Product</h1>

<p align="center">
  I build AI products for financial risk, trading, and operations — and I publish the
  evaluation evidence and the limits next to them.<br>
  Singapore · NUS MSc Digital Financial Technology (Jan 2027) · Mandarin / English
</p>

<p align="center">
  <a href="mailto:zouzhihuajosh@outlook.com">Email</a> ·
  <a href="https://www.linkedin.com/in/zouzhihuajosh">LinkedIn</a> ·
  <a href="https://github.com/joshuazou-web?tab=repositories">All repositories</a> ·
  <a href="ABOUT_JOSH.md">Beyond the portfolio</a>
</p>

<img align="right" width="150" src="assets/avatar-josh-500.png" alt="" />

## What I build

I take unclear financial, user, and risk problems and turn them into product decisions
that someone else can check: explicit rules, a runnable prototype, and a number with a
stated boundary around it.

- **AI product judgment.** Where AI adds incremental value against LLM, agent, and RAG
  capability boundaries — measured on accuracy, confidence, failure analysis, human
  review, and user trust, not on demo polish.
- **Risk and financial domain.** Credit, market, and operational risk expressed as
  explicit policy: thresholds, gates, fallbacks, and reconciliation.
- **Evidence and honest limits.** Every project below ships its own numbers, and says
  where those numbers stop being valid.

<br clear="right" />

## Start here

Different teams need different evidence. Pick the row that matches your role:

| If you are hiring for | Start with these |
| --- | --- |
| **FinTech / AI Product** | [CrossBorder RiskOps](#1-fintech-risk-trading--lending) · [WealthGuard Copilot](#1-fintech-risk-trading--lending) · [OpsSignal](#3-data-operations--trust-products) |
| **AI Product Manager** | [Converge](#2-agents-evaluation--reliability) · [Volc Agent Launchpad](#2-agents-evaluation--reliability) · [OpsSignal](#3-data-operations--trust-products) |
| **Technical PM / AI Engineering** | [DecisiveEval](#2-agents-evaluation--reliability) · [Agent Control Plane](#2-agents-evaluation--reliability) · [DEBUG.CN](#4-developer-experience--ai-tooling) |
| **Data & Operations / BizTech** | [OpsSignal](#3-data-operations--trust-products) · [ThinkBeforeClick](#3-data-operations--trust-products) |

A project appearing in more than one row is deliberate — it means that work carries
more than one kind of evidence.

## Work by area

### 1. FinTech: risk, trading & lending

**Proves:** turning market and credit risk into explicit, testable product rules.

*Domain grounding:* NUS MSc Digital Financial Technology · FinTech intern at **Huatai
International**, on a blockchain-finance product — smart-contract, backend, acceptance
and exception workflows, with Python/SQL validation and reconciliation · investment
analyst intern at **Sequoia Capital**, researching the cybersecurity sector.

| Project | What it proves | Evidence |
| --- | --- | --- |
| **CrossBorder RiskOps** — payment risk operations workbench<br>[Repository](https://github.com/joshuazou-web/crossborder-riskops) | Deterministic rules find the risk, an AI copilot organises the evidence, and only a person decides — a boundary enforced in code rather than promised in a prompt | 20 rules carrying severity, rationale and evidence; 6,000 transactions across 5 seeds; 26.9% escalated to a human; 304 tests. Every figure in the repo is produced by its own eval harness, and a test fails if the README drifts from it. *All data synthetic; never run in production.* |
| **WealthGuard Copilot** — evidence-grounded research protection<br>[Repository](https://github.com/joshuazou-web/wealthguard-copilot) | An ambiguous wealth or securities question turned into a bounded, evidence-backed research task, with the advice boundary held by a deterministic policy engine outside the model | Page- and paragraph-level dated evidence retrieval, financial arithmetic delegated to tested deterministic functions, full decision trace in a review-and-audit view, committed regression and citation-evaluation runs, 14-day dogfood protocol. *Educational and research use only — not investment advice; never places trades.* |
| **Risk-Based DeFi Lending**<br>[Case study](https://github.com/joshuazou-web/risk-based-defi-lending-case-study) · [Demo](https://joshuazou-web.github.io/risk-based-defi-lending-case-study/) | External risk signals become explicit LTV, interest-rate, liquidation-threshold and health-factor policy | Python/Flask scoring service, documented trust boundaries, selected code, interactive demo |
| **Algorithmic FX Trading & Monitoring**<br>[Case study](https://github.com/joshuazou-web/algorithmic-fx-product-case) · [Demo](https://joshuazou-web.github.io/algorithmic-fx-product-case/) | Market-regime logic that survives causal validation and turnover costs | Causal backtesting, monitoring design, fail-closed practice execution |
| **SoAI 2026 High-Beta Leader**<br>[Repository](https://github.com/joshuazou-web/SoAI-2026-High-Beta-Leader) | Committing to a frozen strategy under competition rules instead of fitting after the fact | Frozen high-beta leader strategy, SoAI 2026 AI Algorithmic Trading Competition entry |

### 2. Agents, evaluation & reliability

**Proves:** deciding when *not* to use an LLM, and proving an agent behaves under pressure.

| Project | What it proves | Evidence |
| --- | --- | --- |
| **Converge** — proactive clarification & recommendation<br>[Repository](https://github.com/joshuazou-web/techjam-converge) | Incomplete and shifting intent modelled as an inverse user model with explicit task state; expected-information-gain clarification and confidence-gated recommendations | **0.976 vs 0.107 baseline** on the official 200-session evaluator; 28 tests, ablation and stress checks. Deliberately no LLM where interpretable rules sufficed. *Bounded to a closed catalog and synthetic users — not real conversion or retention.* |
| **Volc Agent Launchpad** — agent safety & audit<br>[Repository](https://github.com/joshuazou-web/volc-agent-launchpad) | Prompt injection, privilege escalation and dangerous-command risk mapped to a three-layer guardrail with block / allow / human-review outcomes | **138 passed, 1 skipped**; 8 demo scenarios, false-positive corpora, audit trails, type checks and production build passing. *A prototype — not proof of complete attack coverage.* |
| **DecisiveEval**<br>[Repository](https://github.com/joshuazou-web/decisive-eval) | Whether a coding-agent decision survives defensible changes to grading, runtime, failure handling, cost and latency policy | 26 public JSON Schemas, 103 tests, immutable evidence receipts, repeated-run and bootstrap paths. *Publishes its failed experiments and leaves real-world validation open.* |
| **Agent Control Plane**<br>[Repository](https://github.com/joshuazou-web/agent-control-plane) | Machine-checkable authority and approval gates for agent workflows | Append-only traces, resumable task folders, reproducible propose-check-execute-record-escalate examples |
| **PropTech Agent Reliability Lab**<br>[Repository](https://github.com/joshuazou-web/proptech-agent-reliability-lab) | Debugging agent failures against a realistic customer problem | Synthetic PropTech practice lab on FastAPI + Streamlit |

### 3. Data, operations & trust products

**Proves:** instrumenting a workflow, then handing uncertainty back to a human on purpose.

| Project | What it proves | Evidence |
| --- | --- | --- |
| **OpsSignal** — operations analytics & human-AI workflow<br>[Repository](https://github.com/joshuazou-web/opssignal) | An explainable model chosen over an LLM for cost, control and explainability, with a review queue that exposes model uncertainty | **0.842 held-out accuracy, 0.836 Macro-F1**; at a 0.65 threshold, **84.0% auto-coverage and 92.3% agreement** among auto-classified held-out samples. 3,600 synthetic tickets into 6 dimensions, 51 values, 21 marts; 19 validations and 166 tests passed. |
| **ThinkBeforeClick** — anti-scam learning product<br>[Case study](https://github.com/joshuazou-web/think-before-click-product-case) · [Demo](https://joshuazou-web.github.io/think-before-click-product-case/) | Learner feedback connected to enterprise analytics with responsible safeguards, shipped by a 5-person team on AWS | 23-person course test: **4.3/5 usability, 4.2/5 individual and 4.5/5 enterprise-participant satisfaction**; NUS STePS Honourable Mention (2025). *Course sample only.* |

### 4. Developer experience & AI tooling

**Proves:** making another person's failure legible, in two languages.

| Project | What it proves | Evidence |
| --- | --- | --- |
| **DEBUG.CN** — Mandarin OpenAI API debugging copilot<br>[Repository](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot) · [Demo](https://ctkhkof0ez.feishuapp.com/app/app_17c3qmjxcq2) · [3-min bilingual video](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot/releases/download/v0.1.0/DEBUG-CN-3min-bilingual-demo-subtitled.mp4) | API and SDK failures turned into reviewable evidence, root causes, minimal fixes and verification checks | 8 error categories, 24 backend tests, 20/20 public eval; server-side secret redaction, deterministic fallback, source-level rate and token controls. *Structured Outputs path implemented; real-model validation pending account quota.* |
| **白盒 · wbox** — presentation rehearsal for students<br>[Repository](https://github.com/joshuazou-web/wbox) | Helping students genuinely understand the AI-assisted coursework they are about to defend | Mandarin-first product: predicted questions, Q&A rehearsal, presentation pack |

## How I work

```text
Market, user, or risk signal
    -> reproducible problem
    -> explicit assumptions and capability boundaries
    -> smallest useful prototype
    -> evaluation, failure analysis, human review
    -> stated limits and next iteration
```

| Build | Validate | Communicate |
| --- | --- | --- |
| Python, TypeScript, SQL, FastAPI, React, AWS Serverless, DuckDB, Solidity, Git | Metric trees, instrumentation and funnels, rule/model evaluation, confidence and failure analysis, redaction, rate limits, audit trails, usability testing | PRDs and flows, conversational UI, Mandarin/English demos and quick starts, acceptance and retrospectives |

I use Codex and Claude Code for ideation and code and test drafts. I own the product
decisions, the reproducibility, and the truth boundaries.

## Experience signals

- **Huatai International** — FinTech intern (Jul–Nov 2024). Iteration and launch
  coordination for a blockchain-finance product; assessed AI risk, CBDC, DLT, DeFi and
  digital-human concepts by user value, feasibility, risk and cost.
- **AI Star** — angel investor and co-founder (2022–present). Segmentation, pricing and
  unit economics, feature prioritisation, and partner communication for an early-stage
  education product.
- **Sequoia Capital** — investment analyst intern (Jan–May 2024). Researched dozens of
  cybersecurity companies across customer need, commercialisation and technology trends.
- **MiraclePlus** — campus scout (Mar–Aug 2023). Sourced and screened early-stage
  ventures; interviewed founders on pain points, differentiation and validation paths.
- **Recognition** — First Prize and Best Entrepreneurship Award, National Innovation &
  Entrepreneurship Challenge (cross-border e-commerce); Budweiser
  digital-transformation study, [DOI 10.54691/bcpbm.v38i.3909](https://doi.org/10.54691/bcpbm.v38i.3909).

## Public-work boundary

Public repositories contain portfolio-safe code, architecture, validation, and reviewed
examples. Team-owned implementations, credentials, private data, and restricted
configuration remain private. Demo datasets are synthetic unless stated otherwise. Full
employment and education details are available directly to recruiters.

---

<p align="center">
  Open to FinTech and AI product roles in Shenzhen, Hong Kong, Singapore, and other
  major technology and financial hubs. Graduating January 2027.
</p>
