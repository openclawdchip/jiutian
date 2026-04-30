# RISC-V 开放规范中文译文索引

本目录保存 `docs/references/riscv/` 下 RISC-V 开放规范参考 PDF 的中文 Markdown。当前顶层 6 份专题 Markdown 是正文级浓缩译稿，不是严格全文翻译。严格全文翻译从 `full/` 子目录重新按源 PDF 章节推进。

## 文档清单

| 中文译文 | 对应源文件 | 当前状态 |
|---|---|---|
| [RISC-V 非特权 ISA 浓缩译稿](unprivileged-isa.md) | `The_RISC-V_Instruction_Set_Manual_Volume_I_Unprivileged_ISA_TD004_20191213.pdf` | 非严格全文；严格全文见 [full/unprivileged-isa/](full/unprivileged-isa/) |
| [RISC-V 特权架构浓缩译稿](privileged-architecture.md) | `The_RISC-V_Instruction Set_Manual_Volume_II_Privileged_Architecture_TD005_V20190608.pdf` | 非严格全文；严格全文见 [full/privileged-architecture/](full/privileged-architecture/) |
| [RISC-V Vector 扩展浓缩译稿](vector-extension.md) | `RISC-V_Vector_ISA-extensions_V1.0.pdf` | 非严格全文；严格全文见 [full/vector-extension/](full/vector-extension/) |
| [RISC-V Bit-Manipulation 扩展浓缩译稿](bit-manipulation-extension.md) | `RISC-V_Bit-Manipulation_ISA-extensions_TD013_V1.0.0-38-g865e7a7.pdf` | 非严格全文；严格全文见 [full/bit-manipulation-extension/](full/bit-manipulation-extension/) |
| [RISC-V External Debug 浓缩译稿](external-debug.md) | `RISC-V_External Debug_Support_TD003_V0.13.pdf` | 非严格全文；严格全文见 [full/external-debug/](full/external-debug/) |
| [RISC-V Processor Trace 浓缩译稿](processor-trace.md) | `RISC-V_Processor_Trace_TD010_V1.0.pdf` | 非严格全文；严格全文见 [full/processor-trace/](full/processor-trace/) |

## 翻译约定

- 译文是中文正文译文稿，不复制英文原文长段内容。
- 原 PDF 保持不变；如中文译文与源规范存在差异，以源 PDF 为准。
- 指令名、CSR 名、扩展名、寄存器名和规范关键词通常保留英文或代码形式。
- `unprivileged` 译作“非特权”，`privileged` 译作“特权”，`vector` 译作“向量/Vector”，`debug` 译作“调试”，`trace` 译作“跟踪/Trace”，`bit-manipulation` 译作“位操作/Bit-Manipulation”。

## 严格全文译文

严格全文译文位于 [`full/`](full/) 子目录。当前 6 份 RISC-V 开放规范均已完成严格全文初译，按源 PDF 章节拆分为 Markdown 文件。
