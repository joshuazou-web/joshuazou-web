<p align="right"><strong>EN</strong> &nbsp;·&nbsp; <a href="README.zh-CN.md">中文</a></p>

<h1 align="center">Zou Zhihua (Josh)</h1>

<p align="center">
  <strong>Looking for: AI Solutions | FinTech · putting agents to work</strong><br>
  NUS MSc Digital Financial Technology (Class of 2027)
</p>

<p align="center">
  <a href="mailto:zouzhihuajosh@outlook.com">Email</a> &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/in/zouzhihuajosh">LinkedIn</a> &nbsp;·&nbsp;
  <a href="assets/zhihua-zou-ai-product-business-casebook-zh-cn.pdf">Casebook (PDF, Chinese)</a> &nbsp;·&nbsp;
  <a href="https://joshuazou-web.github.io/money-ai-is-allowed-to-move/en/">The Money AI Is Allowed to Move</a> &nbsp;·&nbsp;
  <a href="https://github.com/joshuazou-web?tab=repositories">All repositories</a>
</p>

I take a vague business request, break it into **rules, states, permissions and acceptance criteria**, and deliver something the other side can check on the spot: a working prototype, an evaluation anyone can re-run, and a note that says plainly where it stops working.

**18 projects** · 14 public repositories · 2 desensitised reports from real situations · cross-border payment compliance, securities research, internal operations, agent safety and on-the-ground business launches

> Labels: **Real situation** = a deliverable used in real work (desensitised); **Synthetic-data prototype** = runs and reproduces, but has not run in production; **Team project** = only my own part is described.

<a id="nav"></a>

**[01 · Turning a messy real-world problem into a plan people can act on](#solve)**

- [LLM-assisted consolidation of legacy property contracts](#contracts): turned "a stack of old handwritten contracts" into a clear picture of who holds what, and legal drafts ready for a lawyer's review
- [AI-assisted launch plan for a small food counter](#stall): from "one photo and two voice notes" to a buildable opening plan with an acceptance checklist
- [IT ticket triage and operations dashboard](#opssignal): define the work first, then add AI; 84% of tickets triaged automatically
- [B2B agent troubleshooting and client-communication lab](#proptech): a public walkthrough from client complaint to root cause, fix and explanation
- [Taking smart garment-manufacturing equipment to market](#aistar): brought 27 smart machines from the factory to customer production lines

**[02 · Drawing AI's boundaries, and proving it can be trusted](#ai)**

- [Permission control and audit kernel for enterprise agents](#acp): moves an agent's permissions out of the prompt and into code, with every step auditable
- [Three-layer safety gate for coding agents](#volc): stops dangerous commands and injection attacks at three points, 0/65 false positives
- [Robustness audit for agent evaluation results](#decisive): change one reasonable evaluation choice — does your conclusion still hold?
- [Conversational shopping by inverting the user model](#converge): finds the right product in 1.96 turns on average, with no model calls
- [Safe API-error diagnosis for Mandarin-speaking developers](#debugcn): redact first, then give a diagnosis that can be checked
- [AI practice partner for project defences](#wbox): find what you don't really understand before the defence, then explain it out loud

**[03 · Turning financial rules and risk into product mechanisms](#fin)**

- [Cross-border payment AML investigation triage](#crossborder): with the same staff, precision within capacity rises from 0.223 to 0.870
- [Evidence and quality layer for securities research answers](#wealthguard): every financial answer traces back to a dated official source
- [Pre-payment scam intervention](#finsafe): tiered intervention in the last seconds before paying; AI cannot lower the warning level
- [Risk-score-driven lending terms](#defi): turns a risk score into loan terms a borrower can read and recompute
- [From FX signal to research, monitoring and execution product](#fx): research, monitoring and orders kept apart; production environments refused outright
- [Anti-overfitting protocol for a trading competition strategy](#highbeta): rules frozen first, negative results published anyway
- [Adaptive phishing-awareness SaaS](#tbc): training for individuals and enterprises; enterprise satisfaction 4.5/5


<!--
Put a new project in the group it best proves, follow this template, and add a line to the directory above: "- [Project name](#id): one-line summary".

<a id="id"></a>

#### Project name
`Original name` · Personal / team project · Real situation / synthetic-data prototype · [Repository →](link)

One-line summary

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: who, in what situation, facing what problem; what needed to happen.
- **My role**: what I personally did (for team work, state the split).
- **Delivery & results**: what was delivered plus checkable numbers; say what kind of result it is (measured / estimated / synthetic evaluation).

</details>
-->

<a id="solve"></a>

## 01 / Turning a messy real-world problem into a plan people can act on

> When the request is unclear and the information incomplete, first work out who is deciding and where things are stuck, then deliver a plan the other side can follow and check on the spot: a process, a workbook, documents or a system.

<a id="contracts"></a>

#### LLM-assisted consolidation of legacy property contracts
`Project Report A` · Led by me · Real situation (family engagement, draft stage) · [Report PDF →](evidence/Project_Report_A_Legacy_Rights_Consolidation.pdf)

Turned "a stack of old handwritten contracts" into a clear picture of who holds what, and legal drafts ready for a lawyer's review

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Over the years a family had built up several property interests through cooperative-construction agreements. All they had was "a stack of old handwritten contracts": agreements, applications and scans, many handwritten or incomplete. Succession had not been verified and there was no single entity to manage the interests. The goal was to turn the loose paperwork into a position and an action plan where every statement has a source and a lawyer can review it.
- **My role**: Analyst and coordinator: collected the originals, designed the process for using an LLM to extract and organise the contract information, checked every AI output against the originals, and decided how much confidence each conclusion deserved and in what order to act. Legal advice, notarisation, tax and registration were left to licensed professionals.
- **Delivery & results**: A rights chronology separated by plot; a set of legal drafts labelled by confidence, including a confirmation agreement; an action plan split into workstreams, listing the missing information, the risks and how to handle them. Verification caught the AI describing a "proposed split" as "confirmed". Still at draft stage; nothing has been signed.

</details>

<a id="stall"></a>

#### AI-assisted launch plan for a small food counter
`Project Report B` · Led by me · Real situation (first store in validation) · [Report PDF →](evidence/Project_Report_B_Micro_Retail_Launch.pdf)

From "one photo and two voice notes" to a buildable opening plan with an acceptance checklist

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: A family food business planned to pilot a 16.8 m² cooked-food counter at the entrance of a shopping hall in a county-level city. The decision-maker was not on site and had only one annotated photo and two voice notes; the budget was capped in the low tens of thousands of RMB; extraction, power and drainage were controlled by the landlord and not yet confirmed in writing. The goal was a plan a contractor could build from, that meets food-safety requirements and can be repeated later.
- **My role**: Defined the specification, used AI tools to turn the site fragments into modules and parameters, wrote the control workbook and two business documents, and checked each item against the site information and public rules. Site inspection and sign-off on electrical and extraction design were outside my scope.
- **Delivery & results**: 17 dimensioned modules and specifications for 9 utility systems; a seven-sheet budget and procurement workbook (15 construction items; 17 equipment items bought, 3 deferred); 4 pre-construction gates and a 16-item opening checklist, with the rule "if a gate fails, stop buying; repeat only after three stable months". The first counter is in validation, and these deliverables are the working basis for the build and opening.

</details>

<a id="opssignal"></a>

#### IT ticket triage and operations dashboard
`OpsSignal` · Personal project · Synthetic-data prototype · [Repository →](https://github.com/joshuazou-web/opssignal)

Define the work first, then add AI; 84% of tickets triaged automatically

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: An internal IT and business-technology team could not say where its workload sat: statuses and team names came in several spellings, classification depended on who was triaging that day, and an earlier AI triage had no confidence score or review path, so nobody trusted it. The goal was to define the work first, measure it next, and only then let a model triage.
- **My role**: Designed a six-dimension, 51-value taxonomy (with edge cases and messy aliases), the metric definitions for 21 mart tables, 19 graded checks with rollback, the auto-accept threshold and abstention rules for AI triage, and built the dashboard.
- **Delivery & results**: Ran cleaning → warehouse → dashboard → AI triage end to end on 3,600 synthetic tickets. The analysis found that 50% of resolved tickets had preventable root causes (about 9,423 person-days), and the largest duplicate cluster had been raised 52 times. Triage accuracy 0.842, calibration error 0.048; at confidence ≥ 0.65, 84.0% are auto-accepted (92.3% agreement with humans), 13.0% go to a person and 3.1% are abstained on; 166 automated tests.

</details>

<a id="proptech"></a>

#### B2B agent troubleshooting and client-communication lab
`PropTech Agent Reliability Lab` · Personal project · Synthetic practice lab · [Repository →](https://github.com/joshuazou-web/proptech-agent-reliability-lab)

A public walkthrough from client complaint to root cause, fix and explanation

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: After interviewing for a B2B PropTech role, I realised that someone new to the industry cannot see a company's internal agents or client projects. Rather than invent experience, I built a safe simulation and practised the "client feedback → root cause → fix → explanation" loop in public.
- **My role**: Designed the simulated site-analysis agent, the deliberately injected failure modes and the troubleshooting process, and wrote separate client-facing and engineering documents.
- **Delivery & results**: FastAPI + CLI + Streamlit dashboard; structured traces stored in SQLite and replayable; failures can be injected and classified, and every confirmed root cause leaves a regression test. Client reports are split into "facts / hypotheses / unknowns" with acceptance criteria, and each root cause is explained once for the client and once for engineering. All data is fictional; it shows the method transfers, not industry experience.

</details>

<a id="aistar"></a>

#### Taking smart garment-manufacturing equipment to market
`AI Star` · Investor & Product Commercialization Lead · Real business · [Product catalogue PDF →](evidence/AIStar_Product_Catalogue.pdf)

Brought 27 smart machines from the factory to customer production lines

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: AI Star develops smart garment-manufacturing equipment and needed to get it from the factory onto customers' lines, with cost, pricing and delivery worked out.
- **My role**: As investor and product commercialization lead, worked on customer conversations, factory coordination, product cost, pricing and delivery.
- **Delivery & results**: A product-line catalogue covering 27 automated sewing and finishing machines plus an equipment visualisation system, serving several brand customers.

</details>

<p align="right"><a href="#nav">↑ Back to directory</a></p>

<a id="ai"></a>

## 02 / Drawing AI's boundaries, and proving it can be trusted

> Decide what goes to the model, what goes to rules and what must stay with a person; put permissions in code rather than in the prompt; then use fixed test sets, ablations and false-positive rates to show it actually helps.

<a id="acp"></a>

#### Permission control and audit kernel for enterprise agents
`Agent Control Plane` · Personal project · Working CLI · [Repository →](https://github.com/joshuazou-web/agent-control-plane)

Moves an agent's permissions out of the prompt and into code, with every step auditable

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Writing "do not delete files" in a prompt is a request, not a rule: the model still decides whether to act. Teams deploying autonomous agents need permissions that are enforced at runtime and auditable afterwards.
- **My role**: Designed the threat model and decision order, the policy DSL (shell globs rather than regular expressions, so people other than the author can read and challenge a rule), one-time and expiring approvals, the audit chain and the CLI.
- **Delivery & results**: A Python kernel and CLI with no third-party dependencies. Every action is decided as allow / gate / deny; anything unmatched is denied and "cannot" rules always win. Sensitive actions wait for human approval, and approvals are single-use and expire. Tool-call and time budgets per task. Traces and approval logs are sealed with a SHA-256 hash chain, and a dry run explains a decision without executing it. Not yet audited by a third party.

</details>

<a id="volc"></a>

#### Three-layer safety gate for coding agents
`Volc Agent Launchpad` · Personal entry · TechJam 2026 · [Repository →](https://github.com/joshuazou-web/volc-agent-launchpad)

Stops dangerous commands and injection attacks at three points, 0/65 false positives

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Prompt filtering fails in three cases: the attack is reworded or translated; the instruction is benign but its implementation is destructive ("clean up the build artefacts" becomes `rm -rf`); or the attack hides inside a workspace file. The goal was to intercept at three different points without getting in the way of normal development.
- **My role**: Broke down the threat scenarios, designed the three layers, implemented PolicyGate, and wrote the demo scenarios and tests.
- **Delivery & results**: L1 deterministic rules (stops attacks before the model is called, 0 tokens) + L2 semantic intent classification + L3 runtime command and file-content gates; Fastify API → PolicyGate → container sandbox, with every decision written to a structured JSON audit trail. 138 tests pass, 0/65 false positives, 8 one-click demo scenarios (2 allowed controls + 6 threat probes).

</details>

<a id="decisive"></a>

#### Robustness audit for agent evaluation results
`DecisiveEval` · Personal project · v0.1 research prototype · [Repository →](https://github.com/joshuazou-web/decisive-eval)

Change one reasonable evaluation choice — does your conclusion still hold?

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: "Config A beats config B" rests on choices nobody wrote down: whether infrastructure errors count as failures, whether cost counts, which statistic to take over reruns. Change one and the conclusion can quietly flip. The goal was to tell a team how solid a conclusion is before they change a production default.
- **My role**: Designed the "specification universe" and the audit-report fields, wrote a pre-registration protocol, and published the negative results and failure log.
- **Delivery & results**: A CLI and immutable evidence pipeline: SHA-256 of the inputs, metrics per specification, deterministic stratified bootstrap, agreement with the default decision, the specifications that flip the conclusion and the "minimum specification distance"; a Codex adapter with fail-closed budgets and a public JSON Schema. The empirical loop is deliberately left open; it is not used to claim any configuration is better.

</details>

<a id="converge"></a>

#### Conversational shopping by inverting the user model
`Converge` · Personal entry · TikTok TechJam 2026 · [Repository →](https://github.com/joshuazou-web/techjam-converge)

Finds the right product in 1.96 turns on average, with no model calls

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Conversational search usually asks how similar the user's words are to a product. In this challenge the user's words were generated from the target product in the first place. The goal was to find the product within 10 turns with as few questions as possible.
- **My role**: Reframed the problem as "if this were the product, could the user have said that?"; designed the retrieval, questioning and display strategy, and ran ablations with the official evaluator.
- **Delivery & results**: Pre-expanded and indexed all 50,000 products, so retrieval became set intersection; the next question is chosen by expected information gain and the number of results shown by confidence. Official evaluation: TechnicalScore 0.9760 (weak baseline 0.1067), Hit@10 1.000, 1.96 turns on average, 7.7 ms per turn, no model calls; ablation shows the inverted user model is worth 0.12 points. Results hold only within the challenge's evaluation protocol.

</details>

<a id="debugcn"></a>

#### Safe API-error diagnosis for Mandarin-speaking developers
`DEBUG.CN` · Personal project · Working demo · [Repository →](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot)

Redact first, then give a diagnosis that can be checked

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Developers tend to paste an entire error together with their configuration into an AI chat. That can leak keys and identifiers, and what comes back is prose nobody can verify. The goal was to redact first and then return a structured diagnosis that can be checked.
- **My role**: Designed the safe defaults, the diagnosis format, the error taxonomy and the cost guardrails for the public demo, and built the front end and back end.
- **Delivery & results**: Secrets are masked before anything reaches a model, and the browser never sees a key. Every diagnosis includes evidence, confidence, a minimal fix and a verification checklist. The public demo has guardrails (3 calls per minute per client, 25 per day, 1,600 tokens per call) and falls back to deterministic diagnosis instead of failing; a demo mode that needs no key, bilingual examples and a 20-case public evaluation set.

</details>

<a id="wbox"></a>

#### AI practice partner for project defences
`wbox` · Personal project · MVP · [Repository →](https://github.com/joshuazou-web/wbox)

Find what you don't really understand before the defence, then explain it out loud

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Students now routinely use AI for course projects, so the real question is whether they can explain what they hand in. The goal was to find the gaps before the defence and make the student explain them, not to detect whether AI wrote the work.
- **My role**: Set the product and ethical boundary (training before the defence only; live answering was cut), designed the question bank and red-flag rules, and built the Flask service and four-step wizard.
- **Delivery & results**: Question prediction (20 common follow-up types + 6 kinds of AI-trace red flags) → question-by-question practice → talk outline, Q&A cards and a must-fix list; a template mode that works with no setup, and an LLM mode once a key is added. No real-user data yet.

</details>

<p align="right"><a href="#nav">↑ Back to directory</a></p>

<a id="fin"></a>

## 03 / Turning financial rules and risk into product mechanisms

> Break compliance requirements, risk signals and trading discipline into states, rules, thresholds and audit records, so that decisions about money can be explained, recomputed and traced when they go wrong.

<a id="crossborder"></a>

#### Cross-border payment AML investigation triage
`CrossBorder RiskOps` · Personal project · Synthetic-data prototype · [Repository →](https://github.com/joshuazou-web/crossborder-riskops)

With the same staff, precision within capacity rises from 0.223 to 0.870

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: The real bottleneck in AML teams is not spotting anomalies but having too many to review: raw alert precision is low, so investigators open cases by time or amount. The goal was to make the batch they can handle each day the batch that most deserves attention, with the same staff, and to let an investigator overrule any ranking on the spot.
- **My role**: Worked through the scenario on my own (5 roles: investigator, payment operations, customer service, operations lead, auditor), designed the rules, ranking, human–AI permission boundary and evaluation, and built the front end and back end.
- **Delivery & results**: An 8-state payment core, 20 deterministic rules (9 signal families, 6 laundering typologies), 8-factor explainable ranking and four-way routing; AI only writes cited summaries and flags conflicts, and has no disposition rights in code. On 6,000 synthetic transactions the alert funnel runs 1,638 → 957 → 693 → 242, and precision within capacity rises from 0.223 to 0.870; 0/34 boundary probes broke through, prompt injection blocked 12/12 with 0/6 false blocks; 453 automated tests and a Chinese demo video.

</details>

<a id="wealthguard"></a>

#### Evidence and quality layer for securities research answers
`WealthGuard Proofline` · Personal project · Synthetic-data prototype · [Repository →](https://github.com/joshuazou-web/wealthguard-proofline)

Every financial answer traces back to a dated official source

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: The riskiest answer from a brokerage or wealth-platform assistant is not an absurd one but a confident one given without enough information: skipping the holding period, doing arithmetic in prose, citing undated sources. The goal was to turn an answer into a research trail that can be checked step by step before anyone trusts it.
- **My role**: Defined the product boundary (no trading, no forecasts, no promised returns), designed intent classification and clarification, a deterministic policy engine, evidence lineage with checksums and quality operations over 16 error types, and built the React + FastAPI app and all evaluations.
- **Delivery & results**: A six-step research flow: identify the task → ask only the question with the highest information value → keep policy outside the model → retrieve dated source text → do arithmetic in tested code → keep a complete trail. 13 official SEC / HKEX / SZSE / CSRC documents split into 1,714 checksummed evidence chunks; classification regression 126/126 and official-citation tracing 39/39 all pass. Synthetic data; not investment advice.

</details>

<a id="finsafe"></a>

#### Pre-payment scam intervention
`ThinkBeforeClick FinSafe` · Personal P0 (built on a five-person team prototype) · Synthetic-data prototype · [Repository →](https://github.com/joshuazou-web/think-before-click-product-case)

Tiered intervention in the last seconds before paying; AI cannot lower the warning level

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: The original ThinkBeforeClick was a five-person team's anti-phishing education product. I added a harder question: when urgency, authority, secrecy or high returns are pushing someone towards an irreversible payment, does what they learned come back to them? The goal was to move the intervention from the classroom to the last seconds before paying.
- **My role**: Built the P0 on my own (the team prototype is marked separately in the repository): risk representation, tiered intervention policy, the AI permission boundary and evaluation.
- **Delivery & results**: 10 scam types, 16 sourced risk signals and a 9-stage state model; deterministic policy sets the minimum intervention level, and AI can explain but not lower it; every result carries a reason, a citation and a concrete verification step. 243 locked synthetic cases (161 consumer, 82 business payment), 3 baselines, retained failure cases; an in-browser demo that needs no key.

</details>

<a id="defi"></a>

#### Risk-score-driven lending terms
`Risk-Based DeFi Lending` · NUS five-person team project · Live demo · [Repository →](https://github.com/joshuazou-web/risk-based-defi-lending-case-study)

Turns a risk score into loan terms a borrower can read and recompute

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Most "AI risk control" stops at a score, but a borrower cares how much they can borrow, at what rate, and when they will be liquidated. The goal was to translate a risk score into transparent lending rules a third party can recompute.
- **My role**: Built the Python risk-scoring service and Flask API; the contracts and front end were team work.
- **Delivery & results**: Scores are computed off-chain and enforced on-chain; one score drives maximum LTV, interest rate, liquidation threshold and borrowing limit together (e.g. score 20 → 80: LTV 74% → 56%, rate 5% → 11%); handles authorised updates, score freshness, parameter bounds and failure cases; the live demo needs no wallet or real funds.

</details>

<a id="fx"></a>

#### From FX signal to research, monitoring and execution product
`Algorithmic FX` · NUS five-person team project · Synthetic-data prototype · [Repository →](https://github.com/joshuazou-web/algorithmic-fx-product-case)

Research, monitoring and orders kept apart; production environments refused outright

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Between a profitable signal and a trading product others can use safely lie data versions, execution timing, trading costs, operator controls and monitoring. The goal was to turn an EUR/USD two-regime strategy into a complete research-workflow prototype.
- **My role**: A team project, so I do not claim all of the output; I proposed and pushed the product structure that keeps research, monitoring and execution separate.
- **Delivery & results**: ADX switches between trend and mean-reversion regimes, and the regime is visible in the interface; a target formed at the close of bar t applies to bar t+1; 2bp fees + 1bp slippage; three independent gates for data, orders and environment, with production refused outright; 12 offline tests and a live product demo. Synthetic data; indicative metrics.

</details>

<a id="highbeta"></a>

#### Anti-overfitting protocol for a trading competition strategy
`Frozen High-Beta Leader` · Personal entry · SoAI 2026 · [Repository →](https://github.com/joshuazou-web/SoAI-2026-High-Beta-Leader)

Rules frozen first, negative results published anyway

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: Anyone can tune a beautiful backtest; the hard part is not touching the parameters after seeing the results. The goal was a research protocol for a trading-competition strategy that stops me from cheating myself.
- **My role**: Designed the protocol, froze the rules and ran all three evaluation stages.
- **Delivery & results**: Only 3 dimensions were tunable, chosen on 7 development windows and then frozen; next, 6 previously seen holdout windows were opened (mean −6.32%, negative result kept), and finally 18 fresh out-of-sample windows were opened once (mean +10.95%, no parameter changed afterwards); next-day-open execution with 3bp costs. Simulated competition; not investment advice.

</details>

<a id="tbc"></a>

#### Adaptive phishing-awareness SaaS
`ThinkBeforeClick` · NUS five-person team project · User testing · [Product report PDF →](evidence/ThinkBeforeClick_Product_Report.pdf)

Training for individuals and enterprises; enterprise satisfaction 4.5/5

<details>
<summary>Show: background & goal · my role · delivery & results</summary>

- **Background & goal**: In the first half of 2025 Singapore recorded almost 20,000 scam cases and S$456 million in losses; enterprise phishing training is mostly static and one-size-fits-all, and security teams maintain simulations on top of their day jobs. The goal was an adaptive phishing-awareness SaaS for both individuals and enterprises.
- **My role**: Member of the five-person product team, working on the product plan, business model and user validation.
- **Delivery & results**: A SaaS on AWS serverless (Lambda, API Gateway, DynamoDB, Cognito and more) with phishing simulations and click-behaviour analytics; three-year total cost of ownership estimated 45% below on-premise (estimate); user-test satisfaction 4.2/5 for individuals and 4.5/5 for enterprises, and 89% of testers felt more confident spotting phishing.

</details>

<p align="right"><a href="#nav">↑ Back to directory</a></p>

## 04 / How I deliver an AI solution

```text
a vague request
    ↓  diagnose on site: who decides at what moment, and what a wrong call costs
    ↓  draw boundaries: what goes to the model, what to rules, what must stay with a person
    ↓  smallest working loop: prototype / workbook / documents the other side can check
    ↓  acceptance criteria: fixed test sets, counter-metrics, failure cases, human review
    ↓  handover: impact for the business, root cause for engineering, and where it stops working
```

I use AI for research, code and first drafts. The judgment on the solution, the acceptance criteria, checking the evidence, and what the system is allowed to do remain my responsibility.

## 05 / Experience

- **NUS** · MSc Digital Financial Technology · 2025–2027
- **Huatai International** · FinTech Product Intern · translated financial rules into product requirements
- **Sequoia China** · Investment Research Analyst · studied technology and cybersecurity companies
- **MiraclePlus** · Campus Scout · met young founders and evaluated early ideas
- **AI Star** · Investor & Product Commercialization Lead · customers, factories, cost, pricing and delivery

---

<p align="center">
  <strong>If your team needs AI to work inside a real business, let's talk.</strong><br><br>
  <a href="mailto:zouzhihuajosh@outlook.com">zouzhihuajosh@outlook.com</a>
</p>
