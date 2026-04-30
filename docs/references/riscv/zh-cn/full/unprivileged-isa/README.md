# RISC-V 非特权 ISA 严格全文翻译进度

源文档：`docs/references/riscv/The_RISC-V_Instruction_Set_Manual_Volume_I_Unprivileged_ISA_TD004_20191213.pdf`

本目录用于按源 PDF 的章节顺序进行严格中文全文翻译。这里的“全文”指逐章逐段翻译，保留原有章节、表格、字段、指令说明、伪代码语义和注释性说明；指令名、寄存器名、CSR 名、扩展名和必要字段名保持原文。

上一级 `zh-cn/unprivileged-isa.md` 是正文级浓缩译稿，不再标记为严格全文完成。

注：仓库内 20191213 版非特权 ISA PDF 未包含后续加入的 `Zfh`/`Zfhmin` 章节，且其 Chapter 14 为 RVWMO。`14-zfh.md` 保留为额外公开扩展译文，不替代本地 PDF 的 Chapter 14。

## 当前文件

| 顺序 | 文件 | 源范围 | 状态 |
|---|---|---|---|
| 00 | [00-preface.md](00-preface.md) | Preface，含当前版本和历史版本前言 | 严格全文初译完成 |
| 01 | [01-introduction.md](01-introduction.md) | Chapter 1 Introduction，1.1-1.7 | 严格全文初译完成 |
| 02 | [02-rv32i-base-integer.md](02-rv32i-base-integer.md) | Chapter 2 RV32I Base Integer Instruction Set，2.1-2.9 | 严格全文初译完成 |
| 03 | [03-zifencei.md](03-zifencei.md) | Chapter 3 `Zifencei` Instruction-Fetch Fence | 严格全文初译完成 |
| 04 | [04-rv32e.md](04-rv32e.md) | Chapter 4 RV32E Base Integer Instruction Set，4.1-4.2 | 严格全文初译完成 |
| 05 | [05-rv64i.md](05-rv64i.md) | Chapter 5 RV64I Base Integer Instruction Set，5.1-5.4 | 严格全文初译完成 |
| 06 | [06-rv128i.md](06-rv128i.md) | Chapter 6 RV128I Base Integer Instruction Set | 严格全文初译完成 |
| 07 | [07-m-extension.md](07-m-extension.md) | Chapter 7 `M` Standard Extension for Integer Multiplication and Division，7.1-7.2 | 严格全文初译完成 |
| 08 | [08-a-extension.md](08-a-extension.md) | Chapter 8 `A` Standard Extension for Atomic Instructions，8.1-8.4 | 严格全文初译完成 |
| 09 | [09-zicsr.md](09-zicsr.md) | Chapter 9 `Zicsr`, Control and Status Register (CSR) Instructions，9.1 | 严格全文初译完成 |
| 10 | [10-counters.md](10-counters.md) | Chapter 10 Counters，10.1-10.2 | 严格全文初译完成 |
| 11 | [11-f-extension.md](11-f-extension.md) | Chapter 11 `F` Standard Extension for Single-Precision Floating-Point，11.1-11.9 | 严格全文初译完成 |
| 12 | [12-d-extension.md](12-d-extension.md) | Chapter 12 `D` Standard Extension for Double-Precision Floating-Point，12.1-12.7 | 严格全文初译完成 |
| 13 | [13-q-extension.md](13-q-extension.md) | Chapter 13 `Q` Standard Extension for Quad-Precision Floating-Point，13.1-13.5 | 严格全文初译完成 |
| 14 | [14-rvwmo-memory-consistency.md](14-rvwmo-memory-consistency.md) | Chapter 14 RVWMO Memory Consistency Model，14.1-14.3 | 严格全文初译完成 |
| 15 | [15-l-decimal-floating-point.md](15-l-decimal-floating-point.md) | Chapter 15 `L` Standard Extension for Decimal Floating-Point，15.1 | 严格全文初译完成 |
| 16 | [16-c-compressed.md](16-c-compressed.md) | Chapter 16 `C` Standard Extension for Compressed Instructions，16.1-16.8 | 严格全文初译完成 |
| 17 | [17-b-bit-manipulation.md](17-b-bit-manipulation.md) | Chapter 17 `B` Standard Extension for Bit Manipulation | 严格全文初译完成 |
| 18 | [18-j-dynamically-translated-languages.md](18-j-dynamically-translated-languages.md) | Chapter 18 `J` Standard Extension for Dynamically Translated Languages | 严格全文初译完成 |
| 19 | [19-t-transactional-memory.md](19-t-transactional-memory.md) | Chapter 19 `T` Standard Extension for Transactional Memory | 严格全文初译完成 |
| 20 | [20-p-packed-simd.md](20-p-packed-simd.md) | Chapter 20 `P` Standard Extension for Packed-SIMD Instructions | 严格全文初译完成 |
| 21 | [21-v-vector-operations.md](21-v-vector-operations.md) | Chapter 21 `V` Standard Extension for Vector Operations | 严格全文初译完成 |
| 22 | [22-zam-misaligned-atomics.md](22-zam-misaligned-atomics.md) | Chapter 22 `Zam` Standard Extension for Misaligned Atomics | 严格全文初译完成 |
| 23 | [23-ztso-total-store-ordering.md](23-ztso-total-store-ordering.md) | Chapter 23 `Ztso` Standard Extension for Total Store Ordering | 严格全文初译完成 |
| 24 | [24-rv32-64g-instruction-listings.md](24-rv32-64g-instruction-listings.md) | Chapter 24 RV32/64G Instruction Set Listings，表 24.1-24.3 | 严格全文初译完成 |
| 25 | [25-assembly-programmers-handbook.md](25-assembly-programmers-handbook.md) | Chapter 25 RISC-V Assembly Programmer's Handbook，表 25.1-25.3 | 严格全文初译完成 |
| 26 | [26-extending-riscv.md](26-extending-riscv.md) | Chapter 26 Extending RISC-V，26.1-26.5 | 严格全文初译完成 |
| 27 | [27-isa-extension-naming.md](27-isa-extension-naming.md) | Chapter 27 ISA Extension Naming Conventions，27.1-27.11 | 严格全文初译完成 |
| 28 | [28-history-and-acknowledgments.md](28-history-and-acknowledgments.md) | Chapter 28 History and Acknowledgments，28.1-28.7 | 严格全文初译完成 |
| A | [appendix-a-rvwmo-explanatory-material.md](appendix-a-rvwmo-explanatory-material.md) | Appendix A RVWMO Explanatory Material，A.1-A.7 | 严格全文初译完成 |
| B | [appendix-b-formal-memory-model.md](appendix-b-formal-memory-model.md) | Appendix B Formal Memory Model Specifications，B.1-B.3 | 严格全文初译完成 |
| Bibliography | [bibliography.md](bibliography.md) | Bibliography，参考文献 [1]-[25] | 严格全文初译完成 |

## 额外公开扩展译文

| 文件 | 源范围 | 状态 |
|---|---|---|
| [14-zfh.md](14-zfh.md) | `Zfh` and `Zfhmin` Standard Extensions for Half-Precision Floating-Point，当前公开非特权 ISA 章序 | 额外公开扩展初译完成，不计入 20191213 PDF 主章序 |

## 主章序状态

本地 PDF（Preface、Chapter 1-28、Appendix A、Appendix B、Bibliography）已完成严格全文初译。

## 完成状态

本地非特权 ISA PDF 的主章序、附录和 Bibliography 已全部覆盖。

## 翻译约定

- 不删减源章节内容，不把段落改写成摘要。
- 源文档中的表格转换为 Markdown 表格。
- 源文档中的非规范性 commentary 用引用块标出。
- 如抽取文本存在排版噪声，按 PDF 语义修正中文表达，但不改变技术含义。
