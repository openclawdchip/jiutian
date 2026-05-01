# v0.1 实现覆盖矩阵

本文档记录规格与当前模拟器实现之间的对应关系。

## 状态定义

- 已实现：模拟器已有功能并有测试覆盖。
- 部分实现：功能存在，但语义仍简化。
- 未实现：规格已提出，但当前不可运行。
- 待定义：规格尚未稳定。

## ISA 覆盖

| 能力 | 状态 | 说明 |
|---|---|---|
| li/add/sub | 已实现 | 基本整数操作 |
| jmp/beqz | 已实现 | label 跳转 |
| load/store | 已实现 | 支持 spm 与 cluster |
| dma_copy/dma_wait | 部分实现 | 当前可按同步完成建模 |
| barrier | 已实现 | 支持参与者计数与释放 |
| flush/invalidate/fence | 部分实现 | 当前主要记录 trace |
| trap/halt | 已实现 | 支持异常与正常结束 |

## APU-IR 覆盖

| 字段 | 状态 | 说明 |
|---|---|---|
| version/name | 已实现 | 基础元数据 |
| config | 已实现 | 模拟器配置 |
| memory | 已实现 | memory region 与 capability 来源 |
| barriers | 已实现 | barrier 参与者声明 |
| tasks | 已实现 | 任务列表 |
| host_init | 已实现 | 支持 64-bit word、UTF-8 text 与 byte list 初始化 host memory |
| dump_words | 已实现 | 输出指定地址结果 |
| dump_regions | 已实现 | 输出 host 文本区域，供长期记忆候选结果校验 |
| ledger_versions/evidence_refs | 部分实现 | 作为长期记忆高层任务的输入元数据 |

## 长期任务记忆覆盖

| 能力 | 状态 | 说明 |
|---|---|---|
| ledger_delta_extract | 已实现 | 从授权 transcript/artifact preview region 提取 goal/plan/evidence/decision/recovery 候选 delta |
| recovery_anchor_select | 已实现 | 从授权 trace、artifact 或 candidate delta region 选择候选恢复点 |
| context_budget_pack/context_projection | 已实现 | 在 byte/token 预算内生成下一轮上下文投影 |
| candidate-only 安全边界 | 已实现 | 高层任务只写候选输出区，不修改 ledger_versions |
| 输出 region 边界 | 已实现 | JSON payload 超出 region 时写入截断标记或触发 overflow trap |
| evidence 强校验 | 部分实现 | 模拟器保留来源与引用结构；离线校验器会检查 benchmark 期望 delta 的 evidence 可解析 |
| 长期记忆离线校验器 | 已实现 | `tools/validate_long_task_memory.py` 校验 benchmark 契约样例 |
| Super Domain 提交流程 | 未实现 | 当前模拟器不执行 ledger commit，只模拟 Agent Domain 候选输出 |

## 未实现或待增强

- 异步 DMA 队列。
- 多 cluster NoC 延迟。
- 更细粒度资源预算。
- 稳定 trace schema。
- RTL 参数生成。

## 文档覆盖

| 文档族 | 状态 | 说明 |
|---|---|---|
| 产品简介 | 已建立 | 见 `docs/product-brief.md` |
| 数据手册 | 已建立 | 见 `docs/datasheet.md` |
| 地址空间 | 已建立 | 见 `specs/memory-map-v0.1.md` |
| 调试与 Trace | 已建立 | 见 `specs/debug-trace-v0.1.md` |
| 最小外设模型 | 已建立 | 见 `specs/peripheral-model-v0.1.md` |
