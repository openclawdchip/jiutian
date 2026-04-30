# RISC-V External Debug Support 0.13 中文全文译文

源 PDF：`docs/references/riscv/RISC-V_External Debug_Support_TD003_V0.13.pdf`

本目录是 RISC-V External Debug Support Version 0.13 的中文全文译文。译文按源文档章节拆分，覆盖前言、目录、正文第 1-6 章、附录 A-D、索引和变更记录。为便于实现对照，DM、DTM、DMI、hart、trigger、abstract command、program buffer、SBA、CSR、寄存器名、字段名、命令名、指令助记符和信号名均保留原文。

## 进度索引

| 文件 | 覆盖范围 | 状态 |
|---|---|---|
| `00-frontmatter.md` | 标题页、警告、致谢、目录、图表目录 | 已翻译 |
| `01-introduction.md` | 第 1 章 Introduction，含术语、文档结构、寄存器定义格式、背景、支持特性 | 已翻译 |
| `02-system-overview.md` | 第 2 章 System Overview，含系统组成和图 2.1 说明 | 已翻译 |
| `03-debug-module.md` | 第 3 章 Debug Module (DM)，含 DMI、reset、hart 选择、run control、abstract command、program buffer、SBA、安全、所有 DM DMI 寄存器字段 | 已翻译 |
| `04-riscv-debug.md` | 第 4 章 RISC-V Debug，含 Debug Mode、单步、reset、`dret`、core debug registers 和 virtual debug registers | 已翻译 |
| `05-trigger-module.md` | 第 5 章 Trigger Module，含 trigger 枚举、`tselect`、`tdata*`、`mcontrol`、`icount` 字段 | 已翻译 |
| `06-debug-transport-module.md` | 第 6 章 Debug Transport Module (DTM)，含 JTAG DTM、`IDCODE`、`dtmcs`、`dmi`、`BYPASS`、推荐 JTAG 接口 | 已翻译 |
| `appendix-a-d.md` | 附录 A Hardware Implementations、附录 B Debugger Implementation、附录 C Future Ideas、附录 D Change Log | 已翻译 |
| `index.md` | 源文档 Index 条目中英对照 | 已翻译 |

## 译文约定

- “Debug Module”译为“调试模块”，但缩写 DM 保留。
- “Debug Transport Module”译为“调试传输模块”，但缩写 DTM 保留。
- “Debug Module Interface”译为“调试模块接口”，但缩写 DMI 保留。
- “Program Buffer”译为“program buffer”或“程序缓冲区”，寄存器名前后文保留 `progbuf*`。
- “System Bus Access”译为“系统总线访问”，缩写 SBA 保留。
- “hart”保留原文。
- 寄存器、字段、CSR、指令、命令、异常名和状态编码保留源文档拼写。
