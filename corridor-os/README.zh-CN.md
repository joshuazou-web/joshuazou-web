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
| **CrossBorder AML RiskOps** | `risk/` + `core/audit.py` | 改为读取平台事件，不再自造世界；它的金额算术、哈希链、AI guardrails 升级为全平台基础设施 |
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

## 七个端到端场景

`tests/e2e/test_scenarios.py`：正常付款 · 收款账户变更 · 重复付款 · 可疑交易 ·
FX 报价过期 · Webhook 重复或乱序 · 对账金额不一致。共 65 个测试，
领域层不依赖任何第三方库。

## 运行

```bash
pip install -e '.[dev]'
python -m corridoros.cli demo          # 主线演示
python -m corridoros.cli boundary      # 打印 AI 权限边界
python -m corridoros.cli verify-audit  # 重算哈希链
python -m pytest                       # 全部测试

python -m corridoros.cli snapshot      # 生成 data/snapshot.json
cd apps/web && npm install && npm run build   # 统一前端（静态可部署）
```

## 尚未完成的部分

P2 阶段将 RiskOps 的 20 条交易完整性规则与 6 种 AML 典型模式移植到本事件流上，
并带来分析师工作台与队列评测；P3 阶段将 WealthGuard 的 13 份官方文件、1,714 个
带校验和的证据块并入证据库。界面会明确标注当前运行的是哪一套信号集，不会暗示
AML 层已经就位。

来自四个原项目的评测数字均标注了出处项目与数据集，不作为 CorridorOS 的结果重述。
见 [EVALUATION.md](docs/EVALUATION.md)。
