# RISC-V 开放规范中文译文索引

本目录保存 `docs/references/riscv/` 下 RISC-V 开放规范参考 PDF 的中文 Markdown 译文。翻译按基础规范优先推进：先非特权 ISA，再特权架构、Vector、Bit-Manipulation、External Debug 和 Processor Trace。

## 文档清单

| 中文译文 | 对应源文件 | 当前状态 |
|---|---|---|
| [RISC-V 非特权 ISA 中文译文](unprivileged-isa.md) | `The_RISC-V_Instruction_Set_Manual_Volume_I_Unprivileged_ISA_TD004_20191213.pdf` | 正文译文稿已完成第一版，覆盖核心章节、主要扩展、表格化指令语义和扩展组织 |
| [RISC-V 特权架构中文译文](privileged-architecture.md) | `The_RISC-V_Instruction Set_Manual_Volume_II_Privileged_Architecture_TD005_V20190608.pdf` | 正文译文稿已完成第一版，覆盖特权级、CSR、trap、中断、PMP、计时器和虚拟内存 |
| [RISC-V Vector 扩展中文译文](vector-extension.md) | `RISC-V_Vector_ISA-extensions_V1.0.pdf` | 正文译文稿已完成第一版，覆盖 Vector 模型、配置、访存、算术、归约、排列、异常和 ABI |
| [RISC-V Bit-Manipulation 扩展中文译文](bit-manipulation-extension.md) | `RISC-V_Bit-Manipulation_ISA-extensions_TD013_V1.0.0-38-g865e7a7.pdf` | 正文译文稿已完成第一版，覆盖 Zba/Zbb/Zbc/Zbs、逐条指令语义、软件用途和实现注意事项 |
| [RISC-V External Debug 中文译文](external-debug.md) | `RISC-V_External Debug_Support_TD003_V0.13.pdf` | 正文译文稿已完成第一版，覆盖 DM/DTM、hart 控制、abstract command、program buffer、SBA、trigger 和调试流程 |
| [RISC-V Processor Trace 中文译文](processor-trace.md) | `RISC-V_Processor_Trace_TD010_V1.0.pdf` | 正文译文稿已完成第一版，覆盖 trace 模型、encoder/sink、packet、过滤、decoder 和实现注意事项 |

## 翻译约定

- 译文是中文正文译文稿，不复制英文原文长段内容。
- 原 PDF 保持不变；如中文译文与源规范存在差异，以源 PDF 为准。
- 指令名、CSR 名、扩展名、寄存器名和规范关键词通常保留英文或代码形式。
- `unprivileged` 译作“非特权”，`privileged` 译作“特权”，`vector` 译作“向量/Vector”，`debug` 译作“调试”，`trace` 译作“跟踪/Trace”，`bit-manipulation` 译作“位操作/Bit-Manipulation”。

## 后续翻译范围

6 份中文 Markdown 均已完成正文译文稿第一版。后续可继续做逐表逐字段校对、与源 PDF 页码对照、术语统一和示例补强。
