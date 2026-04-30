# RISC-V 特权架构严格全文翻译进度

源文档：`docs/references/riscv/The_RISC-V_Instruction Set_Manual_Volume_II_Privileged_Architecture_TD005_V20190608.pdf`

本目录用于按源 PDF 的章节顺序存放 RISC-V 特权架构规范的中文全文译文。这里的“全文”指逐章逐段翻译，保留源文档章节、表格、寄存器字段、trap/interrupt、PMP、虚拟内存、页表、特权指令和历史/附录内容；CSR 名、寄存器名、指令名、异常名、字段名和必要英文术语保持原文。

上一级 `zh-cn/privileged-architecture.md` 是正文级浓缩译稿，不作为严格全文完成状态使用。

## 当前文件

| 顺序 | 文件 | 源范围 | 状态 |
|---|---|---|---|
| 00 | [00-front-matter.md](00-front-matter.md) | 题名页、贡献者、许可、Preface、历史版本前言、Contents，PDF 第 1-12 页 | 严格全文初译完成 |
| 01 | [01-introduction.md](01-introduction.md) | Chapter 1 Introduction，1.1-1.3，PDF 第 13-16 页 | 严格全文初译完成 |
| 02 | [02-control-and-status-registers.md](02-control-and-status-registers.md) | Chapter 2 Control and Status Registers (CSRs)，2.1-2.4，PDF 第 17-26 页 | 严格全文初译完成 |
| 03 | [03-machine-level-isa.md](03-machine-level-isa.md) | Chapter 3 Machine-Level ISA，3.1-3.6，PDF 第 27-66 页 | 严格全文初译完成 |
| 04 | [04-supervisor-level-isa.md](04-supervisor-level-isa.md) | Chapter 4 Supervisor-Level ISA，4.1-4.5，PDF 第 67-86 页 | 严格全文初译完成 |
| 05 | [05-privileged-instruction-listings.md](05-privileged-instruction-listings.md) | Chapter 5 RISC-V Privileged Instruction Set Listings，PDF 第 87-88 页 | 严格全文初译完成 |
| 06 | [06-history.md](06-history.md) | Chapter 6 History，6.1，PDF 第 89-91 页 | 严格全文初译完成 |

## 翻译约定

- 不删减源章节内容，不把段落改写成摘要。
- 源文档中的表格、图注和字段列表按 PDF 抽取顺序翻译；抽取造成的换行或排版噪声在后续校订中可继续清理。
- CSR 名、寄存器名、指令名、异常名、字段名、页表格式名和特权模式名保持英文原文。
- 若译文与源 PDF 存在差异，以源 PDF 为准。
