<p align="left">
  <a href="README.md">English</a> · <strong>中文</strong>
</p>

<h1 align="center">邹志华 Josh — 金融科技 AI 产品</h1>

<p align="center">
  我为金融风险、交易与运营场景做 AI 产品，并把评测证据和它的边界一起公开。<br>
  新加坡 · 新加坡国立大学 数字金融科技硕士（2027 年 1 月毕业） · 中文 / 英文
</p>

<p align="center">
  <a href="mailto:zouzhihuajosh@outlook.com">邮箱</a> ·
  <a href="https://www.linkedin.com/in/zouzhihuajosh">LinkedIn</a> ·
  <a href="https://github.com/joshuazou-web?tab=repositories">全部仓库</a> ·
  <a href="ABOUT_JOSH.md">作品集之外</a>
</p>

<img align="right" width="150" src="assets/avatar-josh-500.png" alt="" />

## 我做什么

我把模糊的金融、用户与风险问题，转化成别人可以复核的产品决策：明确的规则、能跑起来的原型，
以及一个说清楚了适用边界的数字。

- **AI 产品判断。** 在 LLM、Agent、RAG 的能力边界上判断 AI 到底带来多少增量价值——用准确率、
  置信度、失败分析、人工复核和用户信任来衡量，而不是用 demo 的精致程度。
- **风险与金融领域。** 把信用风险、市场风险和运营风险写成明确的策略：阈值、闸门、兜底、对账。
- **证据与诚实的边界。** 下面每个项目都带自己的数字，并且说明这些数字在哪里不再成立。

<br clear="right" />

## 从哪里开始看

不同团队需要不同的证据。找到和你岗位对应的那一行：

| 如果你在招 | 建议从这几个开始 |
| --- | --- |
| **金融科技 / AI 产品** | [Risk-Based DeFi Lending](#1-金融科技风险交易与借贷) · [Algorithmic FX](#1-金融科技风险交易与借贷) · [OpsSignal](#3-数据运营与信任产品) |
| **AI 产品经理** | [Converge](#2-agent评测与可靠性) · [Volc Agent Launchpad](#2-agent评测与可靠性) · [OpsSignal](#3-数据运营与信任产品) |
| **技术产品经理 / AI 工程** | [DecisiveEval](#2-agent评测与可靠性) · [Agent Control Plane](#2-agent评测与可靠性) · [DEBUG.CN](#4-开发者体验与-ai-工具) |
| **数据与运营 / BizTech** | [OpsSignal](#3-数据运营与信任产品) · [ThinkBeforeClick](#3-数据运营与信任产品) |

同一个项目出现在多行是有意为之——说明这份工作承载了不止一种证据。

## 按能力分类的作品

### 1. 金融科技：风险、交易与借贷

**证明的能力：** 把市场风险和信用风险，变成明确、可测试的产品规则。

*领域基础：* 新加坡国立大学 数字金融科技硕士 · **华泰国际** 金融科技实习——区块链金融产品的
智能合约、后端、验收与异常流程，用 Python/SQL 做校验与对账 · **红杉资本** 投研实习，研究网络
安全赛道。

| 项目 | 证明了什么 | 证据 |
| --- | --- | --- |
| **Risk-Based DeFi Lending**<br>[案例](https://github.com/joshuazou-web/risk-based-defi-lending-case-study) · [演示](https://joshuazou-web.github.io/risk-based-defi-lending-case-study/) | 把外部风险信号变成明确的 LTV、利率、清算阈值与健康因子策略 | Python/Flask 评分服务、成文的信任边界、精选代码、可交互演示 |
| **Algorithmic FX Trading & Monitoring**<br>[案例](https://github.com/joshuazou-web/algorithmic-fx-product-case) · [演示](https://joshuazou-web.github.io/algorithmic-fx-product-case/) | 能经受因果验证和换手成本检验的市场状态逻辑 | 因果回测、监控设计、fail-closed 的模拟执行 |
| **SoAI 2026 High-Beta Leader**<br>[仓库](https://github.com/joshuazou-web/SoAI-2026-High-Beta-Leader) | 在比赛规则下先冻结策略，而不是事后拟合 | 冻结的 high-beta leader 策略，SoAI 2026 AI 算法交易大赛参赛作品 |

### 2. Agent、评测与可靠性

**证明的能力：** 判断什么时候*不该*用 LLM，以及证明一个 Agent 在压力下的真实表现。

| 项目 | 证明了什么 | 证据 |
| --- | --- | --- |
| **Converge** — 主动澄清与推荐<br>[仓库](https://github.com/joshuazou-web/techjam-converge) | 用逆向用户模型和显式任务状态刻画不完整、会变化的意图；基于期望信息增益的澄清与置信度门控的推荐 | 官方 200 轮会话评测 **0.976 对比基线 0.107**；28 个测试，消融与压力检查。在可解释规则足够的地方刻意不用 LLM。*边界：限定于封闭品类和合成用户，不代表真实转化或留存。* |
| **Volc Agent Launchpad** — Agent 安全与审计<br>[仓库](https://github.com/joshuazou-web/volc-agent-launchpad) | 把提示注入、权限提升和危险命令风险，映射到放行 / 拦截 / 转人工三态的三层护栏 | **138 通过，1 跳过**；8 个演示场景、误报语料、审计轨迹，类型检查与生产构建均通过。*边界：这是原型，不等于完整的攻击覆盖。* |
| **DecisiveEval**<br>[仓库](https://github.com/joshuazou-web/decisive-eval) | 一个 Coding Agent 的结论，能否在评分、运行时、失败处理、成本与延迟策略发生合理变化后依然成立 | 26 个公开 JSON Schema、103 个测试、不可变证据回执、重复运行与自助采样路径。*同时公开失败的实验，并明确保留真实世界验证这一未决问题。* |
| **Agent Control Plane**<br>[仓库](https://github.com/joshuazou-web/agent-control-plane) | Agent 工作流中可被机器校验的授权与审批闸门 | 只追加的执行轨迹、可恢复的任务目录、可复现的"提议-检查-执行-记录-升级"示例 |
| **PropTech Agent Reliability Lab**<br>[仓库](https://github.com/joshuazou-web/proptech-agent-reliability-lab) | 面向真实客户问题去调试 Agent 的失败 | 基于 FastAPI + Streamlit 的合成 PropTech 练习场 |

### 3. 数据、运营与信任产品

**证明的能力：** 把一条工作流埋点量化，然后有意识地把不确定性交回给人。

| 项目 | 证明了什么 | 证据 |
| --- | --- | --- |
| **OpsSignal** — 运营分析与人机协作工作流<br>[仓库](https://github.com/joshuazou-web/opssignal) | 出于成本、可控性和可解释性选择可解释模型而非 LLM，并用复核队列把模型的不确定性暴露出来 | **留出集准确率 0.842，Macro-F1 0.836**；在 0.65 阈值下 **自动覆盖率 84.0%、一致率 92.3%**。3,600 条合成工单归入 6 个维度、51 个取值、21 张 mart 表；19 项校验与 166 个测试通过。 |
| **ThinkBeforeClick** — 反诈学习产品<br>[案例](https://github.com/joshuazou-web/think-before-click-product-case) · [演示](https://joshuazou-web.github.io/think-before-click-product-case/) | 把学习者反馈与企业侧分析连起来，并配有负责任的防护措施；5 人团队在 AWS 上交付 | 23 人课程测试：**可用性 4.3/5、个人满意度 4.2/5、企业参与者满意度 4.5/5**；NUS STePS 优异奖（2025）。*边界：仅为课程样本。* |

### 4. 开发者体验与 AI 工具

**证明的能力：** 把别人的失败讲清楚——用两种语言。

| 项目 | 证明了什么 | 证据 |
| --- | --- | --- |
| **DEBUG.CN** — 中文 OpenAI API 排错助手<br>[仓库](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot) · [演示](https://ctkhkof0ez.feishuapp.com/app/app_17c3qmjxcq2) · [3 分钟双语视频](https://github.com/joshuazou-web/mandarin-openai-api-debugging-copilot/releases/download/v0.1.0/DEBUG-CN-3min-bilingual-demo-subtitled.mp4) | 把 API 与 SDK 的失败，变成可复核的证据、根因、最小修复和验证步骤 | 8 类错误、24 个后端测试、20/20 公开评测；服务端密钥脱敏、确定性兜底、源码级的频率与 token 控制。*边界：Structured Outputs 路径已实现，真实模型验证待账户配额。* |
| **白盒 · wbox** — 面向学生的答辩陪练<br>[仓库](https://github.com/joshuazou-web/wbox) | 帮学生真正搞懂他们即将答辩的、用 AI 做出来的课程项目 | 中文优先的产品：被问预测、问答演练、汇报包 |

## 我的工作方式

```text
市场、用户或风险信号
    -> 可复现的问题
    -> 明确的假设与能力边界
    -> 最小可用原型
    -> 评测、失败分析、人工复核
    -> 写明边界，进入下一轮
```

| 构建 | 验证 | 沟通 |
| --- | --- | --- |
| Python、TypeScript、SQL、FastAPI、React、AWS Serverless、DuckDB、Solidity、Git | 指标树、埋点与漏斗、规则与模型评测、置信度与失败分析、脱敏、频率限制、审计轨迹、可用性测试 | PRD 与流程、对话式界面、中英文演示与快速上手、验收与复盘 |

我用 Codex 和 Claude Code 做构思以及代码和测试的初稿。产品决策、可复现性和真实性边界由我自己负责。

## 经历信号

- **华泰国际** — 金融科技实习（2024 年 7 月–11 月）。参与一款区块链金融产品的迭代与上线协调；
  从用户价值、可行性、风险和成本角度评估 AI 风险、CBDC、DLT、DeFi 与数字人等方向。
- **AI Star** — 天使投资人与联合创始人（2022 年至今）。为一款早期教育产品做用户分层、定价与
  单位经济模型、功能优先级和合作方沟通。
- **红杉资本** — 投研实习（2024 年 1 月–5 月）。从客户需求、商业化和技术趋势三个角度研究了
  数十家网络安全公司。
- **奇绩创坛** — 校园寻访（2023 年 3 月–8 月）。寻找并筛选早期项目；与创始人访谈，评估痛点、
  差异化与验证路径。
- **获奖与发表** — 全国创新创业挑战赛一等奖及最佳创业奖（澳门跨境电商方向）；百威数字化转型
  研究，[DOI 10.54691/bcpbm.v38i.3909](https://doi.org/10.54691/bcpbm.v38i.3909)。

## 公开范围说明

公开仓库中的代码、架构、验证与示例均已做过可公开处理。团队所有的实现、凭证、私有数据和受限
配置不会公开。除非另有说明，演示数据均为合成数据。完整的工作与教育经历可直接向招聘方提供。

---

<p align="center">
  正在寻找深圳、香港、新加坡以及其他主要科技与金融中心的金融科技 / AI 产品岗位，2027 年 1 月毕业。
</p>
