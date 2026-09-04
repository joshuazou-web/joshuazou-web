<p align="left">
  <a href="README.md">English</a> · <strong>中文</strong>
</p>

<h1 align="center">邹志华 Josh</h1>

<p align="center">
  <strong>我不希望 AI 与数字产品把重要决定藏在一个精致的界面背后。<br>
  我希望它让证据清晰可见、权限边界明确，也让人的下一步行动更安全。</strong>
</p>

<p align="center">
  金融科技 × AI 产品 · 新加坡<br>
  新加坡国立大学 数字金融科技硕士 · 2027 年 1 月毕业 · 中文 / English
</p>

<p align="center">
  <a href="mailto:zouzhihuajosh@outlook.com">邮箱</a> ·
  <a href="https://www.linkedin.com/in/zouzhihuajosh">LinkedIn</a> ·
  <a href="https://github.com/joshuazou-web?tab=repositories">全部仓库</a> ·
  <a href="ABOUT_JOSH.md">作品集之外</a>
</p>

<img align="right" width="150" src="assets/avatar-josh-500.png" alt="" />

## 我一直在追一个问题

很多 AI 与数字产品都在努力回答得更快、自动完成更多事情，也显得更有能力。但当一个产品会影响
资金、风险或人的下一步行动时，“听起来合理”远远不够。

系统依据了什么？关键数字是谁算的？资料是否已经过期？模型不确定时会不会停下来？如果它与人
意见不同，最后是谁做决定？当它本来就不该替人做决定时，产品还能不能帮助人走好下一步？

我做的项目都围绕这组问题展开：

> **把模糊问题变成明确任务，把模型与自动化能力放进可检查的边界，并让人的下一步行动清晰可执行。**

这条方向来自几段看似不同的经历：在红杉研究网络安全企业，在华泰参与区块链金融产品，在 NUS
学习数字金融科技，也做过创业、投资与产品落地。它们最终汇聚成同一种工作方式——先把业务里的
风险、例外和责任说清楚，再决定 AI 应该站在哪一层。

<br clear="right" />

## 如果你只有五分钟

先看这三个项目。它们从支付运营决策，走到投资研究问题，再走到安全教育闭环，但遵循的是同一套
产品逻辑：让重要权限边界清晰、让证据可检查，并把“接下来怎么办”设计进产品。

### 1. 当一笔跨境支付触发九个风险信号，AI 应该做什么？

[**CrossBorder RiskOps →**](https://github.com/joshuazou-web/crossborder-riskops)

不是替分析师决定放行或拦截，而是找出真正重要的两项证据、指出缺失信息，并把决定留给人。

我构建了完整的跨境支付生命周期、20 条确定性风险规则、一个可解释模型、人工复核队列与
hash-chained 审计记录。系统在代码层禁止 AI 提交最终决定，而不是只在 Prompt 里请求它“谨慎”。

- 6,000 笔合成交易，跨 5 个固定随机种子评测；
- 召回率 97.01% ± 0.42%，精确率 80.06% ± 1.49%；
- 304 个自动化测试；
- 所有数据均为合成数据，从未在生产环境运行。

### 2. 当用户问“SPY 适合我吗”，为什么不能马上回答？

[**WealthGuard Copilot →**](https://github.com/joshuazou-web/wealthguard-copilot)

因为投资期限、流动性需求和亏损承受能力中的任何一项，都可能改变研究路径。

WealthGuard 先找出最可能改变路径的那一项缺失信息，只问一个问题；随后检索带日期和页码的官方
资料，用确定性程序完成金融计算，并展示从问题到结论的完整研究轨迹。要求交易或保证收益时，
系统通过模型之外的策略引擎拒绝。

- 13 份 SEC、港交所、深交所与证监会官方原始文件；
- 1,714 个带位置与 checksum 的证据片段；
- 126 个固定种子策略回归案例和 39 个官方引用追溯案例；
- 仅用于教育与研究，不构成投资建议；不连接券商，也不执行交易。

### 3. 从 FinSafe 到 ThinkBeforeClick：如何把课程原型优化成更安全、更完整的产品案例？

[**ThinkBeforeClick——FinSafe 优化版 →**](https://github.com/joshuazou-web/think-before-click-product-case) ·
[**安全交互演示**](https://joshuazou-web.github.io/think-before-click-product-case/)

FinSafe 最初是一个 5 人 NUS 云计算课程团队项目：团队用 AWS Serverless 原型连接面向个人的本地化
钓鱼识别教育与面向企业的授权模拟分析。课程项目测试包含 15 名个人学习者和 8 名企业决策者，
可用性评分为 4.3/5，并获得 2025 NUS STePS Showcase Honourable Mention。

在公开作品集版本中，我将这套基础重新梳理并优化为 ThinkBeforeClick。它保留原有的双边产品闭环，
同时把三个边界讲清楚：团队原型真正实现了什么、现有证据能够支持什么，以及走向生产仍需补齐什么。

- 安全演示只使用通用场景和合成分析，不发送邮件、不保存回答，也不包含追踪；
- 产品案例与工程案例把个人的即时学习连接到企业的后续培训决策，而不是停在一张数据看板；
- 新增概念化事件合约与脱敏后的聚合逻辑，让“行为事件如何变成后续行动”可检查，同时不公开团队私有源码；
- 优化方案补入 token 绑定的租户授权、收件人白名单、假名化、幂等、数据留存、审计与紧急停止机制；
- 公开案例不主张个人独占成果，也不宣称已达到生产就绪，原始团队实现仍保持私有。

## 同一套产品逻辑，应用到更多场景

后面的项目把这套方法继续展开：先决定该问什么，再让不确定性进入工作流，最后把权限边界写进软件。

### 先问最能减少不确定性的那个问题

[**Converge →**](https://github.com/joshuazou-web/techjam-converge)

不是把顾客的每句话继续塞进搜索框，而是反过来问：如果某个商品真是目标，顾客会不会说出刚才
那些话？下一道问题又能排除多少错误答案？

Converge 用逆向用户模型、期望信息增益和置信度门控，把推荐变成一个逐轮收敛的过程。它也让我
验证了一件很重要的事：**能解释、能复现的规则已经足够时，不必为了“更 AI”而调用 LLM。**

- 官方 200 会话评测 TechnicalScore：**0.976，对比基线 0.107**；
- 200/200 会话找到目标，平均 1.96 轮；
- 零 token、零模型费用；
- 消融实验与改写压力测试公开在仓库中；
- 限定于封闭商品目录和合成用户，不代表真实转化率或留存。

### 让“不确定”进入工作流，而不是藏在模型分数里

[**OpsSignal**](https://github.com/joshuazou-web/opssignal) 从 3,600 条合成运营工单中识别问题结构。
我选择可解释模型而不是 LLM，并设计了一条明确的人机分工线：高置信度结果自动流转，低置信度结果
进入复核队列。

- 留出集准确率 0.842，Macro-F1 0.836；
- 在 0.65 阈值下，自动覆盖率 84.0%，自动分类样本一致率 92.3%；
- 19 项数据校验与 166 个自动化测试。

[**DEBUG.CN**](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot) 把 OpenAI API
和 SDK 报错整理成可复核的证据、根因、最小修复与验证步骤。它不是再生成一段“可能有用”的解释，
而是帮助中文开发者知道下一步应该检查什么。项目覆盖 8 类错误、24 个后端测试和 20/20 公开评测，
并包含服务端密钥脱敏、速率限制、token 控制与确定性兜底。

### 让 Agent 在获得能力之前，先获得边界

[**Volc Agent Launchpad**](https://github.com/joshuazou-web/volc-agent-launchpad) 把提示注入、
权限提升和危险命令映射成放行、拦截与人工复核三种结果。它包含 8 个演示场景、误报语料、
审计轨迹，以及 138 个通过、1 个跳过的测试。它是安全原型，不代表完整攻击覆盖。

[**Agent Control Plane**](https://github.com/joshuazou-web/agent-control-plane) 把“你可以做什么”
从 Prompt 文本变成机器可执行的权限策略：default deny、人工审批、预算限制、一次性 gate 和
hash-linked audit。目标不是让 Agent 更聪明，而是让它的权力更明确、更难被意外绕过。

[**DecisiveEval**](https://github.com/joshuazou-web/decisive-eval) 追问更底层的问题：一个 Coding
Agent 的结论，换一套合理的评分方式、运行时、失败政策、成本或延迟假设后，还成立吗？项目包含
26 个公开 JSON Schema、103 个测试、不可变证据回执，也公开没有成功的实验。

[**PropTech Agent Reliability Lab**](https://github.com/joshuazou-web/proptech-agent-reliability-lab)
则把这些可靠性问题放进一个合成的真实客户场景里，用 FastAPI 与 Streamlit 观察 Agent 如何失败、
恢复和被调试。

### 其他金融与产品实验

- [**Risk-Based DeFi Lending**](https://github.com/joshuazou-web/risk-based-defi-lending-case-study)：
  把外部风险信号变成明确的 LTV、利率、清算阈值和健康因子策略。
  [交互演示](https://joshuazou-web.github.io/risk-based-defi-lending-case-study/)
- [**Algorithmic FX Trading & Monitoring**](https://github.com/joshuazou-web/algorithmic-fx-product-case)：
  用因果回测、换手成本和 fail-closed 模拟执行检查市场状态逻辑。
  [交互演示](https://joshuazou-web.github.io/algorithmic-fx-product-case/)
- [**SoAI 2026 High-Beta Leader**](https://github.com/joshuazou-web/SoAI-2026-High-Beta-Leader)：
  在比赛规则下提前冻结策略，而不是看到结果后再拟合。
- [**白盒 · wbox**](https://github.com/joshuazou-web/wbox)：
  面向学生的中文答辩陪练，帮助他们真正理解自己即将展示的 AI 辅助课程项目。

## 我怎么做产品

我通常从一个不太漂亮、但很真实的问题开始：

```text
一个市场、用户或风险信号
        ↓
把它变成可以复现的问题
        ↓
写清假设、权限与失败边界
        ↓
做出最小但完整的产品闭环
        ↓
评测、找失败、设计人工复核
        ↓
公开数字，也公开数字在哪里失效
```

| 构建 | 验证 | 沟通 |
| --- | --- | --- |
| Python、TypeScript、SQL、FastAPI、React、AWS Serverless、DuckDB、Solidity、Git | 指标树、规则与模型评测、置信度与失败分析、审计轨迹、脱敏、限流、可用性测试 | PRD、流程设计、对话式界面、中英文演示、验收与复盘 |

我使用 Codex 和 Claude Code 协助构思，以及生成代码与测试初稿。产品判断、验证设计、可复现性和
真实性边界由我负责。

## 我从哪里来

- **华泰国际｜金融科技实习，2024.07–2024.11**  
  参与区块链金融产品的迭代与上线协调；从用户价值、可行性、风险和成本角度评估 AI 风险、
  CBDC、DLT、DeFi 与数字人等方向。
- **AI Star｜天使投资人与联合创始人，2022–至今**  
  负责早期教育产品的用户分层、定价与单位经济模型、功能优先级和合作方沟通。
- **红杉资本｜投资分析实习，2024.01–2024.05**  
  从客户需求、商业化和技术趋势出发，研究数十家网络安全企业。
- **奇绩创坛｜校园寻访，2023.03–2023.08**  
  寻找并筛选早期项目，与创始人讨论痛点、差异化和验证路径。
- **其他成果**  
  全国创新创业挑战赛一等奖及最佳创业奖（跨境电商方向）；百威数字化转型研究，
  [DOI 10.54691/bcpbm.v38i.3909](https://doi.org/10.54691/bcpbm.v38i.3909)。

## 公开范围

公开仓库只包含适合公开的代码、架构、评测与示例。团队所有的实现、凭证、私有数据和受限配置
不会公开。除非另有说明，演示数据均为合成数据。完整工作与教育经历可直接向招聘方提供。

---

<p align="center">
  正在寻找深圳、香港、新加坡及其他主要科技与金融中心的金融科技 / AI 产品岗位。<br>
  如果你也在思考 AI 应该做什么、又应该在哪里停下，欢迎联系我。
</p>
