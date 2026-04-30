# 文档地图

本文档定义九天文档体系的分层。新增文档时应优先放入对应层级，避免 README 变成所有内容的堆叠入口。

## 第一层：项目入口

- `README.md`：项目首页、对标叙事、最快运行路径。
- `docs/product-brief.md`：面向新读者的产品简介。
- `docs/datasheet.md`：v0.1 数据手册。
- `docs/whitepaper.md`：完整架构叙事与技术主张。

## 第二层：架构说明

- `docs/architecture.md`：控制面与 Agent 执行面。
- `docs/memory-noc.md`：存储与 NoC。
- `docs/security.md`：安全模型。
- `docs/execution-model.md`：任务生命周期和调度模型。
- `docs/glossary.md`：术语表。

## 第三层：规格

- `specs/jiutian-apu-v0.1.md`：总规格入口。
- `specs/isa-v0.1.md`：Agent ISA。
- `specs/apu-ir-v0.1.md`：APU-IR。
- `specs/task-model-v0.1.md`：任务模型。
- `specs/memory-map-v0.1.md`：地址空间。
- `specs/debug-trace-v0.1.md`：调试与 trace。
- `specs/peripheral-model-v0.1.md`：最小外设模型。

## 第四层：工程流程

- `docs/quick-start.md`：快速开始。
- `docs/environment.md`：环境要求。
- `docs/configuration-flow.md`：配置与生成流程。
- `docs/filelists-and-manifests.md`：文件清单。
- `docs/generated-artifacts.md`：生成物说明。
- `docs/release-notes.md`：发布说明。

## 第五层：验证与模拟

- `docs/simulator-guide.md`：模拟器指南。
- `simulator/docs/cli.md`：模拟器 CLI。
- `docs/testcase-organization.md`：测试组织。
- `docs/benchmark-methodology.md`：benchmark 方法。
- `specs/v0.1/implementation-coverage.md`：实现覆盖矩阵。

## 第六层：扩展与维护

- `docs/porting-guide.md`：移植指南。
- `docs/troubleshooting.md`：故障排查。
- `docs/waveform-and-trace.md`：trace 与波形。
