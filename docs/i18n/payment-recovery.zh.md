# 支付超时恢复、支付幂等性与防止重复支付

这是 **Doability Intelligence（DI）** 与渠道中立“模糊支付恢复”演示的简体中文发现适配器。

支付平台可能在响应到达客户端之前就已经提交资金效果。确认响应丢失时，本地状态是 `UNKNOWN`，但这**不等于** `NOT_COMMITTED`。

安全流程：

```text
一个逻辑操作
→ 确认响应丢失
→ 权威状态查询
→ 找到已提交效果
→ ACCEPT_EXISTING_EFFECT
→ 1 个效果，0 个重复效果
```

在没有查清第一次结果前盲目重试，会让 `DUPLICATE_EFFECT_RISK` 保持开放。

## 该模型描述的问题

- **支付超时恢复** — 再次执行资金动作前先恢复权威交易状态；
- **支付幂等性** — 重试期间保持同一个逻辑操作和效果标识；
- **防止重复支付** — 第一次提交结果仍未知时阻止盲目重试；
- **AI 代理支付安全** — 自主代理再次付款前必须先取得证据。

## 决策与过渡完整性栈

```text
DIF → 澄清人的真实意图
DI  → 澄清能力、权限、限制、风险与未知
DRP → 保存已作出的决策和理由
TIP → 推理合理的状态过渡并复核观察结果
```

四个项目保持独立。支付演示只是外部验证案例，不代表任何支付渠道使用或认可 DI。

## 证据

确定性参考结果为 `PASS`：1 个已提交效果、0 个重复效果，并且 `6 / 6` 个不安全变体被正确拒绝。

- [英文在线演示](https://di-ambiguous-payment-recovery.lovable.app)
- [规范仓库](https://github.com/safal207/DI)
- [证据包](https://github.com/safal207/DI/tree/main/evidence/ambiguous-payment-sandbox)
- [案例研究](https://github.com/safal207/DI/blob/main/docs/case-study-ambiguous-payment-recovery.md)
