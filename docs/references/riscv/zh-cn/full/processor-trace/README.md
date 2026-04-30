# RISC-V Processor Trace 中文全文翻译

原文：`docs/references/riscv/RISC-V_Processor_Trace_TD010_V1.0.pdf`

版本：Version 1.0，2020-03-20  
作者：Gajinder Panesar, Iain Robertson，UltraSoC Technologies Ltd.

## 翻译进度索引

| 文件 | 原文章节 | 状态 |
| --- | --- | --- |
| [00-title-and-frontmatter.md](00-title-and-frontmatter.md) | 标题页、目录、图表清单 | 已完成 |
| [01-introduction.md](01-introduction.md) | Chapter 1 Introduction | 已完成 |
| [02-branch-trace.md](02-branch-trace.md) | Chapter 2 Branch Trace | 已完成 |
| [03-hart-to-encoder-interface.md](03-hart-to-encoder-interface.md) | Chapter 3 Hart to encoder interface | 已完成 |
| [04-filtering.md](04-filtering.md) | Chapter 4 Filtering | 已完成 |
| [05-trace-encoder-output-packets.md](05-trace-encoder-output-packets.md) | Chapter 5 Trace Encoder Output Packets | 已完成 |
| [06-reference-algorithm.md](06-reference-algorithm.md) | Chapter 6 Reference Algorithm | 已完成 |
| [07-parameters-and-discovery.md](07-parameters-and-discovery.md) | Chapter 7 Parameters and Discovery | 已完成 |
| [08-future-directions.md](08-future-directions.md) | Chapter 8 Future Directions | 已完成 |
| [09-decoder.md](09-decoder.md) | Chapter 9 Decoder | 已完成 |
| [10-example-code-and-packets.md](10-example-code-and-packets.md) | Chapter 10 Example code and packets | 已完成 |

## 术语保留约定

按任务要求，以下技术名词、packet 名、字段名、寄存器/接口名和工具链角色在译文中保留英文原文：`packet`、`trace`、`branch trace`、`encoder`、`sink`、`decoder`、`hart`、`te_inst`、`format`、`subformat`、`branch_map`、`updiscon`、`irreport`、`irdepth`、`trigger`、`iaddress`、`context`、`privilege`、`ucause/scause/mcause`、`utval/stval/mtval`、`ipxact` 等。

## 覆盖范围

本目录覆盖原 PDF 的标题页、目录、List of Figures、List of Tables、Chapter 1 至 Chapter 10 的正文、表格、伪代码和示例 packet。原 PDF 未被修改。
