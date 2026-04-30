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
| host_init | 已实现 | 初始化 host memory |
| dump_words | 已实现 | 输出指定地址结果 |

## 未实现或待增强

- 异步 DMA 队列。
- 多 cluster NoC 延迟。
- 更细粒度资源预算。
- 稳定 trace schema。
- RTL 参数生成。
