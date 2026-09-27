# Contributing

Thanks for helping this list stay sharp. 谢谢帮助维护本列表。中文说明在下半部分。

## The bar for an entry

1. **Primary sources only.** Link the arXiv abs page, the official repo, or the official lab blog — not aggregators, not tweets, not secondhand summaries.
2. **One line of "why it matters."** What does this actually demonstrate? Be specific (a number, a mechanism), not promotional.
3. **An honest label.**
   - 🔁 **True RSI** — the mechanism that produces improvements is itself improved by the system.
   - 🔄 **Bounded SI** — persistent self-improvement through a fixed operator (memory, skills, self-training).
   - 🧩 **Enabler** — harness / benchmark / infrastructure / analysis that such systems build on.
4. **In scope:** self-improvement for software-engineering ability. If your entry is general RSI, embodied RSI, or self-evolving agents broadly, consider the [related lists](README.md#related-lists) instead.

## Checklist for PRs

- [ ] Added to the right section in **both** `README.md` and `README.zh-CN.md` (keep the two in sync).
- [ ] Link resolves (no 404) — yes, please actually click it.
- [ ] Label assigned and defensible.
- [ ] One-line description, English in `README.md`, 中文在 `README.zh-CN.md`。

Keyword tuning for the [radar](scripts/radar.py) is also welcome — keep precision high, noise low.

## 贡献指南（中文）

**收录门槛：**

1. **只链一手来源**——arXiv 页面、官方仓库或官方实验室博客；不收聚合站、推特转述或二手总结。
2. **一句话说明意义**——具体（一个数字、一个机制），不要宣传腔。
3. **诚实的标签**：🔁 真递归（改进器本身被改进）/ 🔄 有界自改进（固定算子的持久改进）/ 🧩 支撑件（harness、基准、基础设施、分析）。
4. **范围**：面向软件工程能力的自改进。泛 RSI、具身 RSI、广义自进化智能体请投[相邻列表](README.zh-CN.md#相邻列表)。

**PR 检查项：** 中英两个 README 同步更新；链接实际点开过；标签站得住；一句话描述中英各一份。也欢迎调整[雷达](scripts/radar.py)的关键词——保持高精度、低噪声。
