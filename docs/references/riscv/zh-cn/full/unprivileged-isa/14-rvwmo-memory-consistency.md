# Chapter 14 RVWMO Memory Consistency Model, Version 0.1

本章定义 RISC-V 内存一致性模型。内存一致性模型是一组规则，用来规定从内存执行 load 时可以返回哪些值。RISC-V 使用名为 `RVWMO` 的内存模型，即 RISC-V Weak Memory Ordering。该模型的设计目标是在支持易处理的编程模型的同时，为架构设计者构建高性能、可扩展设计提供灵活性。

在 `RVWMO` 下，从同一 hart 中其他内存指令的视角看，运行在单个 hart 上的代码似乎按顺序执行；但另一个 hart 上的内存指令可能观察到第一个 hart 的内存指令以不同顺序执行。因此，多线程代码可能需要显式同步，以保证来自不同 hart 的内存指令之间的顺序。基础 RISC-V ISA 为此提供 `FENCE` 指令，见 2.7 节；原子扩展 `A` 还定义了 load-reserved/store-conditional 指令和原子读-改-写指令。

用于 misaligned atomics 的标准 ISA 扩展 `Zam`（Chapter 22）和用于 total store ordering 的标准 ISA 扩展 `Ztso`（Chapter 23）会用这些扩展专用的附加规则增强 `RVWMO`。

本规范的附录提供内存一致性模型的公理化和操作化形式化定义，并提供额外解释材料。

本章定义 regular main memory 操作的内存模型。该内存模型与 I/O memory、instruction fetch、`FENCE.I`、page table walk 和 `SFENCE.VMA` 的交互尚未形式化。上述部分或全部内容可能会在本规范未来修订版中形式化。RV128 基础 ISA，以及未来的 ISA 扩展，例如 `V` vector、`T` transactional memory 和 `J` JIT 扩展，也需要纳入未来修订版。

支持不同宽度重叠内存访问同时存在的内存一致性模型，仍然是活跃的学术研究领域，并且尚未被完全理解。不同大小的内存访问在 `RVWMO` 下如何交互，本规范已尽当前能力做出规定；但如果发现新问题，这些细节仍可能修订。

## 14.1 Definition of the RVWMO Memory Model

`RVWMO` 内存模型用 global memory order 定义。global memory order 是所有 hart 产生的内存操作上的一个全序。一般而言，一个多线程程序有许多种可能执行，每一种执行都有其对应的 global memory order。

global memory order 定义在内存指令生成的原始 load 和 store 操作之上。随后它受本章其余部分定义的约束限制。任何满足所有内存模型约束的执行，就内存模型而言，都是合法执行。

### Memory Model Primitives

内存操作上的 program order 反映生成每个 load 和 store 的指令在该 hart 动态指令流中逻辑排列的顺序；也就是一个简单顺序处理器执行该 hart 指令时的顺序。

访问内存的指令会产生内存操作。一个内存操作可以是 load 操作、store 操作，或者同时是两者。所有内存操作都是 single-copy atomic：它们绝不会以部分完成状态被观察到。

在 RV32GC 和 RV64GC 的指令中，每条对齐内存指令恰好产生一个内存操作，但有两个例外。第一，未成功的 `SC` 指令不会产生任何内存操作。第二，如 12.3 节所述并在下文进一步澄清，当 `XLEN < 64` 时，`FLD` 和 `FSD` 指令各自可能产生多个内存操作。一条对齐 `AMO` 会产生一个内存操作，该操作同时是 load 操作和 store 操作。

RV128 基础指令集中的指令，以及未来 ISA 扩展中的指令，例如 `V`（vector）和 `P`（SIMD），可能产生多个内存操作。不过，这些扩展的内存模型尚未形式化。

一条 misaligned load 或 store 指令可以分解为一组任意粒度的组成内存操作。当 `XLEN < 64` 时，一条 `FLD` 或 `FSD` 指令也可以分解为一组任意粒度的组成内存操作。由这些指令生成的内存操作彼此之间不按 program order 排序，但它们相对于 program order 中前后指令生成的内存操作，仍按通常方式排序。原子扩展 `A` 完全不要求执行环境支持 misaligned atomic 指令；不过，如果通过 `Zam` 扩展支持 misaligned atomics，则 `LR`、`SC` 和 `AMO` 可以在满足 Chapter 22 中为 misaligned atomics 定义的 atomicity axiom 约束下被分解。

把 misaligned 内存操作向下分解到字节粒度，有助于在不原生支持 misaligned accesses 的实现上进行仿真。例如，这类实现可以简单地逐字节迭代完成一次 misaligned access。

如果一条 `LR` 指令在 program order 中先于一条 `SC` 指令，并且二者之间没有其他 `LR` 或 `SC` 指令，则称该 `LR` 和 `SC` 指令成对；对应的内存操作也称为成对操作。但若 `SC` 失败，则不会生成 store 操作。决定一条 `SC` 必须成功、可以成功或必须失败的完整条件列表见 8.2 节。

load 和 store 操作还可以携带以下集合中的一个或多个 ordering annotation：`acquire-RCpc`、`acquire-RCsc`、`release-RCpc` 和 `release-RCsc`。设置了 `aq` 的 `AMO` 或 `LR` 指令带有 `acquire-RCsc` annotation。设置了 `rl` 的 `AMO` 或 `SC` 指令带有 `release-RCsc` annotation。同时设置 `aq` 和 `rl` 的 `AMO`、`LR` 或 `SC` 指令同时带有 `acquire-RCsc` 和 `release-RCsc` annotations。

为方便起见，术语 acquire annotation 指 `acquire-RCpc` annotation 或 `acquire-RCsc` annotation。同样，release annotation 指 `release-RCpc` annotation 或 `release-RCsc` annotation。RCpc annotation 指 `acquire-RCpc` annotation 或 `release-RCpc` annotation。RCsc annotation 指 `acquire-RCsc` annotation 或 `release-RCsc` annotation。

在内存模型文献中，术语 `RCpc` 表示 release consistency with processor-consistent synchronization operations；术语 `RCsc` 表示 release consistency with sequentially-consistent synchronization operations。

> Commentary
>
> 文献中对 acquire 和 release annotation 有许多不同定义；但在 `RVWMO` 语境下，这些术语由 preserved program order 规则 5-7 简洁且完整地定义。

> Commentary
>
> `RCpc` annotations 当前只在标准扩展 `Ztso`（Chapter 23）按每个内存访问隐式分配时使用。此外，虽然 ISA 当前不包含原生 load-acquire 或 store-release 指令，也不包含它们的 `RCpc` 变体，但 `RVWMO` 模型本身被设计为向前兼容，以便未来扩展可以把上述任何或全部内容加入 ISA。

### Syntactic Dependencies

`RVWMO` 内存模型的定义部分依赖 syntactic dependency 的概念，其定义如下。

在定义依赖关系的语境中，register 指整个通用寄存器、某个 CSR 的一部分，或整个 CSR。通过 CSR 跟踪依赖关系的粒度由各 CSR 自身决定，并在 14.2 节中定义。

syntactic dependencies 根据指令的 source registers、指令的 destination registers，以及指令把依赖关系从 source registers 传递到 destination registers 的方式来定义。本节给出这些术语的一般定义；不过，14.3 节为每条指令提供完整的具体列表。

一般而言，如果满足以下任一条件，则除 `x0` 以外的寄存器 `r` 是指令 `i` 的 source register：

- 在 `i` 的 opcode 中，`rs1`、`rs2` 或 `rs3` 被设置为 `r`。
- `i` 是 CSR 指令，并且在 `i` 的 opcode 中，`csr` 被设置为 `r`；但如果 `i` 是 `CSRRW` 或 `CSRRWI` 且 `rd` 被设置为 `x0`，则不包括这种情形。
- `r` 是 CSR，并且是 14.3 节定义的 `i` 的 implicit source register。
- `r` 是 CSR，并且与 `i` 的另一个 source register alias。

内存指令还会进一步指定哪些 source registers 是 address source registers，哪些是 data source registers。

一般而言，如果满足以下任一条件，则除 `x0` 以外的寄存器 `r` 是指令 `i` 的 destination register：

- 在 `i` 的 opcode 中，`rd` 被设置为 `r`。
- `i` 是 CSR 指令，并且在 `i` 的 opcode 中，`csr` 被设置为 `r`；但如果 `i` 是 `CSRRS` 或 `CSRRC` 且 `rs1` 被设置为 `x0`，或者 `i` 是 `CSRRSI` 或 `CSRRCI` 且 `uimm[4:0]` 被设置为 0，则不包括这种情形。
- `r` 是 CSR，并且是 14.3 节定义的 `i` 的 implicit destination register。
- `r` 是 CSR，并且与 `i` 的另一个 destination register alias。

大多数非内存指令会把依赖关系从它们的每个 source register 传递到它们的每个 destination register。不过，这条规则存在例外；见 14.3 节。

如果满足以下任一条件，则称指令 `j` 经由指令 `i` 的 destination register `s` 和指令 `j` 的 source register `r` 对指令 `i` 具有 syntactic dependency：

- `s` 与 `r` 相同，并且在 program order 中位于 `i` 和 `j` 之间的任何指令都没有把 `r` 作为 destination register。
- 在 program order 中位于 `i` 和 `j` 之间存在一条指令 `m`，并且以下条件全部成立：
  1. `j` 经由 destination register `q` 和 source register `r` 对 `m` 具有 syntactic dependency。
  2. `m` 经由 destination register `s` 和 source register `p` 对 `i` 具有 syntactic dependency。
  3. `m` 把依赖关系从 `p` 传递到 `q`。

最后，在下面的定义中，令 `a` 和 `b` 为两个内存操作，令 `i` 和 `j` 分别为生成 `a` 和 `b` 的指令。

如果 `r` 是 `j` 的 address source register，并且 `j` 经由 source register `r` 对 `i` 具有 syntactic dependency，则 `b` 对 `a` 具有 syntactic address dependency。

如果 `b` 是 store 操作，`r` 是 `j` 的 data source register，并且 `j` 经由 source register `r` 对 `i` 具有 syntactic dependency，则 `b` 对 `a` 具有 syntactic data dependency。

如果在 program order 中位于 `i` 和 `j` 之间存在一条指令 `m`，使得 `m` 是 branch 或 indirect jump，并且 `m` 对 `i` 具有 syntactic dependency，则 `b` 对 `a` 具有 syntactic control dependency。

> Commentary
>
> 一般而言，非 `AMO` load 指令没有 data source registers，无条件非 `AMO` store 指令没有 destination registers。不过，成功的 `SC` 指令被认为把 `rd` 指定的寄存器作为 destination register，因此后续指令可能对 program order 中先于它的成功 `SC` 指令具有 syntactic dependency。

### Preserved Program Order

程序某次执行的 global memory order 会遵守每个 hart 的部分 program order，但并不遵守全部 program order。global memory order 必须遵守的 program order 子集称为 preserved program order。

preserved program order 的完整定义如下。注意，`AMO` 同时既是 load 也是 store：如果内存操作 `a` 在 program order 中先于内存操作 `b`，`a` 和 `b` 都访问 regular main memory（而不是 I/O regions），并且满足以下任一条件，则 `a` 在 preserved program order 中先于 `b`，因而也在 global memory order 中先于 `b`。

Overlapping-Address Orderings：

1. `b` 是 store，并且 `a` 与 `b` 访问重叠的内存地址。
2. `a` 和 `b` 都是 load，`x` 是 `a` 和 `b` 都读取的一个字节，在 program order 中 `a` 和 `b` 之间没有对 `x` 的 store，并且 `a` 和 `b` 对 `x` 返回由不同内存操作写入的值。
3. `a` 由 `AMO` 或 `SC` 指令生成，`b` 是 load，并且 `b` 返回由 `a` 写入的值。

Explicit Synchronization：

4. 存在一条 `FENCE` 指令把 `a` 排在 `b` 之前。
5. `a` 带有 acquire annotation。
6. `b` 带有 release annotation。
7. `a` 和 `b` 都带有 `RCsc` annotations。
8. `a` 与 `b` 成对。

Syntactic Dependencies：

9. `b` 对 `a` 具有 syntactic address dependency。
10. `b` 对 `a` 具有 syntactic data dependency。
11. `b` 是 store，并且 `b` 对 `a` 具有 syntactic control dependency。

Pipeline Dependencies：

12. `b` 是 load，并且在 program order 中 `a` 和 `b` 之间存在某个 store `m`，使得 `m` 对 `a` 具有 address 或 data dependency，并且 `b` 返回由 `m` 写入的值。
13. `b` 是 store，并且在 program order 中 `a` 和 `b` 之间存在某条指令 `m`，使得 `m` 对 `a` 具有 address dependency。

### Memory Model Axioms

只有当存在一个符合 preserved program order 并满足 load value axiom、atomicity axiom 和 progress axiom 的 global memory order 时，RISC-V 程序的一次执行才服从 `RVWMO` 内存一致性模型。

Load Value Axiom：每个 load `i` 的每个字节，都返回由以下 store 中在 global memory order 中最新的那个 store 写入该字节的值：

1. 写入该字节并且在 global memory order 中先于 `i` 的 store。
2. 写入该字节并且在 program order 中先于 `i` 的 store。

Atomicity Axiom：如果 `r` 和 `w` 是某 hart `h` 中由对齐 `LR` 和 `SC` 指令生成的一对 load 和 store 操作，`s` 是对字节 `x` 的 store，并且 `r` 返回由 `s` 写入的值，那么 `s` 必须在 global memory order 中先于 `w`，并且在 global memory order 中，不能存在来自 hart `h` 以外的、对字节 `x` 的 store 位于 `s` 之后且 `w` 之前。

> Commentary
>
> Atomicity Axiom 理论上支持不同宽度和不匹配地址的 `LR`/`SC` 对，因为允许实现让这类情况下的 `SC` 操作成功。不过在实践中，预计这类模式很少见，并且不鼓励使用。

Progress Axiom：在 global memory order 中，任何内存操作之前都不能有无限序列的其他内存操作。

## 14.2 CSR Dependency Tracking Granularity

表 14.1：通过 CSR 跟踪 syntactic dependencies 的粒度。

| Name | Portions Tracked as Independent Units | Aliases |
|---|---|---|
| `fflags` | 位 4、3、2、1、0 | `fcsr` |
| `frm` | 整个 CSR | `fcsr` |
| `fcsr` | 位 7-5、4、3、2、1、0 | `fflags`、`frm` |

注：只读 CSR 没有列出，因为它们不参与 syntactic dependencies 的定义。

## 14.3 Source and Destination Register Listings

本节给出每条指令的 source registers 和 destination registers 的具体列表。这些列表用于 14.1 节中 syntactic dependencies 的定义。

术语 accumulating CSR 用来描述一个 CSR：它同时是 source register 和 destination register，但只把依赖关系从自己传递到自己。

除另有标注外，指令会把依赖关系从 Source Registers 列中的每个 source register 传递到 Destination Registers 列中的每个 destination register，从 Source Registers 列中的每个 source register 传递到 Accumulating CSRs 列中的每个 CSR，并且从 Accumulating CSRs 列中的每个 CSR 传递到其自身。

Key：

| 标记 | 含义 |
|---|---|
| `A` | Address source register |
| `D` | Data source register |
| `†` | 该指令不把依赖关系从任何 source register 传递到任何 destination register |
| `‡` | 该指令按说明把依赖关系从 source register 传递到 destination register |

### RV32I Base Integer Instruction Set

| 指令 | Source Registers | Destination Registers | Accumulating CSRs |
|---|---|---|---|
| `LUI` |  | `rd` |  |
| `AUIPC` |  | `rd` |  |
| `JAL` |  | `rd` |  |
| `JALR†` | `rs1` | `rd` |  |
| `BEQ` | `rs1`, `rs2` |  |  |
| `BNE` | `rs1`, `rs2` |  |  |
| `BLT` | `rs1`, `rs2` |  |  |
| `BGE` | `rs1`, `rs2` |  |  |
| `BLTU` | `rs1`, `rs2` |  |  |
| `BGEU` | `rs1`, `rs2` |  |  |
| `LB†` | `rs1A` | `rd` |  |
| `LH†` | `rs1A` | `rd` |  |
| `LW†` | `rs1A` | `rd` |  |
| `LBU†` | `rs1A` | `rd` |  |
| `LHU†` | `rs1A` | `rd` |  |
| `SB` | `rs1A`, `rs2D` |  |  |
| `SH` | `rs1A`, `rs2D` |  |  |
| `SW` | `rs1A`, `rs2D` |  |  |
| `ADDI` | `rs1` | `rd` |  |
| `SLTI` | `rs1` | `rd` |  |
| `SLTIU` | `rs1` | `rd` |  |
| `XORI` | `rs1` | `rd` |  |
| `ORI` | `rs1` | `rd` |  |
| `ANDI` | `rs1` | `rd` |  |
| `SLLI` | `rs1` | `rd` |  |
| `SRLI` | `rs1` | `rd` |  |
| `SRAI` | `rs1` | `rd` |  |
| `ADD` | `rs1`, `rs2` | `rd` |  |
| `SUB` | `rs1`, `rs2` | `rd` |  |
| `SLL` | `rs1`, `rs2` | `rd` |  |
| `SLT` | `rs1`, `rs2` | `rd` |  |
| `SLTU` | `rs1`, `rs2` | `rd` |  |
| `XOR` | `rs1`, `rs2` | `rd` |  |
| `SRL` | `rs1`, `rs2` | `rd` |  |
| `SRA` | `rs1`, `rs2` | `rd` |  |
| `OR` | `rs1`, `rs2` | `rd` |  |
| `AND` | `rs1`, `rs2` | `rd` |  |
| `FENCE` |  |  |  |
| `FENCE.I` |  |  |  |
| `ECALL` |  |  |  |
| `EBREAK` |  |  |  |

### RV32I Base Integer Instruction Set, Continued: CSR Register Instructions

| 指令 | Source Registers | Destination Registers | Accumulating CSRs | 注释 |
|---|---|---|---|---|
| `CSRRW‡` | `rs1`, `csr*` | `rd`, `csr` |  | `*` 除非 `rd=x0`；`‡` 表示从 `rs1` 到 `csr`、从 `csr` 到 `rd` 传递依赖关系 |
| `CSRRS‡` | `rs1`, `csr` | `rd*`, `csr` |  | `*` 除非 `rs1=x0`；`‡` 表示从 `rs1` 到 `csr`、从 `csr` 到 `rd` 传递依赖关系 |
| `CSRRC‡` | `rs1`, `csr` | `rd*`, `csr` |  | `*` 除非 `rs1=x0`；`‡` 表示从 `rs1` 到 `csr`、从 `csr` 到 `rd` 传递依赖关系 |

### RV32I Base Integer Instruction Set, Continued: CSR Immediate Instructions

| 指令 | Source Registers | Destination Registers | Accumulating CSRs | 注释 |
|---|---|---|---|---|
| `CSRRWI‡` | `csr*` | `rd`, `csr` |  | `*` 除非 `rd=x0`；`‡` 表示从 `csr` 到 `rd` 传递依赖关系 |
| `CSRRSI‡` | `csr` | `rd`, `csr*` |  | `*` 除非 `uimm[4:0]=0`；`‡` 表示从 `csr` 到 `rd` 传递依赖关系 |
| `CSRRCI‡` | `csr` | `rd`, `csr*` |  | `*` 除非 `uimm[4:0]=0`；`‡` 表示从 `csr` 到 `rd` 传递依赖关系 |

### RV64I Base Integer Instruction Set

| 指令 | Source Registers | Destination Registers | Accumulating CSRs |
|---|---|---|---|
| `LWU†` | `rs1A` | `rd` |  |
| `LD†` | `rs1A` | `rd` |  |
| `SD` | `rs1A`, `rs2D` |  |  |
| `SLLI` | `rs1` | `rd` |  |
| `SRLI` | `rs1` | `rd` |  |
| `SRAI` | `rs1` | `rd` |  |
| `ADDIW` | `rs1` | `rd` |  |
| `SLLIW` | `rs1` | `rd` |  |
| `SRLIW` | `rs1` | `rd` |  |
| `SRAIW` | `rs1` | `rd` |  |
| `ADDW` | `rs1`, `rs2` | `rd` |  |
| `SUBW` | `rs1`, `rs2` | `rd` |  |
| `SLLW` | `rs1`, `rs2` | `rd` |  |
| `SRLW` | `rs1`, `rs2` | `rd` |  |
| `SRAW` | `rs1`, `rs2` | `rd` |  |

### RV32M Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs |
|---|---|---|---|
| `MUL` | `rs1`, `rs2` | `rd` |  |
| `MULH` | `rs1`, `rs2` | `rd` |  |
| `MULHSU` | `rs1`, `rs2` | `rd` |  |
| `MULHU` | `rs1`, `rs2` | `rd` |  |
| `DIV` | `rs1`, `rs2` | `rd` |  |
| `DIVU` | `rs1`, `rs2` | `rd` |  |
| `REM` | `rs1`, `rs2` | `rd` |  |
| `REMU` | `rs1`, `rs2` | `rd` |  |

### RV64M Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs |
|---|---|---|---|
| `MULW` | `rs1`, `rs2` | `rd` |  |
| `DIVW` | `rs1`, `rs2` | `rd` |  |
| `DIVUW` | `rs1`, `rs2` | `rd` |  |
| `REMW` | `rs1`, `rs2` | `rd` |  |
| `REMUW` | `rs1`, `rs2` | `rd` |  |

### RV32A Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs |
|---|---|---|---|
| `LR.W†` | `rs1A` | `rd` |  |
| `SC.W†` | `rs1A`, `rs2D` | `rd*` |  |
| `AMOSWAP.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOADD.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOXOR.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOAND.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOOR.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMIN.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMAX.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMINU.W†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMAXU.W†` | `rs1A`, `rs2D` | `rd` |  |

`SC.W†` 的 `rd*` 仅在成功时作为 destination register。

### RV64A Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs |
|---|---|---|---|
| `LR.D†` | `rs1A` | `rd` |  |
| `SC.D†` | `rs1A`, `rs2D` | `rd*` |  |
| `AMOSWAP.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOADD.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOXOR.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOAND.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOOR.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMIN.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMAX.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMINU.D†` | `rs1A`, `rs2D` | `rd` |  |
| `AMOMAXU.D†` | `rs1A`, `rs2D` | `rd` |  |

`SC.D†` 的 `rd*` 仅在成功时作为 destination register。

### RV32F Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs | 注释 |
|---|---|---|---|---|
| `FLW†` | `rs1A` | `rd` |  |  |
| `FSW` | `rs1A`, `rs2D` |  |  |  |
| `FMADD.S` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FMSUB.S` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FNMSUB.S` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FNMADD.S` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FADD.S` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FSUB.S` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FMUL.S` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FDIV.S` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `DZ`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FSQRT.S` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FSGNJ.S` | `rs1`, `rs2` | `rd` |  |  |
| `FSGNJN.S` | `rs1`, `rs2` | `rd` |  |  |
| `FSGNJX.S` | `rs1`, `rs2` | `rd` |  |  |
| `FMIN.S` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FMAX.S` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FCVT.W.S` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FCVT.WU.S` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FMV.X.W` | `rs1` | `rd` |  |  |
| `FEQ.S` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FLT.S` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FLE.S` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FCLASS.S` | `rs1` | `rd` |  |  |
| `FCVT.S.W` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FCVT.S.WU` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FMV.W.X` | `rs1` | `rd` |  |  |

### RV64F Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs | 注释 |
|---|---|---|---|---|
| `FCVT.L.S` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FCVT.LU.S` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FCVT.S.L` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FCVT.S.LU` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |

### RV32D Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs | 注释 |
|---|---|---|---|---|
| `FLD†` | `rs1A` | `rd` |  |  |
| `FSD` | `rs1A`, `rs2D` |  |  |  |
| `FMADD.D` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FMSUB.D` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FNMSUB.D` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FNMADD.D` | `rs1`, `rs2`, `rs3`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FADD.D` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FSUB.D` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FMUL.D` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FDIV.D` | `rs1`, `rs2`, `frm*` | `rd` | `NV`, `DZ`, `OF`, `UF`, `NX` | `*` 若 `rm=111` |
| `FSQRT.D` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FSGNJ.D` | `rs1`, `rs2` | `rd` |  |  |
| `FSGNJN.D` | `rs1`, `rs2` | `rd` |  |  |
| `FSGNJX.D` | `rs1`, `rs2` | `rd` |  |  |
| `FMIN.D` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FMAX.D` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FCVT.S.D` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FCVT.D.S` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FEQ.D` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FLT.D` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FLE.D` | `rs1`, `rs2` | `rd` | `NV` |  |
| `FCLASS.D` | `rs1` | `rd` |  |  |
| `FCVT.W.D` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FCVT.WU.D` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FCVT.D.W` | `rs1` | `rd` |  |  |
| `FCVT.D.WU` | `rs1` | `rd` |  |  |

### RV64D Standard Extension

| 指令 | Source Registers | Destination Registers | Accumulating CSRs | 注释 |
|---|---|---|---|---|
| `FCVT.L.D` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FCVT.LU.D` | `rs1`, `frm*` | `rd` | `NV`, `NX` | `*` 若 `rm=111` |
| `FMV.X.D` | `rs1` | `rd` |  |  |
| `FCVT.D.L` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FCVT.D.LU` | `rs1`, `frm*` | `rd` | `NX` | `*` 若 `rm=111` |
| `FMV.D.X` | `rs1` | `rd` |  |  |
