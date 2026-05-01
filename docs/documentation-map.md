# 文档地图

本文档定义九天文档体系的分层。新增文档时应优先放入对应层级，避免 README 变成所有内容的堆叠入口。

## 第一层：项目入口

- `README.md`：项目首页、对标叙事、最快运行路径。
- `docs/product-brief.md`：面向新读者的产品简介，说明 v0.1 第一版目标、模拟器最小闭环和长期记忆闭环边界。
- `docs/blog-agent-long-term-memory.md`：面向 Agent 长任务记忆问题的技术博客。
- `docs/textbook-agent-cpu-architecture.md`：Agent CPU 体系结构学科定义与教材草案。
- `docs/datasheet.md`：v0.1 数据手册。
- `docs/whitepaper.md`：完整架构叙事与技术主张。

## 第二层：架构说明

- `docs/architecture.md`：控制面与 Agent 执行面。
- `docs/memory-noc.md`：存储与 NoC。
- `docs/security.md`：安全模型。
- `docs/execution-model.md`：任务生命周期和调度模型。
- `docs/glossary.md`：术语表。

## 第三层：规格

- `specs/jiutian-apu-v0.1.md`：总规格入口，定义 v0.1 的最小架构目标与长期任务记忆语义。
- `specs/isa-v0.1.md`：Agent ISA。
- `specs/apu-ir-v0.1.md`：APU-IR。
- `specs/task-model-v0.1.md`：任务模型、capability、预算、异常与长期记忆候选结果边界。
- `specs/memory-map-v0.1.md`：地址空间，以及 ledger、artifact、trace 等规划空间。
- `specs/debug-trace-v0.1.md`：调试与 trace，包括长期记忆投影任务的可观测事件。
- `specs/peripheral-model-v0.1.md`：最小外设模型。

## 第四层：工程流程

- `docs/quick-start.md`：快速开始。
- `docs/environment.md`：环境要求。
- `docs/development-sequence.md`：文档、规格、模拟器、benchmark 与 RTL 的推进顺序。
- `docs/configuration-flow.md`：配置与生成流程。
- `docs/filelists-and-manifests.md`：文件清单。
- `docs/generated-artifacts.md`：生成物说明。
- `docs/release-notes.md`：发布说明。

## 第五层：验证与模拟

- `docs/simulator-guide.md`：模拟器指南，说明当前可运行的 v0.1 功能模型。
- `simulator/docs/cli.md`：模拟器 CLI。
- `docs/testcase-organization.md`：测试组织。
- `docs/benchmark-methodology.md`：benchmark 方法。
- `benchmarks/long_task_memory.md`：长期任务记忆 benchmark 契约和离线校验命令。
- `specs/v0.1/implementation-coverage.md`：实现覆盖矩阵，用于区分已实现、部分实现、未实现和待定义语义。

当前文档入口应避免把“长期记忆闭环”误写成已经完整落地的模拟器能力。准确表述是：长期记忆已经进入 v0.1 规格、地址空间、任务模型和 trace 设计；当前模拟器先提供 APU-IR 到执行、同步、异常、trace 和结果导出的最小闭环。

## 第六层：扩展与维护

- `docs/porting-guide.md`：移植指南。
- `docs/troubleshooting.md`：故障排查。
- `docs/waveform-and-trace.md`：trace 与波形。
- `docs/references/riscv/`：RISC-V 开放规范参考。
