<p align="left">
  <strong>English</strong> · <a href="README.zh-CN.md">中文</a>
</p>

<h1 align="center">Zou Zhihua (Josh)</h1>

<p align="center">
  <strong>I do not want financial AI to merely sound more like an expert.<br>
  I want every consequential judgment to be challengeable, reproducible, and able to stop before it crosses a boundary.</strong>
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

A lot of AI products try to answer faster and sound more expert. But when an answer can affect
money, risk, or a person's next action, sounding plausible is nowhere near enough.

What evidence did the system use? Who calculated the important number? Is the source still current?
Will the model stop when it is uncertain? If the AI and the human disagree, who actually decides?

My projects keep returning to the same idea:

> **Turn an ambiguous problem into an explicit task, put model capability inside inspectable boundaries, and deliberately return uncertainty to a human.**

That direction grew out of experiences that initially looked unrelated: researching cybersecurity
companies at Sequoia, working on a blockchain-finance product at Huatai International, studying
digital financial technology at NUS, and building and investing in early-stage products. They now
converge on one way of working: make the risks, exceptions, and ownership explicit before deciding
where AI belongs.

<br clear="right" />

## If you have five minutes

Start with these three projects. Each answers one of the questions I care about most.

### 1. Nine risk signals fire on a cross-border payment. What should the AI do?

[**CrossBorder RiskOps →**](https://github.com/joshuazou-web/crossborder-riskops)

It should not decide whether to release or hold the payment. It should identify the two signals that
matter, expose missing evidence, and leave the decision to a person.

I built a cross-border payment lifecycle, 20 deterministic risk rules, an interpretable model, a
human review queue, and a hash-chained audit trail. The system prevents an AI actor from committing
the final decision in code—not through a prompt asking it to be careful.

- 6,000 synthetic transactions evaluated across five fixed seeds;
- 97.01% ± 0.42% recall and 80.06% ± 1.49% precision;
- 304 automated tests;
- all data is synthetic, and the system has never run in production.

### 2. A user asks, “Is SPY suitable for me?” Why not answer immediately?

[**WealthGuard Copilot →**](https://github.com/joshuazou-web/wealthguard-copilot)

Because horizon, liquidity needs, or loss tolerance could each change the research path.

WealthGuard identifies the one missing fact most likely to change that path and asks one question.
It then retrieves dated, page-level official evidence, delegates financial arithmetic to
deterministic tools, and exposes the full research trail. Requests to trade or guarantee a return
are refused by a policy engine outside the model.

- 13 original documents from the SEC, HKEX, SZSE, and CSRC;
- 1,714 evidence chunks bound to locations and checksums;
- 126 fixed-seed policy regression cases and 39 official citation-trace cases;
- for education and research only—not investment advice; no brokerage connection or execution path.

### 3. ThinkBeforeClick

- [**ThinkBeforeClick**](https://github.com/joshuazou-web/think-before-click-product-case):
  an anti-scam learning product shipped by a five-person team on AWS; a 23-person course test
  reported 4.3/5 usability, and the project received a 2025 NUS STePS Honourable Mention.
  [Interactive demo](https://joshuazou-web.github.io/think-before-click-product-case/)

## The same thread, taken further

### The shopper has not fully decided what they want. What should the system ask?

[**Converge →**](https://github.com/joshuazou-web/techjam-converge)

Instead of appending every utterance to a search query, Converge asks a different question: if this
product were the target, could it have generated what the shopper just said? And which next question
would eliminate the most wrong answers?

Converge combines an inverse user model, expected information gain, and confidence-gated
recommendations to make the conversation converge. It also let me test an important product
judgment: **when interpretable and reproducible rules are already sufficient, adding an LLM does
not automatically make the product better.**

- TechnicalScore **0.976 versus a 0.107 baseline** on the official 200-session evaluator;
- the target was surfaced in 200/200 sessions, in 1.96 turns on average;
- zero tokens and zero model cost;
- public ablations and paraphrase stress tests;
- bounded to a closed catalog and synthetic users—not evidence of real conversion or retention.

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
| Python, TypeScript, SQL, FastAPI, React, AWS Serverless, DuckDB, Solidity, Git | Metric trees, rule/model evaluation, confidence and failure analysis, audit trails, redaction, rate limits, usability testing | PRDs, workflow design, conversational UI, Mandarin/English demos, acceptance and retrospectives |

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
