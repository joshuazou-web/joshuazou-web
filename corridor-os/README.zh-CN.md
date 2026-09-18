# CorridorOS

**中国—新加坡跨境支付运营平台**

一家中国企业在新加坡设立主体之后，要完成企业准入、SGD 收款、FX、供应商付款、
风险检查、AML 调查、结算与对账——并且每一笔资金和每一个合规决定，都要能说清
用了哪些证据、谁有权决定。

这是同一个运营问题。CorridorOS 把我原来的四个项目围绕它重建成一个系统。

> ### ⚠️ 这里的每一家企业、供应商、付款、单据、金额和结果都是合成数据
> 由固定种子生成。CorridorOS 从未在生产环境运行，没有任何牌照，没有银行或
> 通道合作方，也从未为任何人处理过一笔真实付款。详见
> [真实性与局限](docs/TRUTH_AND_LIMITATIONS.md)。

## 这个系统为之存在的那笔付款

深圳企业的新加坡实体向供应商支付 **SGD 12,500**，而该供应商 6 天前改过银行账户。

```
business.submitted → business.approved   必备文件缺失时，KYB 审批直接拒绝
payment.created                          SGD 12,500，发票 INV-4821，采购单 PO-4821
beneficiary.changed                      账户 ...4417 → ...8830，发生在 6 天前
risk.assessed                            4 条确定性信号，band critical，无模型参与
intervention.required                    第 4 级：双人审批 + 回拨核验
case.opened                              优先级 1——付款被挂起
   ⟶ 有人要求 copilot 直接批准。被拒绝，并且这条拒绝记录进了审计链。
payment.approved                         两名不同审批人；同一人第二次审批被拒
payment.submitted → payment.settled      扣除 SGD 9.80 手续费后净额 SGD 12,490.20
                                         三方对账通过，25 条审计链校验通过
```

运行：`python -m corridoros.cli demo`。上面每一行都是对平台的真实调用，中间的
拒绝也是真的——把回拨核验去掉，审批就会抛异常。

## 四个项目变成了什么

| 原来 | 现在 | 变化 |
| --- | --- | --- |
| **[China-to-Singapore Payment Corridor](../portfolio/china-to-singapore-payment-corridor.zh-CN.md)**（两篇 Markdown，零代码） | `payments/` **Payment Core** | 把 blueprint 真正实现：KYB、收款、复式账本、带过期的 FX、付款状态机、结算、三方对账 |
| **CrossBorder AML RiskOps** | `risk/` + `core/audit.py` | 六种 AML 典型模式、告警去重、案件聚合与八因子优先级，现在跑在本平台自己的资金流上；它的金额算术、哈希链、AI guardrails 升级为全平台基础设施 |
| **WealthGuard Proofline** | `evidence/` **Evidence & Policy Copilot** | 方法保留、主题更换：为 KYB、付款审核和调查提供带校验和、带定位、可引用的证据 |
| **ThinkBeforeClick FinSafe** | `intervention/` **Pre-payment Intervention Engine** | 同一套干预阶梯，输入换成真实的付款指令、风险评估和证据状态，而不是粘贴的文本 |

四个原仓库保持不变。这是它们加起来的那个系统，而不是并排的第五个项目。
迁移细节见 [MIGRATION.md](docs/MIGRATION.md)。

## 设计原则

> **规则负责判断，AI 负责解释和整理证据，人负责最终决策，每一步都留痕。**

AI 可以做的六件事：整理证据包、生成案件摘要、指出缺失资料、带引用回答问题、
起草补件通知、证据不足时弃权。

AI 绝对不能做的六件事：批准 KYB、修改账本、执行 FX、提交或放行付款、
清除 AML 预警、关闭调查案件或异常。

第二份清单由四道互相独立的机制强制：权限矩阵拒绝、`ApprovalDecision` 拒绝其
作为决定人、审计日志拒绝并记录该次尝试，以及——它的输出对象**根本没有可以
写入决定的字段**。详见 [AI_BOUNDARIES.md](docs/AI_BOUNDARIES.md)。

## AML 层

`risk/` 下是两层确定性逻辑：**21 条规则**作用于单笔付款，**6 种 AML 典型模式**作用于被监控的资金流——
后者是平台自己已结算的movements加上合成的走廊人口，所以那笔 SGD 12,500 就出现在检测器读取的同一个世界里。
详见[规则与模式目录](docs/AML_RULE_CATALOG.md)。

```
331 条告警 → 去重后 109 条 → 30 个案件 → 今天团队能开 12 个 → 18 个在等
```

最后一个数字才是重点：**产能线以下的案件没有被清掉，只是没有被看**，而且有多少植入模式正躺在这个积压里，
是评测的表头行，不是被省略的脚注。

| 合成评测，三个独立种子世界 | |
| --- | --- |
| 召回率（明显落在阈值内的模式） | **1.000 ± 0.000** |
| 召回率（刚好贴着阈值的模式） | **0.875 ± 0.000** |
| 原始告警精确率 | **0.162 ± 0.016** |
| 产能线内精确率 | **0.833 ± 0.068** |
| 留在积压里的植入模式 | **8 个** |

检测器永远看不到生成器的标签——`MonitoringContext.blind()` 会剥掉，构造函数遇到仍带标签的数据直接抛异常——
所以召回率测的是检测能力，而不是把标签复述一遍。人口是刻意加料过的，因此两个数字都不能迁移到真实流量。

优先级是排序而不是判决：八个因子、权重和为 1.0、每一项贡献都显示在案件旁边，
因为不认同这个排序的调查员必须看得到是哪个因子把它推上来的。

## 七个端到端场景

`tests/e2e/test_scenarios.py`：正常付款 · 收款账户变更 · 重复付款 · 可疑交易 ·
FX 报价过期 · Webhook 重复或乱序 · 对账金额不一致。共 124 个测试，
领域层不依赖任何第三方库。

## 运行

```bash
pip install -e '.[dev]'
python -m corridoros.cli demo          # 主线演示
python -m corridoros.cli aml           # 跑一天的交易监控
python -m corridoros.cli aml-eval      # 生成 reports/aml_evaluation.json
python -m corridoros.cli boundary      # 打印 AI 权限边界
python -m corridoros.cli verify-audit  # 重算哈希链
python -m pytest                       # 全部测试

python -m corridoros.cli snapshot      # 生成 data/snapshot.json
cd apps/web && npm install && npm run build   # 统一前端（静态可部署）
```

## 尚未完成的部分

P3 阶段将 WealthGuard 的 13 份官方文件、1,714 个带校验和的证据块并入证据库，并在这里重跑它的
引用可追溯评测。当前证据库里的是演示自己产生的合成发票、采购单、回拨记录与变更授权函。

规则集是**改写而非照搬**：RiskOps 20 条收单规则中有 11 条换了主体后保留，10 条卡收单专属规则被走廊
场景的等价规则替换，另加 1 条指令文本规则。因此它原来的召回率与精确率并不迁移，评测文档把两套数字
分开陈列。

来自四个原项目的评测数字均标注了出处项目与数据集，不作为 CorridorOS 的结果重述。
见 [EVALUATION.md](docs/EVALUATION.md)。
