# 前言

本文档描述 RISC-V 非特权架构。

标记为 Ratified 的 ISA 模块在当前时间点已经批准。标记为 Frozen 的模块，在提交批准之前预计不会发生重大变化。标记为 Draft 的模块预计会在批准之前继续变化。

本文档包含以下版本的 RISC-V ISA 模块：

| Base | Version | Status |
|---|---:|---|
| RVWMO | 2.0 | Ratified |
| RV32I | 2.1 | Ratified |
| RV64I | 2.1 | Ratified |
| RV32E | 1.9 | Draft |
| RV128I | 1.7 | Draft |

| Extension | Version | Status |
|---|---:|---|
| M | 2.0 | Ratified |
| A | 2.1 | Ratified |
| F | 2.2 | Ratified |
| D | 2.2 | Ratified |
| Q | 2.2 | Ratified |
| C | 2.0 | Ratified |
| Counters | 2.0 | Draft |
| L | 0.0 | Draft |
| B | 0.0 | Draft |
| J | 0.0 | Draft |
| T | 0.0 | Draft |
| P | 0.2 | Draft |
| V | 0.7 | Draft |
| Zicsr | 2.0 | Ratified |
| Zifencei | 2.0 | Ratified |
| Zam | 0.1 | Draft |
| Ztso | 0.1 | Frozen |

本文档这一版本的变更包括：

- `A` 扩展现为 2.1 版本，并已于 2019 年 12 月由理事会批准。
- 定义了 big-endian ISA 变体。
- 将用户模式中断的 `N` 扩展移入第二卷。

## 文档版本 20190608-Base-Ratified 的前言

本文档描述 RISC-V 非特权架构。

RVWMO 内存模型在当时已经批准。标记为 Ratified 的 ISA 模块在当时已经批准。标记为 Frozen 的模块，在提交批准之前预计不会发生重大变化。标记为 Draft 的模块预计会在批准之前继续变化。

本文档包含以下版本的 RISC-V ISA 模块：

| Base | Version | Status |
|---|---:|---|
| RVWMO | 2.0 | Ratified |
| RV32I | 2.1 | Ratified |
| RV64I | 2.1 | Ratified |
| RV32E | 1.9 | Draft |
| RV128I | 1.7 | Draft |

| Extension | Version | Status |
|---|---:|---|
| Zifencei | 2.0 | Ratified |
| Zicsr | 2.0 | Ratified |
| M | 2.0 | Ratified |
| A | 2.0 | Frozen |
| F | 2.2 | Ratified |
| D | 2.2 | Ratified |
| Q | 2.2 | Ratified |
| C | 2.0 | Ratified |
| Ztso | 0.1 | Frozen |
| Counters | 2.0 | Draft |
| L | 0.0 | Draft |
| B | 0.0 | Draft |
| J | 0.0 | Draft |
| T | 0.0 | Draft |
| P | 0.2 | Draft |
| V | 0.7 | Draft |
| N | 1.1 | Draft |
| Zam | 0.1 | Draft |

本文档这一版本的变更包括：

- 将理事会在 2019 年初批准的 ISA 模块的描述改为 Ratified。
- 从批准范围中移除了 `A` 扩展。
- 改变了文档版本编号方案，以避免与 ISA 模块版本混淆。
- 将基础整数 ISA 的版本号增加到 2.1，以反映已批准的 RVWMO 内存模型的存在，并反映将 `FENCE.I`、计数器和 CSR 指令从此前基础 ISA 中排除。
- 将 `F` 和 `D` 扩展的版本号增加到 2.2，以反映 2.1 版本改变 canonical NaN，而 2.2 版本定义 NaN-boxing 方案并改变 `FMIN` 和 `FMAX` 指令定义。
- 将文档名称改为使用“unprivileged”指令，以配合把 ISA 规范与平台 profile 强制要求分离的工作。
- 为 execution environment、hart、trap 和 memory access 加入更清晰、更精确的定义。
- 定义了指令集类别：standard、reserved、custom、non-standard 和 non-conforming。
- 删除了暗示 alternate endianness 操作的文字，因为 RISC-V 尚未定义 alternate-endianness 操作。
- 修改了 misaligned load 和 store 行为的描述。规范现在允许 execution environment interface 中出现可见的 misaligned address trap，而不是只要求在用户模式下不可见地处理 misaligned load 和 store。规范现在也允许对不应被模拟的 misaligned access（包括 atomics）报告 access exception。
- 将 `FENCE.I` 从强制基础部分移出，放入单独扩展，并使用 `Zifencei` ISA 名称。`FENCE.I` 已从 Linux 用户 ABI 中移除，并且在具有大型非一致 instruction cache 和 data cache 的实现中存在问题。不过，它仍然是唯一的标准 instruction-fetch coherence 机制。
- 删除了禁止 RV32E 与其他扩展一起使用的限制。
- 删除了 RV32E 和 RV64I 章节中要求某些编码产生 illegal-instruction exception 的平台特定强制要求。
- Counter/timer 指令现在不再视为强制基础 ISA 的一部分。因此 CSR 指令被移入单独章节，并标为 2.0 版本；非特权计数器也移入另一个单独章节。计数器尚未准备批准，因为仍存在一些未解决问题，包括计数器不精确。
- 增加了 CSR-access ordering model。
- 在 2-bit `fmt` 字段中，为浮点指令明确地定义了 16-bit half-precision floating-point 格式。
- 定义了 `FMIN.fmt` 和 `FMAX.fmt` 的 signed-zero 行为，并改变了它们在 signaling-NaN 输入上的行为，以符合拟议 IEEE 754-201x 规范中的 `minimumNumber` 和 `maximumNumber` 操作。
- 定义了内存一致性模型 RVWMO。
- 定义了允许 misaligned AMO 并规定其语义的 `Zam` 扩展。
- 定义了比 RVWMO 更严格的内存一致性模型 `Ztso` 扩展。
- 改进了描述和评论文字。
- 定义了术语 IALIGN，作为描述 instruction-address alignment constraint 的简写。
- 删除了 `P` 扩展章节正文，因为它现在已被活跃任务组文档取代。
- 删除了 `V` 扩展章节正文，因为它现在已被单独的 vector extension 草案文档取代。

## 文档版本 2.2 的前言

这是描述 RISC-V user-level architecture 的文档 2.2 版本。本文档包含以下版本的 RISC-V ISA 模块：

| Base | Version | Draft | Frozen? |
|---|---:|---|---|
| RV32I | 2.0 |  | Y |
| RV32E | 1.9 |  | N |
| RV64I | 2.0 |  | Y |
| RV128I | 1.7 |  | N |

| Extension | Version | Frozen? |
|---|---:|---|
| M | 2.0 | Y |
| A | 2.0 | Y |
| F | 2.0 | Y |
| D | 2.0 | Y |
| Q | 2.0 | Y |
| L | 0.0 | N |
| C | 2.0 | Y |
| B | 0.0 | N |
| J | 0.0 | N |
| T | 0.0 | N |
| P | 0.1 | N |
| V | 0.7 | N |
| N | 1.1 | N |

截至该版本发布时，标准中尚无任何部分由 RISC-V Foundation 正式批准；但上表中标记为 frozen 的组件，在批准过程中除了解决规范中的歧义和缺口之外，预计不会变化。

本文档这一版本的主要变更包括：

- 本文档上一版本由原作者按照 Creative Commons Attribution 4.0 International License 发布；本文档这一版本和未来版本也将按同一许可发布。
- 重新排列章节，把所有扩展先按 canonical order 放置。
- 改进描述和评论文字。
- 修改了 `JALR` 上的隐式 hint 建议，以支持更高效地融合 `LUI/JALR` 和 `AUIPC/JALR` 这样的 macro-op 对。
- 澄清了 load-reserved/store-conditional 序列的约束。
- 增加了新的 control and status register（CSR）映射表。
- 澄清了 `fcsr` 高位的目的和行为。
- 修正了 `FNMADD.fmt` 和 `FNMSUB.fmt` 指令描述；此前描述暗示了零结果的错误符号。
- 将 `FMV.S.X` 和 `FMV.X.S` 指令分别重命名为 `FMV.W.X` 和 `FMV.X.W`，以更符合其未改变的语义。旧名称会继续在工具中支持。
- 使用 NaN-boxing 模型规定了更窄（`<FLEN`）浮点值保存在更宽 `f` 寄存器中时的行为。
- 定义了 `FMA(∞, 0, qNaN)` 的异常行为。
- 增加注记，说明 `P` 扩展可能会被重做为使用整数寄存器进行 fixed-point 操作的 integer packed-SIMD 提案。
- 增加了 `V` vector instruction-set extension 草案提案。
- 增加了 `N` user-level traps extension 早期草案提案。
- 扩展了 pseudoinstruction 列表。
- 删除了 calling convention 章节；该章节已被 RISC-V ELF psABI Specification 取代。
- `C` 扩展已经 frozen，并重新编号为 2.0 版本。

## 文档版本 2.1 的前言

这是描述 RISC-V user-level architecture 的文档 2.1 版本。请注意，frozen 的 user-level ISA base 和扩展 IMAFDQ 2.0 版本相对于本文档上一版本没有变化；但一些规范缺口已被修复，文档也有所改进。软件约定方面做了一些变更。

- 对评论章节做了大量补充和改进。
- 每章使用单独版本号。
- 修改了大于 64 位的长指令编码，以避免在很长的指令格式中移动 `rd` 指示符。
- CSR 指令现在在引入 counter register 的基础整数格式中描述，而不是只在后续浮点章节和配套特权架构手册中引入。
- `SCALL` 和 `SBREAK` 指令分别重命名为 `ECALL` 和 `EBREAK`。它们的编码和功能未改变。
- 澄清了浮点 NaN 处理，并定义了新的 canonical NaN 值。
- 澄清了浮点到整数转换溢出时返回的值。
- 澄清了 LR/SC 的允许成功和必定失败条件，包括序列中使用压缩指令的情况。
- 增加了减少整数寄存器数量的 RV32E base ISA 新提案，支持 MAC 扩展。
- 修订了 calling convention。
- 放宽了 soft-float calling convention 的栈对齐，并描述了 RV32E calling convention。
- 修订了 `C` compressed extension 1.9 版本提案。

## 版本 2.0 的前言

这是 user ISA specification 的第二次发布。我们计划让 base user ISA 加通用扩展（即 IMAFD）的规范在未来开发中保持固定。相对于该 ISA 规范 1.0 版本，已做出以下变更：

- ISA 被划分为一个 integer base 和若干 standard extension。
- 重新排列了指令格式，使立即数编码更高效。
- base ISA 被定义为具有 little-endian memory system，并把 big-endian 或 bi-endian 作为非标准变体。
- 在 atomic instruction extension 中增加了 Load-Reserved/Store-Conditional（LR/SC）指令。
- AMO 和 LR/SC 可以支持 release consistency model。
- `FENCE` 指令提供更细粒度的 memory 和 I/O ordering。
- 增加了 fetch-and-XOR 的 AMO（`AMOXOR`），并改变了 `AMOSWAP` 的编码以腾出空间。
- `AUIPC` 指令把 20 位 upper immediate 加到 PC，替代只读取当前 PC 值的 `RDNPC` 指令。这给 position-independent code 带来显著节省。
- `JAL` 指令现在移到 U-Type 格式，并具有显式 destination register；`J` 指令被删除，由 `rd=x0` 的 `JAL` 替代。这删除了唯一具有隐式 destination register 的指令，也从 base ISA 中删除了 J-Type 指令格式。伴随而来的是 `JAL` 可达范围缩小，但 base ISA 复杂度显著降低。
- 删除了 `JALR` 指令上的静态 hint。对于遵循标准 calling convention 的代码，这些 hint 与 `rd` 和 `rs1` register specifier 冗余。
- `JALR` 指令现在清除计算所得目标地址的最低 bit，以简化硬件，并允许在 function pointer 中保存辅助信息。
- `MFTX.S` 和 `MFTX.D` 指令分别重命名为 `FMV.X.S` 和 `FMV.X.D`。类似地，`MXTF.S` 和 `MXTF.D` 指令分别重命名为 `FMV.S.X` 和 `FMV.D.X`。
- `MFFSR` 和 `MTFSR` 指令分别重命名为 `FRCSR` 和 `FSCSR`。增加了 `FRRM`、`FSRM`、`FRFLAGS` 和 `FSFLAGS` 指令，用于分别访问 `fcsr` 的 rounding mode 和 exception flags 子字段。
- `FMV.X.S` 和 `FMV.X.D` 指令现在从 `rs1` 而不是 `rs2` 取得操作数。该变更简化了 datapath 设计。
- 增加了 `FCLASS.S` 和 `FCLASS.D` floating-point classify 指令。
- 采用了更简单的 NaN 生成与传播方案。
- 对 RV32I，system performance counter 被扩展为 64 位宽，并可分别读取高 32 位和低 32 位。
- 定义了 canonical `NOP` 和 `MV` 编码。
- 定义了 48 位、64 位和大于 64 位指令的标准 instruction-length encoding。
- 增加了 128 位地址空间变体 RV128 的描述。
- 在 32 位基础指令格式中，为用户定义 custom extension 分配了 major opcode。
- 修正了一个排印错误；该错误暗示 store 从 `rd` 取得数据，现在已更正为从 `rs2` 取得数据。
