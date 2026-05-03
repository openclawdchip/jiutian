# zhuque / 朱雀

本目录是 `zhuque / 朱雀` 的工程目录。

`zhuque` 是模块顶层 codename，中文名统一使用 `朱雀`。本目录用于定义并实现朱雀自己的文档、行为模型、RTL 与验证资产。

## 当前状态

当前阶段以文档建设为主。

- 已完成：总体架构文档、分域文档、模块级文档目录、工程原则、推进路线
- 未开始：行为模型代码
- 未开始：RTL 代码

## 工程原则

- 顶层命名统一使用 `zhuque`
- 中文名统一使用 `朱雀`
- 先文档，后行为模型，最后 RTL
- 文档按模块拆分，不合并为单一大文档
- 行为模型优先表达架构语义，不追求结构照抄
- RTL 以可读、可验证、可维护为第一目标

## 目录

- `docs/`
  - 新生成的设计文档体系
- `docs/domains/`
  - 按功能域拆分的一级与模块级规格
- `docs/plans/`
  - 端到端推进路线和阶段计划

## 建议阅读顺序

1. `docs/zhuque-architecture-overview.md`
2. `docs/zhuque-engineering-principles.md`
3. `docs/plans/zhuque-fullstack-roadmap.md`
4. `docs/domains/` 下的各域模块文档
