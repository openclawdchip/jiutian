# 移植指南

本文档说明如何把九天 v0.1 模型迁移到新的运行环境、测试环境或后续硬件原型中。

## 移植目标

- 保持 APU-IR 语义不变。
- 保持 task/capability 边界不变。
- 保持 trace 可比对。
- 保持 benchmark 输入可复现。

## 适配步骤

1. 实现 memory region 与 capability 检查。
2. 实现 SPM 与 Cluster SRAM 访问。
3. 实现 DMA copy 与 wait。
4. 实现 barrier。
5. 实现 trap、timeout 与清理。
6. 对齐 trace 输出。
7. 跑通最小示例和单元测试。

## 验证清单

- copy_add 输出正确。
- cluster_barrier 输出正确。
- capability 越界会 trap。
- barrier deadlock 可检测。
- cycle budget 可强制。
