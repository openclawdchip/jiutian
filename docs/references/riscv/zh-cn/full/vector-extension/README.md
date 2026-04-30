# RISC-V Vector 扩展严格全文翻译进度

源文档：`docs/references/riscv/RISC-V_Vector_ISA-extensions_V1.0.pdf`

本目录用于保存 RISC-V Vector Extension Version 1.0 的中文全文译文。译文按源 PDF 章节顺序组织，逐章逐段翻译正文、说明性 Note、表格、图注、配置指令、load/store、mask、tail 策略、整数/定点/浮点、reduction、permutation、异常、标准扩展、ABI 占位附录和示例附录。指令名、寄存器名、CSR 名、字段名、`SEW`、`LMUL`、`VLEN`、`ELEN`、`VLMAX`、`AVL` 等术语保留英文原文。

上一级 `zh-cn/vector-extension.md` 是正文级浓缩译稿，不标记为严格全文完成。

## 当前文件

| 顺序 | 文件 | 源范围 | 状态 |
|---|---|---|---|
| 00 | [00-frontmatter.md](00-frontmatter.md) | 标题、目录、贡献者、Changes from v1.0-rc2 | 严格全文初译完成 |
| 01 | [01-intro-programmer-model.md](01-intro-programmer-model.md) | Chapter 1-6 | 严格全文初译完成 |
| 02 | [02-load-store-memory.md](02-load-store-memory.md) | Chapter 7-9 | 严格全文初译完成 |
| 03 | [03-arithmetic.md](03-arithmetic.md) | Chapter 10-13 | 严格全文初译完成 |
| 04 | [04-reduction-mask-permutation.md](04-reduction-mask-permutation.md) | Chapter 14-16 | 严格全文初译完成 |
| 05 | [05-exceptions-extensions-listing.md](05-exceptions-extensions-listing.md) | Chapter 17-19 | 严格全文初译完成 |
| 06 | [06-appendix-a-examples.md](06-appendix-a-examples.md) | Appendix A | 严格全文初译完成 |
| 07 | [07-appendix-b-c.md](07-appendix-b-c.md) | Appendix B-C | 严格全文初译完成 |

## 翻译约定

- 不删减源章节含义，不改写为摘要。
- 源文档中的 Note 用引用块标出。
- Markdown 表格用于承载源表格；编码表和指令列表保留原指令/字段拼写。
- 代码示例中的汇编指令、寄存器和标签保持原文，仅翻译注释。
- 若 PDF 抽取文本存在连字或换行噪声，按源语义修正中文表达。
