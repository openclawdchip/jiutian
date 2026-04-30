# RISC-V Bit-Manipulation ISA 扩展全文译文

原文：`docs/references/riscv/RISC-V_Bit-Manipulation_ISA-extensions_TD013_V1.0.0-38-g865e7a7.pdf`

版本：Version 1.0.0-38-g865e7a7，2021-06-28，Release candidate。

本目录为该 PDF 的中文全文翻译。译文按原文结构拆分，保留 `Zba`、`Zbb`、`Zbc`、`Zbs`、指令名、字段名、寄存器名、编码标记和伪代码符号原文。

## 进度索引

| 文件 | 覆盖范围 | 状态 |
|---|---|---|
| `00-front-matter.md` | 标题页、目录、Colophon、Acknowledgments、公开审阅与批准分组说明、Word Instructions、指令语义伪代码说明 | 完成 |
| `01-extensions.md` | Chapter 1: Extensions，含 `Zba`、`Zbb`、`Zbc`、`Zbs` 扩展说明、指令清单、软件用途与实现提示 | 完成 |
| `02-instructions.md` | Chapter 2: Instructions (in alphabetical order)，`add.uw` 至 `zext.h` 共 43 条指令，含语义、编码说明、伪代码、提示和所属扩展 | 完成 |
| `appendix-a-software-optimization-guide.md` | Appendix A: Software optimization guide，`strlen` 与 `strcmp` 示例及代码注释 | 完成 |

## 覆盖章节

- Colophon
- Acknowledgments
- Bit-manipulation a, b, c and s extensions grouped for public review and ratification
- Word Instructions
- Pseudocode for instruction semantics
- Chapter 1. Extensions
- 1.1. Zba extension
- 1.2. Zbb: Basic bit-manipulation
- 1.2.1. Logical with negate
- 1.2.2. Count leading/trailing zero bits
- 1.2.3. Count population
- 1.2.4. Integer minimum/maximum
- 1.2.5. Sign- and zero-extension
- 1.2.6. Bitwise rotation
- 1.2.7. OR Combine
- 1.2.8. Byte-reverse
- 1.3. Zbc: Carry-less multiplication
- 1.4. Zbs: Single-bit instructions
- Chapter 2. Instructions (in alphabetical order), 2.1 至 2.43
- Appendix A. Software optimization guide
- A.1. strlen
- A.2. strcmp

