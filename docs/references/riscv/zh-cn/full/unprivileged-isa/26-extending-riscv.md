# Chapter 26 Extending RISC-V

除了支持标准 general-purpose 软件开发之外，RISC-V 的另一个目标是为更专门化的 instruction-set extensions 或更定制化的 accelerators 提供基础。指令编码空间和可选的变长指令编码被设计为：在构建更定制化处理器时，更容易复用标准 ISA toolchain 的软件开发成果。例如，其意图是继续为只使用标准 `I` base，或许还带有许多 non-standard instruction-set extensions 的实现，提供完整软件支持。

本章描述基础 RISC-V ISA 可以被扩展的多种方式，并描述用于管理由独立团体开发的 instruction-set extensions 的方案。本卷只处理 unprivileged ISA，不过第二卷中描述的 supervisor-level extensions 也使用相同方法和术语。

## 26.1 Extension Terminology

本节定义用于描述 RISC-V extensions 的一些标准术语。

### Standard versus Non-Standard Extension

任何 RISC-V 处理器实现都必须支持一个 base integer ISA（RV32I 或 RV64I）。此外，一个实现可以支持一个或多个 extensions。本规范把 extensions 分为两大类：standard 与 non-standard。

- standard extension 是通常有用、并且被设计为不与任何其他 standard extension 冲突的扩展。目前，本手册其他章节中描述的 `MAFDQLCBTPV` 要么已经完整，要么是计划中的 standard extensions。
- non-standard extension 可以高度专门化，并且可能与其他 standard 或 non-standard extensions 冲突。预计随着时间推移会开发出各种各样的 non-standard extensions，其中一些最终可能提升为 standard extensions。

### Instruction Encoding Spaces and Prefixes

instruction encoding space 是若干指令位，base ISA 或 ISA extension 在这些位中编码。RISC-V 支持可变指令长度；但即使在单一指令长度内部，也有不同大小的可用编码空间。例如，base ISA 定义在 30 位编码空间中，即 32 位指令的位 31-2；而 atomic extension `A` 放入 25 位编码空间中，即位 31-7。

本规范使用术语 prefix 指位于 instruction encoding space 右侧的位。由于 RISC-V 中 instruction fetch 是 little-endian，右侧的位存储在较早内存地址，因此在 instruction-fetch 顺序中形成 prefix。标准 base ISA 编码的 prefix 是 32 位字中位 1-0 保存的两位 `11` 字段；标准 atomic extension `A` 的 prefix 是 32 位字中位 6-0 保存的七位 `0101111` 字段，表示 `AMO` major opcode。编码格式的一个特殊之处是，用于编码 minor opcode 的 3 位 `funct3` 字段在 32 位指令格式中并不与 major opcode 位连续，但对于 22 位指令空间，它被视为 prefix 的一部分。

虽然 instruction encoding space 可以是任意大小，但采用一组较小的常用大小，能简化把独立开发的 extensions 打包到单个 global encoding 中的过程。表 26.1 给出 RISC-V 的建议大小。

表 26.1：建议的标准 RISC-V instruction encoding space sizes。

| Size | Usage | 16-bit | 32-bit | 48-bit | 64-bit |
|---|---|---:|---:|---:|---:|
| 14-bit | Quadrant of compressed 16-bit encoding | 3 |  |  |  |
| 22-bit | Minor opcode in base 32-bit encoding |  | 28 | 220 | 235 |
| 25-bit | Major opcode in base 32-bit encoding |  | 32 | 217 | 232 |
| 30-bit | Quadrant of base 32-bit encoding |  | 1 | 212 | 227 |
| 32-bit | Minor opcode in 48-bit encoding |  |  | 210 | 225 |
| 37-bit | Major opcode in 48-bit encoding |  |  | 32 | 220 |
| 40-bit | Quadrant of 48-bit encoding |  |  | 4 | 217 |
| 45-bit | Sub-minor opcode in 64-bit encoding |  |  |  | 212 |
| 48-bit | Minor opcode in 64-bit encoding |  |  |  | 29 |
| 52-bit | Major opcode in 64-bit encoding |  |  |  | 32 |

### Greenfield versus Brownfield Extensions

本规范使用术语 greenfield extension 描述一种开始填充新 instruction encoding space 的扩展，因此它只能在 prefix 层面造成编码冲突。本规范使用术语 brownfield extension 描述一种适配到先前已定义指令空间中现有编码周围的扩展。brownfield extension 必然绑定到特定 greenfield parent encoding；同一个 greenfield parent encoding 可以有多个 brownfield extensions。例如，base ISAs 是 30 位指令空间的 greenfield encodings，而 `F`、`D`、`Q` 浮点扩展都是 brownfield extensions，它们添加到父级 base ISA 30 位编码空间中。

注意，本规范认为标准 `A` 扩展具有 greenfield encoding，因为它在完整 32 位基础指令编码的最左侧位中定义了新的、先前为空的 25 位编码空间，即使它的标准 prefix 把它放在 base ISA 的 30 位编码空间内。只改变它的单个 7 位 prefix，就可以把 `A` 扩展移动到不同 30 位编码空间中，并且只需担心 prefix 层面的冲突，而不是编码空间内部的冲突。

表 26.2：standard instruction-set extensions 的二维分类。

|  | Adds state | No new state |
|---|---|---|
| Greenfield | `RV32I(30)`, `RV64I(30)` | `A(25)` |
| Brownfield | `F(I)`, `D(F)`, `Q(D)` | `M(I)` |

表 26.2 把 bases 和 standard extensions 放入一个简单的二维分类。一个轴表示扩展是 greenfield 还是 brownfield，另一个轴表示扩展是否增加 architectural state。对 greenfield extensions，括号中给出 instruction encoding space 的大小。对 brownfield extensions，括号中给出它构建其上的扩展（greenfield 或 brownfield）的名称。额外 user-level architectural state 通常意味着 supervisor-level system 或标准 calling convention 可能需要改变。

注意，RV64I 不被视为 RV32I 的扩展，而是一个不同的完整 base encoding。

### Standard-Compatible Global Encodings

实际 RISC-V 实现的完整编码或 global encoding，必须为每个被包含的 instruction encoding space 分配唯一且不冲突的 prefix。bases 和每个 standard extension 都已经各自分配了标准 prefix，以保证它们可以全部共存于一个 global encoding 中。

standard-compatible global encoding 是这样一种编码：base 和每个被包含的 standard extension 都使用它们的标准 prefixes。standard-compatible global encoding 可以包含不与已包含 standard extensions 冲突的 non-standard extensions。如果相关 standard extensions 没有包含在 global encoding 中，standard-compatible global encoding 也可以把 standard prefixes 用于 non-standard extensions。换句话说，如果 standard extension 被包含在 standard-compatible global encoding 中，它必须使用自己的标准 prefix；否则，它的 prefix 可以重新分配。这些约束让公共 toolchain 能够面向任何 RISC-V standard-compatible global encoding 的标准子集。

### Guaranteed Non-Standard Encoding Space

为了支持 proprietary custom extensions 的开发，编码空间的若干部分保证永远不会被 standard extensions 使用。

## 26.2 RISC-V Extension Design Philosophy

RISC-V 计划支持大量独立开发的 extensions：一方面鼓励 extension developers 在 instruction encoding spaces 内工作，另一方面提供工具，通过分配唯一 prefixes，把这些 extensions 打包进 standard-compatible global encoding。一些 extensions 更自然地实现为现有 extensions 的 brownfield augmentations，并将共享分配给其 parent greenfield extension 的 prefix。standard extension prefixes 避免核心功能编码上的虚假不兼容，同时允许对更专门的 extensions 进行自定义打包。

把 RISC-V extensions 重新打包进不同 standard-compatible global encodings 的能力，可以用在多种方式中。

一种用例是开发高度专门化的 custom accelerators，用于运行重要应用领域的 kernels。这类实现可能希望除 base integer ISA 之外去掉所有内容，只加入当前任务所需的 extensions。base ISA 被设计为对硬件实现提出最小要求，并且编码时只使用 32 位 instruction encoding space 的一小部分。

另一种用例是为新型 instruction-set extension 构建研究原型。研究人员可能不想花精力实现 variable-length instruction-fetch unit，因此希望使用简单的 32 位 fixed-width instruction encoding 来原型化扩展。不过，这个新扩展可能太大，无法在 32 位空间中与 standard extensions 共存。如果研究实验不需要所有 standard extensions，standard-compatible global encoding 可以丢弃未使用的 standard extensions，并复用它们的 prefixes，把拟议扩展放到 non-standard location，从而简化研究原型的工程实现。标准工具仍能面向存在的 base 和任何 standard extensions，以减少开发时间。一旦该 instruction-set extension 已经被评估和改进，就可以让它被打包到更大的 variable-length encoding space 中，以避免与所有 standard extensions 冲突。

以下各节描述开发带有新 instruction-set extensions 的实现时越来越复杂的策略。这些策略主要面向高度定制、教育性或实验性架构，而不是 RISC-V ISA 开发主线。

## 26.3 Extensions within fixed-width 32-bit instruction format

本节讨论向只支持基础 fixed-width 32-bit instruction format 的实现添加 extensions。

预计最简单的 fixed-width 32-bit encoding 将在许多受限 accelerators 和研究原型中流行。

### Available 30-bit instruction encoding spaces

在标准编码中，三个可用的 30 位 instruction encoding spaces，即具有 2 位 prefixes `00`、`01` 和 `10` 的空间，被用于启用可选 compressed instruction extension。不过，如果不需要 compressed instruction-set extension，则这三个额外的 30 位编码空间变为可用。这会使 32 位格式内可用编码空间扩大四倍。

### Available 25-bit instruction encoding spaces

25 位 instruction encoding space 对应 base 和 standard extension encodings 中的 major opcode。

有四个 major opcodes 明确保留给 custom extensions（表 24.1），其中每一个都代表一个 25 位编码空间。其中两个保留给 RV128 base encoding 的最终使用（将成为 `OP-IMM-64` 和 `OP-64`），但可在 RV32 和 RV64 中用于 standard 或 non-standard extensions。

为 RV64 保留的两个 opcodes（`OP-IMM-32` 和 `OP-32`）也可以只用于 RV32 的 standard 和 non-standard extensions。

如果一个实现不需要 floating-point，那么为标准浮点扩展保留的七个 major opcodes（`LOAD-FP`、`STORE-FP`、`MADD`、`MSUB`、`NMSUB`、`NMADD`、`OP-FP`）可以重新用于 non-standard extensions。类似地，如果不需要标准原子扩展，`AMO` major opcode 也可以重新使用。

如果一个实现不需要长于 32 位的指令，则还会有四个额外 major opcodes 可用，即表 24.1 中标灰的那些。

base RV32I encoding 只使用 11 个 major opcodes 加 3 个 reserved opcodes，最多留下 18 个 opcodes 可用于 extensions。base RV64I encoding 只使用 13 个 major opcodes 加 3 个 reserved opcodes，最多留下 16 个 opcodes 可用于 extensions。

### Available 22-bit instruction encoding spaces

22 位 encoding space 对应 base 和 standard extension encodings 中的 `funct3` minor opcode space。若干 major opcodes 的 `funct3` 字段 minor opcode 没有被完全占用，因此留下若干可用的 22 位 encoding spaces。

通常 major opcode 会选择用于在指令剩余位中编码 operands 的格式；理想情况下，extension 应该遵循该 major opcode 的 operand format，以简化硬件 decoding。

### Other spaces

在某些 major opcodes 之下还有更小的空间可用，而且并非所有 minor opcodes 都被完全填满。

## 26.4 Adding aligned 64-bit instruction extensions

为太大而无法放入基础 32 位 fixed-width instruction format 的 extensions 提供空间，最简单的方法是增加自然对齐的 64 位指令。实现仍然必须支持 32 位基础指令格式，但可以要求 64 位指令按 64 位边界对齐，以简化 instruction fetch；必要时使用一条 32 位 `NOP` 指令作为 alignment padding。

为了简化标准工具的使用，64 位指令应按图 1.1 所述方式编码。不过，实现也可以为 64 位指令选择非标准 instruction-length encoding，同时保留 32 位指令的标准编码。例如，如果不需要 compressed instructions，则 64 位指令可以在一条指令的前两位中使用一个或多个零位进行编码。

预计 processor generators 会生成 instruction-fetch units，能够自动处理任意组合的受支持 variable-length instruction encodings。

## 26.5 Supporting VLIW encodings

虽然 RISC-V 并非设计为纯 VLIW machine 的基础，但可以使用几种替代方法把 VLIW encodings 作为 extensions 加入。在所有情况下，都必须支持基础 32 位编码，以允许使用任何标准软件工具。

### Fixed-size instruction group

最简单的方法是定义单个大型自然对齐指令格式，例如 128 位，并在其中编码 VLIW operations。在传统 VLIW 中，这种方法往往会浪费 instruction memory 来保存 NOPs；但 RISC-V 兼容实现也必须支持基础 32 位指令，因此 VLIW code size expansion 会被限制在 VLIW-accelerated functions 中。

### Encoded-Length Groups

另一种方法是使用图 1.1 中的标准长度编码来编码 parallel instruction groups，从而允许把 NOPs 从 VLIW 指令中压缩掉。例如，一条 64 位指令可以保存两个 28 位 operations，一条 96 位指令可以保存三个 28 位 operations，依此类推。或者，一条 48 位指令可以保存一个 42 位 operation，一条 96 位指令可以保存两个 42 位 operations，依此类推。

这种方法的优点是为只保存单个 operation 的指令保留 base ISA encoding；缺点是需要为 VLIW 指令内部的 operations 提供新的 28 位或 42 位编码，并且较大的 groups 需要 misaligned instruction fetch。一个简化方式是不允许 VLIW 指令跨越某些对微架构重要的边界，例如 cache lines 或 virtual memory pages。

### Fixed-Size Instruction Bundles

另一种类似 Itanium 的方法，是使用更大的自然对齐 fixed instruction bundle size，例如 128 位，并跨这个 bundle 编码 parallel operation groups。这简化了 instruction fetch，但把复杂度转移到 group execution engine。为了保持 RISC-V 兼容，仍然必须支持基础 32 位指令。

### End-of-Group bits in Prefix

上述方法都没有在 VLIW 指令内部的 individual operations 上保留 RISC-V encoding。还有一种方法是重新利用 fixed-width 32-bit encoding 中的两个 prefix bits。一个 prefix bit 可以在被置位时表示 “end-of-group”，第二个位若清零则可以表示在 predicate 下执行。不知道 VLIW extension 的工具生成的标准 RISC-V 32 位指令会把两个 prefix bits 都置位（`11`），因此具有正确语义：每条指令都位于一个 group 末尾，并且不受 predication。

这种方法的主要缺点是，base ISA 缺少激进 VLIW 系统通常所需的复杂 predication support，而且难以在标准 30 位编码空间中添加空间来指定更多 predicate registers。
