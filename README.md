<p align="left">
  <strong>English</strong> · <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <a href="assets/zhihua-zou-ai-product-business-casebook-zh-cn.pdf"><strong>AI 产品商业案例集合（中文版，PDF）→</strong></a>
</p>

<h1 align="center">Zou Zhihua (Josh)</h1>

<p align="center">
  <strong>I do not want AI and digital products to hide consequential decisions behind a polished interface.<br>
  I want them to make evidence visible, authority explicit, and the next human action safer.</strong>
</p>

<p align="center">
  FinTech × AI Product · Singapore<br>
  NUS MSc Digital Financial Technology · Graduating January 2027 · Mandarin / English
</p>

<p align="center">
  <a href="mailto:zouzhihuajosh@outlook.com">Email</a> ·
  <a href="https://www.linkedin.com/in/zouzhihuajosh">LinkedIn</a> ·
  <a href="https://github.com/joshuazou-web?tab=repositories">All repositories</a> ·
  <a href="ABOUT_JOSH.md">Beyond the portfolio</a>
</p>

<img align="right" width="150" src="assets/avatar-josh-500.png" alt="" />

## The question behind my work

A lot of AI and digital products try to answer faster, automate more, and look more capable. But
when a product can affect money, risk, or a person's next action, a plausible answer is nowhere near
enough.

What evidence did the system use? Who calculated the important number? Is the source still current?
Who has authority to decide? Will the model stop when it is uncertain? And when it should not decide,
does the product still help a person take the next step?

My projects keep returning to the same idea:

> **Turn an ambiguous problem into an explicit task, put model and automation capability inside inspectable boundaries, and make the next human action clear.**

That direction grew out of experiences that initially looked unrelated: researching cybersecurity
companies at Sequoia, working on a blockchain-finance product at Huatai International, studying
digital financial technology at NUS, and building and investing in early-stage products. They now
converge on one way of working: make the risks, exceptions, and ownership explicit before deciding
where AI belongs.

<br clear="right" />

## If you have five minutes

Start with these three projects. They move from a payment-operations decision, to an investment-
research question, to the last seconds before a payment—but follow the same product logic: keep
consequential authority explicit, make the evidence inspectable, and design what happens next.

### 1. Nine risk signals fire on a cross-border payment. What should the AI do?

[**CrossBorder AML RiskOps →**](https://github.com/joshuazou-web/crossborder-riskops)

It should not decide whether to release or hold the payment. It should identify the two signals that
matter, expose missing evidence, and leave the decision to a person.

I built a cross-border payment lifecycle, 20 deterministic risk rules, an interpretable model, a
human review queue, and a hash-chained audit trail. No language model participates in detection,
prioritisation, or routing. A copilot now sits in the one place it belongs: it summarises the case,
explains each signal with citations, names the missing information that would settle the question,
answers the analyst's follow-up question from a wider packet, and may abstain. A tired analyst
asking it to “just approve this one” is refused before any model call—and the refusal is not the
safeguard. The brief schema has no decision field and the audit log rejects an AI actor, so the
answer has no path to become an outcome.

- 6,000 synthetic transactions across five independently generated worlds: 97.01% ± 0.42% recall,
  80.06% ± 1.49% precision, and a 6.95% ± 0.47% false-positive rate at a 27.08% ± 0.42% review rate;
- raw alert precision 0.223, rising to 0.870 at review capacity—the ordering is the product;
- 453 automated tests, including an adversarial suite aimed at the copilot's grounding gate;
- a real OpenAI-compatible model is opt-in through one environment variable; the demo, the tests,
  and every published metric run on the deterministic provider with no key, and figures from a live
  model are labelled separately;
- all data is synthetic, and the system has never run in production.

### 2. A user asks, “Is SPY suitable for me?” Why not answer immediately?

[**WealthGuard Proofline →**](https://github.com/joshuazou-web/wealthguard-proofline)

Because horizon, liquidity needs, or loss tolerance could each change the research path.

WealthGuard identifies the one missing fact most likely to change that path and asks one question.
It then retrieves dated, page-level official evidence, delegates financial arithmetic to
deterministic tools, and exposes the full research trail. Requests to trade or guarantee a return
are refused by a policy engine outside the model.

The project has since been repositioned around what a fluent securities assistant cannot easily
prove on its own: **evidence and version validation before an answer is trusted, and bad-case
governance after one fails.** A language model may turn already-selected evidence into language.
Its output has to pass schema and citation validation, and a timeout or a malformed response
degrades to the deterministic path, a caution, or an abstention. Policy, arithmetic, dates,
confidence, and audit never depend on a model name.

- 13 original documents from the SEC, HKEX, SZSE, and CSRC, parsed into 1,714 evidence chunks bound
  to page or paragraph locations and SHA-256 checksums;
- 126 fixed-seed policy regression cases and 39 official citation-trace cases;
- a quality-operations surface with 16 error types, expected-versus-actual traces, ownership, and
  regression links, so a failed answer becomes an attributable case instead of a complaint;
- for education and research only—not investment advice; no brokerage connection or execution
  path; an independent prototype with no institutional affiliation.

### 3. What if the anti-scam lesson arrived at the moment the money was about to move?

[**ThinkBeforeClick FinSafe →**](https://github.com/joshuazou-web/think-before-click-product-case) ·
[**Live FinSafe demo**](https://joshuazou-web.github.io/think-before-click-product-case/finsafe/) ·
[**Original team-prototype case**](https://joshuazou-web.github.io/think-before-click-product-case/)

ThinkBeforeClick began as a five-person NUS Cloud Computing team project: an AWS serverless
prototype connecting localised phishing education for individuals with authorised campaign
analytics for enterprises. The course report records 23 participants, 4.3/5 usability, and an
Honourable Mention at the 27th NUS STePS Showcase.

The harder product question came next: would any of that knowledge still surface while urgency,
authority, secrecy, or a promised return was pushing someone toward an irreversible payment?
FinSafe moves the intervention to that moment—`message → risk signals → scam stage → deterministic
intervention → independent verification → user decision → micro-learning`—with 10 scam categories,
16 sourced signals, a nine-stage state model, and a five-level intervention ladder. A business
payment pack adds the dimension the consumer flow never modelled: **how much money is about to
move** sets a floor under the intervention level that signal rules may raise but never lower.

The result worth reading is a baseline rather than the headline. An LLM without deterministic
safety rules reached 95.2% critical-signal recall but only 29.2% intervention accuracy. With rules
owning the intervention level and the model restricted to suggesting known signal IDs and
explaining them, accuracy is 97.5% at the same recall, with 0% over-intervention.

- 161 fixed consumer cases and 82 locked business cases, each measured against three baselines;
  removing only the amount dimension pushes business under-intervention from 0% to 22.0%;
- six failing indirect-language cases stay visible rather than being deleted to improve the score;
- the demo runs entirely in the browser on a deterministic mock provider—no API key, no email, no
  tracking, and pasted text is redacted before analysis;
- the 23-person pilot tested the original prototype, not FinSafe, and no figure from it is
  presented as a FinSafe result; the private team implementation stays private;
- a portfolio P0—not a bank product, a fraud verdict, or a payment blocker.

## Where a model is allowed to speak

Three of the projects above now integrate a language model. Two others deliberately do not. It is
the same decision made once per problem, and the boundary is written in code rather than in a
prompt.

| Project | What the model may do | What it can never do |
| --- | --- | --- |
| **CrossBorder RiskOps** | Summarise a case, explain signals with citations, answer the analyst's second question, abstain | Detect, prioritise, route, or commit an outcome—the brief schema has no decision field and the audit log rejects an AI actor |
| **WealthGuard Proofline** | Turn already-selected, dated evidence into language | Choose policy, compute a number, date a source, or set a confidence level |
| **FinSafe** | Suggest candidate signals from existing IDs and explain them in plain language | Lower an intervention level a deterministic rule has already set |
| **DEBUG.CN** | Turn an API failure into evidence, root cause, a minimal fix, and verification steps | Reach a live key, skip server-side redaction, or bypass rate and token controls |

Four properties are shared. The deterministic provider is the default, so the demo, the tests, and
every published number run without a key. Model output is schema-validated and rejected when it
invents an identifier. A timeout or malformed response degrades to the rules rather than to a
partial recommendation. And every metric is labelled with the provider that produced it.

The two projects that say no are the other half of the same judgment: **Converge** and
**OpsSignal** already had interpretable, reproducible rules that were sufficient, so a model would
have added cost and variance without adding correctness.

## The same product logic, applied elsewhere

The projects below extend that pattern from deciding what to ask, to routing uncertainty through a
workflow, to encoding authority in software.

### Ask the question that reduces uncertainty

[**Converge →**](https://github.com/joshuazou-web/techjam-converge)

Instead of appending every utterance to a search query, Converge asks a different question: if this
product were the target, could it have generated what the shopper just said? And which next question
would eliminate the most wrong answers?

Converge combines an inverse user model, expected information gain, and confidence-gated
recommendations to make the conversation converge. It also let me test an important product
judgment: **when interpretable and reproducible rules are already sufficient, adding an LLM does
not automatically make the product better**—which is also why the projects that do use one keep it
inside a schema and outside the decision.

- TechnicalScore **0.976 versus a 0.107 baseline** on the official 200-session evaluator;
- the target was surfaced in 200/200 sessions, in 1.96 turns on average;
- zero tokens and zero model cost;
- public ablations and paraphrase stress tests;
- bounded to a closed catalog and synthetic users—not evidence of real conversion or retention.

### Put uncertainty into the workflow instead of hiding it inside a score

[**OpsSignal**](https://github.com/joshuazou-web/opssignal) finds structure in 3,600 synthetic
operations tickets. I chose an interpretable model over an LLM, then drew an explicit human-AI
boundary: high-confidence results can flow automatically; uncertain cases enter a review queue.

- 0.842 held-out accuracy and 0.836 Macro-F1;
- at a 0.65 threshold, 84.0% auto-coverage and 92.3% agreement among auto-classified samples;
- 19 data validations and 166 automated tests.

[**DEBUG.CN**](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot) turns OpenAI
API and SDK failures into reviewable evidence, root causes, minimal fixes, and verification steps.
It is designed to help Mandarin-speaking developers know what to inspect next—not to generate one
more plausible explanation. The project covers eight error categories, 24 backend tests, and a
20/20 public evaluation, with server-side secret redaction, rate and token controls, and a
deterministic fallback.

### Give agents boundaries before giving them authority

[**Volc Agent Launchpad**](https://github.com/joshuazou-web/volc-agent-launchpad) maps prompt
injection, privilege escalation, and dangerous-command risk into allow, block, or human-review
outcomes. It includes eight demo scenarios, false-positive corpora, audit traces, and 138 passing
tests with one skipped. It is a security prototype, not proof of complete attack coverage.

[**Agent Control Plane**](https://github.com/joshuazou-web/agent-control-plane) turns “what an agent
may do” from prompt text into executable policy: default deny, human approval, runtime budgets,
one-shot gates, and hash-linked audit. The goal is not to make the agent smarter. It is to make its
authority explicit and harder to bypass accidentally.

[**DecisiveEval**](https://github.com/joshuazou-web/decisive-eval) asks a deeper evaluation
question: does a coding-agent conclusion survive defensible changes to the grader, runtime,
failure policy, cost, or latency assumptions? It ships 26 public JSON Schemas, 103 tests,
immutable evidence receipts, and the experiments that did not work.

[**PropTech Agent Reliability Lab**](https://github.com/joshuazou-web/proptech-agent-reliability-lab)
puts those reliability questions inside a synthetic but recognisable customer workflow, using
FastAPI and Streamlit to observe how agents fail, recover, and get debugged.

### Write down the variable nobody else is tracking

- [**被允许动的钱 · The Money AI Is Allowed to Move**](https://github.com/joshuazou-web/money-ai-is-allowed-to-move):
  a 40-page independent projection of fintech's next decade, tracking one variable — how much money an
  AI is allowed to move without a human reviewing each transaction — and arguing that this, not model
  capability, decides who ends up owning the rails. An L0–L4 automation-depth ladder graded on liability
  rather than capability; the four control rights (data, entry, execution, liability); six falsifiable
  bets with dated windows; ten quarterly tracking signals. Every forward-looking claim carries its own
  falsification condition, and the appendix publishes the errata from the fact-check rather than a
  disclaimer. [Read it](https://joshuazou-web.github.io/money-ai-is-allowed-to-move/)

### Other financial and product experiments

- [**Risk-Based DeFi Lending**](https://github.com/joshuazou-web/risk-based-defi-lending-case-study):
  external risk signals translated into explicit LTV, interest-rate, liquidation-threshold, and
  health-factor policy. [Interactive demo](https://joshuazou-web.github.io/risk-based-defi-lending-case-study/)
- [**Algorithmic FX Trading & Monitoring**](https://github.com/joshuazou-web/algorithmic-fx-product-case):
  market-regime logic challenged by causal backtesting, turnover cost, and fail-closed practice
  execution. [Interactive demo](https://joshuazou-web.github.io/algorithmic-fx-product-case/)
- [**SoAI 2026 High-Beta Leader**](https://github.com/joshuazou-web/SoAI-2026-High-Beta-Leader):
  a strategy frozen before the competition outcome rather than fitted afterward.
- [**白盒 · wbox**](https://github.com/joshuazou-web/wbox):
  a Mandarin-first presentation rehearsal product that helps students genuinely understand the
  AI-assisted coursework they are about to defend.

## How I build

I usually begin with a problem that is not polished, but is real:

```text
a market, user, or risk signal
        ↓
a reproducible problem
        ↓
explicit assumptions, authority, and failure boundaries
        ↓
the smallest complete product loop
        ↓
evaluation, failure analysis, and human review
        ↓
publish the number—and where the number stops being valid
```

| Build | Validate | Communicate |
| --- | --- | --- |
| Python, TypeScript, SQL, FastAPI, React, AWS Serverless, DuckDB, Solidity, Git, OpenAI-compatible LLM providers behind a schema | Metric trees, rule/model evaluation, schema-bound model output, provider-labelled metrics, confidence and failure analysis, audit trails, redaction, rate limits, usability testing | PRDs, workflow design, conversational UI, Mandarin/English demos, acceptance and retrospectives |

I use Codex and Claude Code to assist with ideation and first drafts of code and tests. I own the
product judgment, validation design, reproducibility, and truth boundaries.

## Where I come from

- **Huatai International · FinTech Intern, Jul–Nov 2024**  
  Worked on iteration and launch coordination for a blockchain-finance product; evaluated AI risk,
  CBDC, DLT, DeFi, and digital-human concepts through user value, feasibility, risk, and cost.
- **AI Star · Angel Investor and Co-founder, 2022–present**  
  Worked on segmentation, pricing and unit economics, feature prioritisation, and partner
  communication for an early-stage education product.
- **Sequoia Capital · Investment Analyst Intern, Jan–May 2024**  
  Researched dozens of cybersecurity companies through customer need, commercialisation, and
  technology trends.
- **MiraclePlus · Campus Scout, Mar–Aug 2023**  
  Sourced and screened early-stage ventures and interviewed founders about pain points,
  differentiation, and validation paths.
- **Other work**  
  First Prize and Best Entrepreneurship Award, National Innovation & Entrepreneurship Challenge
  (cross-border e-commerce); Budweiser digital-transformation research,
  [DOI 10.54691/bcpbm.v38i.3909](https://doi.org/10.54691/bcpbm.v38i.3909).

## Public-work boundary

Public repositories contain portfolio-safe code, architecture, evaluation, and reviewed examples.
Team-owned implementations, credentials, private data, and restricted configuration remain
private. Demo datasets are synthetic unless stated otherwise. Full employment and education details
are available directly to recruiters.

---

<p align="center">
  Open to FinTech and AI product roles in Shenzhen, Hong Kong, Singapore, and other major technology and financial hubs.<br>
  If you are also thinking about what AI should do—and where it should stop—I would be glad to talk.
</p>
