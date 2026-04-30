# Chapter 16 `C` Standard Extension for Compressed Instructions, Version 2.0

本章描述当前的 RISC-V 标准压缩指令集扩展提案，扩展名为 `C`。该扩展为常用操作增加短的 16 位指令编码，从而降低静态和动态代码大小。`C` 扩展可以加入任何基础 ISA（RV32、RV64、RV128），本文使用通用术语 `RVC` 覆盖这些情形。通常，程序中 50%-60% 的 RISC-V 指令可以替换为 RVC 指令，从而带来 25%-30% 的代码大小缩减。

## 16.1 Overview

RVC 使用一种简单压缩方案，在以下情况下为常见 32 位 RISC-V 指令提供较短的 16 位版本：

- immediate 或 address offset 较小；
- 某个寄存器是零寄存器 `x0`、ABI link register `x1` 或 ABI stack pointer `x2`；
- destination register 与第一个 source register 相同；
- 使用的寄存器属于最常用的 8 个寄存器。

`C` 扩展与所有其他标准指令扩展兼容。`C` 扩展允许 16 位指令与 32 位指令自由混合，后者现在可以从任何 16 位边界开始，即 `IALIGN=16`。加入 `C` 扩展后，任何指令都不会引发 instruction-address-misaligned exception。

移除原有 32 位指令上的 32 位对齐约束，可以显著提高代码密度。

压缩指令编码在 RV32C、RV64C 和 RV128C 之间大体相同，但如表 16.4 所示，少数 opcodes 会根据基础 ISA 宽度用于不同目的。例如，地址空间更宽的 RV64C 和 RV128C 变体需要额外 opcodes 来压缩 64 位整数值的 load 和 store，而 RV32C 使用同一组 opcodes 来压缩单精度浮点值的 load 和 store。同样，RV128C 需要额外 opcodes 来表达 128 位整数值的 load 和 store，而这些 opcodes 在 RV32C 和 RV64C 中用于双精度浮点值的 load 和 store。如果实现了 `C` 扩展，那么只要也实现了相关标准浮点扩展（`F` 和/或 `D`），就必须提供相应的压缩浮点 load 和 store 指令。此外，RV32C 包含一条压缩 jump-and-link 指令，用于压缩短距离子例程调用；同一个 opcode 在 RV64C 和 RV128C 中用于压缩 `ADDIW`。

> Commentary
>
> 双精度 load 和 store 在静态和动态指令中都占有显著比例，因此 RV32C 和 RV64C 编码包含它们。

> Commentary
>
> 对当前支持的 ABI 编译得到的 benchmark 而言，单精度 load 和 store 并不是静态或动态压缩的主要来源；但对于只提供硬件单精度浮点单元、且 ABI 只支持单精度浮点数的 microcontrollers，单精度 load 和 store 的使用频率至少会与已测 benchmark 中的双精度 load 和 store 一样高。因此，RV32C 为它们提供压缩支持。

> Commentary
>
> 短距离子例程调用更可能出现在 microcontroller 的小型二进制程序中，因此 RV32C 包含这类指令。

> Commentary
>
> 针对不同基础寄存器宽度复用 opcodes 会让文档稍微复杂一些，但即使对支持多种基础 ISA 寄存器宽度的设计，实现复杂度影响也很小。压缩浮点 load/store 变体使用与更宽整数 load/store 相同的指令格式和相同的寄存器指定方式。

RVC 的设计约束是：每条 RVC 指令都扩展为基础 ISA（RV32I/E、RV64I 或 RV128I）中的一条 32 位指令，或在存在 `F` 和 `D` 标准扩展时扩展为这些扩展中的一条 32 位指令。采用这一约束有两个主要好处：

- 硬件设计可以在 decode 阶段简单地展开 RVC 指令，从而简化验证并尽量减少对现有微架构的修改。
- 编译器可以不知道 RVC 扩展的存在，把代码压缩留给 assembler 和 linker；不过，理解压缩的编译器通常可以产生更好的结果。

> Commentary
>
> 我们认为，`C` 指令和基础 `IFD` 指令之间简单一对一映射带来的多重复杂度降低，远远超过稍密编码可能带来的收益。后者要么增加只在 `C` 扩展中支持的额外指令，要么允许一条 `C` 指令编码多条 `IFD` 指令。

需要注意，`C` 扩展并非设计为独立 ISA，而是要与某个基础 ISA 配合使用。

变长指令集长期以来都用于提升代码密度。例如 1950 年代末开发的 IBM Stretch 具有 32 位和 64 位指令，其中某些 32 位指令是完整 64 位指令的压缩版本。Stretch 还使用了在某些较短指令格式中限制可寻址寄存器集合的思想，例如短分支指令只能引用某个 index register。后来的 IBM 360 架构支持简单的变长指令编码，具有 16 位、32 位或 48 位指令格式。

1963 年，CDC 推出了由 Cray 设计的 CDC 6600，它是 RISC 架构的先驱，采用寄存器丰富的 load-store 架构，指令长度为 15 位和 30 位。后来的 Cray-1 设计使用非常相似的指令格式，指令长度为 16 位和 32 位。

20 世纪 80 年代的初始 RISC ISA 都选择性能优先于代码大小；这对 workstation 环境是合理的，但不适合 embedded systems。因此，ARM 和 MIPS 随后都开发了 ISA 版本，通过提供替代标准 32 位宽指令的 16 位宽指令集来缩小代码大小。压缩 RISC ISA 相对于其起点把代码大小降低约 25%-30%，生成的代码显著小于 80x86。这一结果令一些人惊讶，因为他们直觉上认为变长 CISC ISA 应该比只提供 16 位和 32 位格式的 RISC ISA 更小。

由于原始 RISC ISA 没有留下足够的 opcode 空间来包含这些未预先规划的压缩指令，它们后来被发展为全新的 ISA。这意味着编译器需要为独立的压缩 ISA 使用不同的 code generator。第一代压缩 RISC ISA 扩展（例如 ARM Thumb 和 MIPS16）只使用固定 16 位指令大小，这能很好降低静态代码大小，但会增加动态指令数，从而相对于原始固定 32 位指令大小降低性能。这促成了第二代压缩 RISC ISA 设计，其混合使用 16 位和 32 位指令长度（例如 ARM Thumb2、microMIPS、PowerPC VLE），使性能接近纯 32 位指令，同时显著节省代码大小。遗憾的是，这些不同代际的压缩 ISA 彼此之间以及与原始非压缩 ISA 都不兼容，导致文档、实现和软件工具支持显著复杂。

在常用 64 位 ISA 中，当前只有 PowerPC 和 microMIPS 支持压缩指令格式。考虑到静态代码大小和动态取指带宽是重要指标，最流行的移动平台 64 位 ISA（ARM v8）没有包含压缩指令格式令人意外。虽然静态代码大小在大型系统中未必是主要问题，但在运行 commercial workloads 的服务器中，instruction fetch bandwidth 可能成为主要瓶颈，因为这类工作负载通常有很大的 instruction working set。

RISC-V 受益于 25 年的经验回顾，从一开始就被设计为支持压缩指令，并为 RVC 留下足够 opcode 空间，使其能够作为基础 ISA 之上的简单扩展加入，同时也给许多其他扩展留出空间。RVC 的理念是为 embedded applications 缩小代码大小，并通过减少 instruction cache miss 为所有应用提升性能和能效。Waterman 显示，RVC 获取的 instruction bits 少 25%-30%，这会把 instruction cache misses 降低 20%-25%，大致相当于把 instruction cache 大小翻倍所带来的性能影响。

## 16.2 Compressed Instruction Formats

表 16.1 给出九种压缩指令格式。`CR`、`CI` 和 `CSS` 可以使用任意 32 个 RVI 寄存器；但 `CIW`、`CL`、`CS`、`CA` 和 `CB` 只限于其中 8 个寄存器。表 16.2 列出这些常用寄存器，它们对应 `x8` 到 `x15`。注意，load 和 store 指令另有使用 stack pointer 作为基址寄存器的版本，因为保存到栈和从栈恢复非常常见；这些指令使用 `CI` 和 `CSS` 格式，以便访问全部 32 个数据寄存器。`CIW` 为 `ADDI4SPN` 指令提供 8 位 immediate。

> Commentary
>
> RISC-V ABI 被修改为让频繁使用的寄存器映射到 `x8`-`x15`。这让解压缩 decoder 可以使用连续且自然对齐的寄存器编号集合，从而简化设计；同时它也与只有 16 个整数寄存器的 RV32E 基础 ISA 兼容。

压缩的基于寄存器的浮点 load 和 store 也分别使用 `CL` 和 `CS` 格式，其中 8 个寄存器映射到 `f8` 到 `f15`。

> Commentary
>
> 标准 RISC-V calling convention 把最常用的浮点寄存器映射到 `f8` 到 `f15`，这使浮点寄存器编号可以使用与整数寄存器编号相同的寄存器解压缩 decoding。

这些格式的设计目标是：在所有指令中，让两个 register source specifiers 的位保持在相同位置，而 destination register 字段可以移动。当存在完整 5 位 destination register specifier 时，它位于与 32 位 RISC-V 编码相同的位置。凡是 immediate 需要 sign-extended，其符号扩展总是来自位 12。与基础规范一样，immediate 字段被打散，以减少所需 immediate mux 的数量。

> Commentary
>
> 指令格式中的 immediate 字段被打散，而不是按顺序排列，是为了让尽可能多的位在每条指令中处于相同位置，从而简化实现。例如，immediate 位 17-10 总是来自相同的指令位位置。另有五个 immediate 位（5、4、3、1 和 0）只有两个源指令位，四个位（9、7、6 和 2）有三个源，一个位（8）有四个源。

对许多 RVC 指令而言，值为零的 immediates 不允许使用，`x0` 也不是有效的 5 位寄存器指定符。这些限制释放了编码空间，可供其他需要较少 operand bits 的指令使用。

表 16.1：压缩 16 位 RVC 指令格式。

| Format | Meaning | 编码字段概要 |
|---|---|---|
| `CR` | Register | `funct4 rd/rs1 rs2 op` |
| `CI` | Immediate | `funct3 imm rd/rs1 imm op` |
| `CSS` | Stack-relative Store | `funct3 imm rs2 op` |
| `CIW` | Wide Immediate | `funct3 imm rd' op` |
| `CL` | Load | `funct3 imm rs1' imm rd' op` |
| `CS` | Store | `funct3 imm rs1' imm rs2' op` |
| `CA` | Arithmetic | `funct6 rd'/rs1' funct2 rs2' op` |
| `CB` | Branch | `funct3 offset rs1' offset op` |
| `CJ` | Jump | `funct3 jump target op` |

表 16.2：`CIW`、`CL`、`CS`、`CA` 和 `CB` 格式的三位 `rs1'`、`rs2'` 和 `rd'` 字段指定的寄存器。

| RVC Register Number | `000` | `001` | `010` | `011` | `100` | `101` | `110` | `111` |
|---|---|---|---|---|---|---|---|---|
| Integer Register Number | `x8` | `x9` | `x10` | `x11` | `x12` | `x13` | `x14` | `x15` |
| Integer Register ABI Name | `s0` | `s1` | `a0` | `a1` | `a2` | `a3` | `a4` | `a5` |
| Floating-Point Register Number | `f8` | `f9` | `f10` | `f11` | `f12` | `f13` | `f14` | `f15` |
| Floating-Point Register ABI Name | `fs0` | `fs1` | `fa0` | `fa1` | `fa2` | `fa3` | `fa4` | `fa5` |

## 16.3 Load and Store Instructions

为了增加 16 位指令的可达范围，数据传送指令使用 zero-extended immediates，并按数据字节大小缩放：word 为 `x4`，double word 为 `x8`，quad word 为 `x16`。

RVC 提供两类 load 和 store 变体。一类使用 ABI stack pointer `x2` 作为基址，并可指向任意数据寄存器。另一类可引用 8 个基址寄存器之一和 8 个数据寄存器之一。

### Stack-Pointer-Based Loads and Stores

以下指令使用 `CI` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.LWSP` | `offset[5] dest!=0 offset[4:2|7:6] C2` | `lw rd, offset[7:2](x2)` | 从 `x2` 加按 4 缩放的 zero-extended offset 处加载 32 位值到 `rd`；`rd=x0` 编码保留 |
| `C.LDSP` | `offset[5] dest!=0 offset[4:3|8:6] C2` | `ld rd, offset[8:3](x2)` | RV64C/RV128C-only；加载 64 位值；`rd=x0` 编码保留 |
| `C.LQSP` | `offset[5] dest!=0 offset[4|9:6] C2` | `lq rd, offset[9:4](x2)` | RV128C-only；加载 128 位值；`rd=x0` 编码保留 |
| `C.FLWSP` | `offset[5] dest offset[4:2|7:6] C2` | `flw rd, offset[7:2](x2)` | RV32FC-only；加载单精度浮点值到浮点寄存器 `rd` |
| `C.FLDSP` | `offset[5] dest offset[4:3|8:6] C2` | `fld rd, offset[8:3](x2)` | RV32DC/RV64DC-only；加载双精度浮点值到浮点寄存器 `rd` |

以下指令使用 `CSS` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.SWSP` | `offset[5:2|7:6] src C2` | `sw rs2, offset[7:2](x2)` | 将 `rs2` 中的 32 位值存入 `x2` 加按 4 缩放的 offset 处 |
| `C.SDSP` | `offset[5:3|8:6] src C2` | `sd rs2, offset[8:3](x2)` | RV64C/RV128C-only；存储 64 位值 |
| `C.SQSP` | `offset[5:4|9:6] src C2` | `sq rs2, offset[9:4](x2)` | RV128C-only；存储 128 位值 |
| `C.FSWSP` | `offset[5:2|7:6] src C2` | `fsw rs2, offset[7:2](x2)` | RV32FC-only；存储单精度浮点值 |
| `C.FSDSP` | `offset[5:3|8:6] src C2` | `fsd rs2, offset[8:3](x2)` | RV32DC/RV64DC-only；存储双精度浮点值 |

函数入口/出口处的寄存器保存/恢复代码占静态代码大小的显著部分。RVC 中基于 stack pointer 的压缩 load 和 store 能把保存/恢复代码的静态大小降低约 2 倍，同时通过降低动态指令带宽来提升性能。

其他 ISA 中进一步减少保存/恢复代码大小的常见机制是 load-multiple 和 store-multiple 指令。RISC-V 曾考虑采用这些指令，但注意到以下缺点：

- 这些指令会使处理器实现复杂化。
- 对虚拟内存系统，一些数据访问可能驻留在物理内存中，而另一些可能不在；这要求为部分执行的指令提供新的 restart 机制。
- 与其余 RVC 指令不同，Load Multiple 和 Store Multiple 没有 `IFD` 等价指令。
- 与其余 RVC 指令不同，编译器必须知道这些指令，既要生成它们，也要按顺序分配寄存器，以最大化被保存和恢复的机会，因为这些寄存器会按顺序保存和恢复。
- 简单微架构实现会限制其他指令围绕 load/store multiple 指令的调度方式，从而可能造成性能损失。
- 对顺序寄存器分配的需求可能与 `CIW`、`CL`、`CS`、`CA` 和 `CB` 格式选出的 featured registers 冲突。

此外，通过把 prologue 和 epilogue 代码替换为对公共 prologue 和 epilogue 代码的子例程调用，可以在软件中实现大部分收益；这种技术见文献 [23] 的 5.6 节。

> Commentary
>
> 尽管理性的架构师可能得出不同结论，我们决定省略 load multiple 和 store multiple，而采用纯软件方式调用 save/restore millicode routines，以取得最大的代码大小缩减。

### Register-Based Loads and Stores

以下 load 指令使用 `CL` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.LW` | `offset[5:3] base offset[2|6] dest C0` | `lw rd', offset[6:2](rs1')` | 加载 32 位值到 `rd'` |
| `C.LD` | `offset[5:3] base offset[7:6] dest C0` | `ld rd', offset[7:3](rs1')` | RV64C/RV128C-only；加载 64 位值 |
| `C.LQ` | `offset[5|4|8] base offset[7:6] dest C0` | `lq rd', offset[8:4](rs1')` | RV128C-only；加载 128 位值 |
| `C.FLW` | `offset[5:3] base offset[2|6] dest C0` | `flw rd', offset[6:2](rs1')` | RV32FC-only；加载单精度浮点值 |
| `C.FLD` | `offset[5:3] base offset[7:6] dest C0` | `fld rd', offset[7:3](rs1')` | RV32DC/RV64DC-only；加载双精度浮点值 |

这些指令通过把按数据大小缩放的 zero-extended offset 加到 `rs1'` 中的基址来计算有效地址。

以下 store 指令使用 `CS` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.SW` | `offset[5:3] base offset[2|6] src C0` | `sw rs2', offset[6:2](rs1')` | 存储 32 位值 |
| `C.SD` | `offset[5:3] base offset[7:6] src C0` | `sd rs2', offset[7:3](rs1')` | RV64C/RV128C-only；存储 64 位值 |
| `C.SQ` | `offset[5|4|8] base offset[7:6] src C0` | `sq rs2', offset[8:4](rs1')` | RV128C-only；存储 128 位值 |
| `C.FSW` | `offset[5:3] base offset[2|6] src C0` | `fsw rs2', offset[6:2](rs1')` | RV32FC-only；存储单精度浮点值 |
| `C.FSD` | `offset[5:3] base offset[7:6] src C0` | `fsd rs2', offset[7:3](rs1')` | RV32DC/RV64DC-only；存储双精度浮点值 |

## 16.4 Control Transfer Instructions

RVC 提供无条件 jump 指令和条件 branch 指令。与基础 RVI 指令一样，所有 RVC 控制转移指令的 offsets 都以 2 字节为倍数。

`C.J` 和 `C.JAL` 使用 `CJ` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.J` | `offset[11|4|9:8|10|6|7|3:1|5] C1` | `jal x0, offset[11:1]` | 执行无条件控制转移；offset sign-extended 后加到 `pc` 形成目标；可达 `+/-2 KiB` |
| `C.JAL` | `offset[11|4|9:8|10|6|7|3:1|5] C1` | `jal x1, offset[11:1]` | RV32C-only；同 `C.J`，并把跳转后一条指令地址 `pc+2` 写入 link register `x1` |

`C.JR` 和 `C.JALR` 使用 `CR` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.JR` | `src!=0 0 C2` | `jalr x0, 0(rs1)` | 跳转到寄存器 `rs1` 中的地址；`rs1=x0` 编码保留 |
| `C.JALR` | `src!=0 0 C2` | `jalr x1, 0(rs1)` | 同 `C.JR`，并把 `pc+2` 写入 `x1`；`rs1=x0` 编码对应 `C.EBREAK` |

严格来说，`C.JALR` 并不完全展开为基础 RVI 指令，因为用于形成 link address 的 PC 增量是 2，而基础 ISA 中为 4；但同时支持 2 字节和 4 字节 offset 只需要对基础微架构做很小修改。

`C.BEQZ` 和 `C.BNEZ` 使用 `CB` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.BEQZ` | `offset[8|4:3] src offset[7:6|2:1|5] C1` | `beq rs1', x0, offset[8:1]` | 若 `rs1'` 为 0 则跳转；offset sign-extended 后加到 `pc`；可达 `+/-256 B` |
| `C.BNEZ` | `offset[8|4:3] src offset[7:6|2:1|5] C1` | `bne rs1', x0, offset[8:1]` | 若 `rs1'` 非 0 则跳转 |

## 16.5 Integer Computational Instructions

RVC 提供若干用于整数算术和常量生成的指令。

### Integer Constant-Generation Instructions

两条常量生成指令都使用 `CI` 指令格式，并可指向任意整数寄存器。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.LI` | `imm[5] dest!=0 imm[4:0] C1` | `addi rd, x0, imm[5:0]` | 把 sign-extended 6 位 immediate 加载到 `rd`；`rd=x0` 编码为 HINT |
| `C.LUI` | `nzimm[17] dest!={0,2} nzimm[16:12] C1` | `lui rd, nzimm[17:12]` | 把非零 6 位 immediate 加载到目的寄存器位 17-12，清除低 12 位，并把位 17 sign-extend 到高位 |

`C.LUI` 仅当 `rd!={x0,x2}` 且 immediate 非零时有效。`nzimm=0` 的 code points 保留；剩余 `rd=x0` 的 code points 是 HINTs；剩余 `rd=x2` 的 code points 对应 `C.ADDI16SP`。

### Integer Register-Immediate Operations

这些整数 register-immediate 操作编码为 `CI` 格式，对一个整数寄存器和 6 位 immediate 执行操作。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.ADDI` | `nzimm[5] dest!=0 nzimm[4:0] C1` | `addi rd, rd, nzimm[5:0]` | 把非零 sign-extended 6 位 immediate 加到 `rd`，结果写回 `rd` |
| `C.ADDIW` | `imm[5] dest!=0 imm[4:0] C1` | `addiw rd, rd, imm[5:0]` | RV64C/RV128C-only；产生 32 位结果并 sign-extend；immediate 可为 0，对应 `sext.w rd` |
| `C.ADDI16SP` | `nzimm[9] 2 nzimm[4|6|8:7|5] C1` | `addi x2, x2, nzimm[9:4]` | 调整 stack pointer；immediate 表示 16 的倍数，范围为 `(-512, 496)` |

`C.ADDI` 仅当 `rd!=x0` 且 `nzimm!=0` 时有效。`rd=x0` 的 code points 编码 `C.NOP`；剩余 `nzimm=0` 的 code points 编码 HINTs。

`C.ADDIW` 仅当 `rd!=x0` 时有效；`rd=x0` 的 code points 保留。

`C.ADDI16SP` 与 `C.LUI` 共享 opcode，但 destination 字段为 `x2`。它用于 procedure prologues 和 epilogues 中调整 stack pointer。`C.ADDI16SP` 仅当 `nzimm!=0` 时有效；`nzimm=0` 的 code point 保留。在标准 RISC-V calling convention 中，stack pointer `sp` 总是 16 字节对齐。

`C.ADDI4SPN` 是 `CIW` 格式指令，把按 4 缩放的 zero-extended 非零 immediate 加到 stack pointer `x2`，并把结果写到 `rd'`。该指令用于生成指向 stack-allocated variables 的指针，并展开为 `addi rd', x2, nzuimm[9:2]`。`C.ADDI4SPN` 仅当 `nzuimm!=0` 时有效；`nzuimm=0` 的 code points 保留。

| 指令 | 编码概要 | 展开 |
|---|---|---|
| `C.ADDI4SPN` | `nzuimm[5:4|9:6|2|3] dest C0` | `addi rd', x2, nzuimm[9:2]` |

`C.SLLI` 是 `CI` 格式指令，对寄存器 `rd` 中的值执行 logical left shift，并把结果写回 `rd`。shift amount 编码在 `shamt` 字段中。对于 RV128C，shift amount 为 0 用来编码左移 64。除 RV128C 且 `shamt=0` 时展开为 `slli rd, rd, 64` 外，`C.SLLI` 展开为 `slli rd, rd, shamt[5:0]`。

对于 RV32C，`shamt[5]` 必须为 0；`shamt[5]=1` 的 code points 保留给 custom extensions。对于 RV32C 和 RV64C，shift amount 必须非零；`shamt=0` 的 code points 是 HINTs。对所有基础 ISA，`rd=x0` 的 code points 是 HINTs，但 RV32C 中 `shamt[5]=1` 的情况除外。

`C.SRLI` 是 `CB` 格式指令，对寄存器 `rd'` 中的值执行 logical right shift，并把结果写回 `rd'`。shift amount 编码在 `shamt` 字段中。对于 RV128C，shift amount 为 0 用来编码右移 64。此外，对 RV128C，shift amount 被 sign-extended，因此合法 shift amounts 为 1-31、64 和 96-127。除 RV128C 且 `shamt=0` 时展开为 `srli rd', rd', 64` 外，`C.SRLI` 展开为 `srli rd', rd', shamt[5:0]`。

对于 RV32C，`shamt[5]` 必须为 0；`shamt[5]=1` 的 code points 保留给 custom extensions。对于 RV32C 和 RV64C，shift amount 必须非零；`shamt=0` 的 code points 是 HINTs。

`C.SRAI` 与 `C.SRLI` 类似定义，但执行 arithmetic right shift。`C.SRAI` 展开为 `srai rd', rd', shamt[5:0]`。

> Commentary
>
> 左移通常比右移更常见，因为左移经常用于缩放地址值。因此右移获得的编码空间较少，并被放在所有其他 immediates 都 sign-extended 的编码 quadrant 中。对于 RV128，设计选择让 6 位 shift-amount immediate 也被 sign-extended。除了降低 decode 复杂度外，我们认为 96-127 的右移量会比 64-95 更有用，因为它们可以提取位于 128 位地址指针高部的 tags。需要注意，RV128C 不会与 RV32C 和 RV64C 在同一时间点冻结，以便评估 128 位地址空间代码的典型用法。

`C.ANDI` 是 `CB` 格式指令，计算寄存器 `rd'` 的值与 sign-extended 6 位 immediate 的 bitwise AND，并把结果写回 `rd'`。`C.ANDI` 展开为 `andi rd', rd', imm[5:0]`。

### Integer Register-Register Operations

`C.MV` 和 `C.ADD` 使用 `CR` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.MV` | `dest!=0 src!=0 C2` | `add rd, x0, rs2` | 把 `rs2` 的值复制到 `rd`；`rs2=x0` 对应 `C.JR`；`rs2!=x0` 且 `rd=x0` 为 HINT |
| `C.ADD` | `dest!=0 src!=0 C2` | `add rd, rd, rs2` | 把 `rd` 与 `rs2` 相加并写回 `rd`；`rs2=x0` 对应 `C.JALR` 和 `C.EBREAK`；`rs2!=x0` 且 `rd=x0` 为 HINT |

> Commentary
>
> `C.MV` 展开为与 canonical `MV` pseudoinstruction 不同的指令；后者使用 `ADDI`。如果实现对 `MV` 做特殊处理，例如通过 register-renaming hardware，可能会发现把 `C.MV` 展开为 `MV` 而不是 `ADD` 更方便，只需付出很小的额外硬件成本。

以下指令使用 `CA` 格式。

| 指令 | 编码概要 | 展开 | 说明 |
|---|---|---|---|
| `C.AND` | `dest C.AND src C1` | `and rd', rd', rs2'` | bitwise AND |
| `C.OR` | `dest C.OR src C1` | `or rd', rd', rs2'` | bitwise OR |
| `C.XOR` | `dest C.XOR src C1` | `xor rd', rd', rs2'` | bitwise XOR |
| `C.SUB` | `dest C.SUB src C1` | `sub rd', rd', rs2'` | 从 `rd'` 减去 `rs2'` |
| `C.ADDW` | `dest C.ADDW src C1` | `addw rd', rd', rs2'` | RV64C/RV128C-only；相加后将低 32 位 sign-extend |
| `C.SUBW` | `dest C.SUBW src C1` | `subw rd', rd', rs2'` | RV64C/RV128C-only；相减后将低 32 位 sign-extend |

> Commentary
>
> 这一组六条指令单独看节省不大，但它们占用编码空间很少，实现直接；作为一组，它们对静态和动态压缩提供了有价值的改进。

### Defined Illegal Instruction

一个所有位都为 0 的 16 位指令被永久保留为 illegal instruction。

> Commentary
>
> 保留全零指令作为 illegal instructions，有助于捕获尝试执行内存空间中被清零或不存在部分的行为。全零值不应在任何非标准扩展中重新定义。类似地，所有位都为 1 的指令（在 RISC-V 变长编码方案中对应 very long instructions）也被保留为 illegal，用于捕获不存在内存区域中常见的另一个值。

### NOP Instruction

`C.NOP` 是 `CI` 格式指令，除了推进 `pc` 并递增任何适用的 performance counters 外，不改变任何用户可见状态。`C.NOP` 展开为 `nop`。`C.NOP` 仅当 `imm=0` 时有效；`imm!=0` 的 code points 编码 HINTs。

| 指令 | 编码概要 | 展开 |
|---|---|---|
| `C.NOP` | `0 0 0 C1` | `nop` |

### Breakpoint Instruction

调试器可以使用 `C.EBREAK` 指令使控制权转回 debugging environment。`C.EBREAK` 展开为 `ebreak`。`C.EBREAK` 与 `C.ADD` 共享 opcode，但 `rd` 和 `rs2` 都为 0，因此也可以使用 `CR` 格式。

| 指令 | 编码概要 | 展开 |
|---|---|---|
| `C.EBREAK` | `0 C2` | `ebreak` |

## 16.6 Usage of C Instructions in LR/SC Sequences

在支持 `C` 扩展的实现上，8.3 节描述的 constrained LR/SC sequences 中允许出现的 `I` 指令的压缩形式，也允许出现在 constrained LR/SC sequences 中。

其含义是，任何声称同时支持 `A` 和 `C` 扩展的实现，都必须保证包含有效 `C` 指令的 LR/SC sequences 最终会完成。

## 16.7 HINT Instructions

RVC 编码空间的一部分保留给 microarchitectural HINTs。与 RV32I 基础 ISA 中的 HINTs（见 2.9 节）一样，除了推进 `pc` 和任何适用的 performance counters 外，这些指令不修改任何 architectural state。在忽略它们的实现上，HINTs 作为 no-ops 执行。

RVC HINTs 被编码为不修改 architectural state 的计算指令，要么因为 `rd=x0`（例如 `C.ADD x0, t0`），要么因为 `rd` 被自身的副本覆盖（例如 `C.ADDI t0, 0`）。

> Commentary
>
> 选择这种 HINT 编码，是为了让简单实现可以完全忽略 HINTs，而把 HINT 当作一条恰好不改变 architectural state 的普通计算指令执行。

RVC HINTs 不一定展开为对应的 RVI HINT。例如，`C.ADD x0, t0` 不一定编码与 `ADD x0, x0, t0` 相同的 HINT。

> Commentary
>
> 不要求 RVC HINT 展开为 RVI HINT 的主要原因是，HINTs 不太可能以与底层计算指令相同的方式被压缩。此外，解耦 RVC 和 RVI HINT 映射，可以把稀缺的 RVC HINT 空间分配给最常用的 HINTs，特别是适合 macro-op fusion 的 HINTs。

表 16.3 列出所有 RVC HINT code points。对于 RV32C，78% 的 HINT 空间保留给未来标准 HINTs，但当前尚未定义任何标准 HINT。其余 HINT 空间保留给 custom HINTs：标准 HINT 永远不会在这一子空间中定义。

表 16.3：RVC HINT 指令。

| Instruction | Constraints | Code Points | Purpose |
|---|---|---:|---|
| `C.NOP` | `nzimm!=0` | 63 | Reserved for future standard use |
| `C.ADDI` | `rd!=x0, nzimm=0` | 31 | Reserved for future standard use |
| `C.LI` | `rd=x0` | 64 | Reserved for future standard use |
| `C.LUI` | `rd=x0, nzimm!=0` | 63 | Reserved for future standard use |
| `C.MV` | `rd=x0, rs2!=x0` | 31 | Reserved for future standard use |
| `C.ADD` | `rd=x0, rs2!=x0` | 31 | Reserved for future standard use |
| `C.SLLI` | `rd=x0, nzimm!=0` | 31 (RV32) / 63 (RV64/128) | Reserved for custom use |
| `C.SLLI64` | `rd=x0` | 1 | Reserved for custom use |
| `C.SLLI64` | `rd!=x0, RV32 and RV64 only` | 31 | Reserved for custom use |
| `C.SRLI64` | `RV32 and RV64 only` | 8 | Reserved for custom use |
| `C.SRAI64` | `RV32 and RV64 only` | 8 | Reserved for custom use |

## 16.8 RVC Instruction Set Listings

表 16.4 给出 RVC major opcodes 映射。表中的每一行对应编码空间的一个 quadrant。最后一个 quadrant 的两个最低有效位为 1，对应宽于 16 位的指令，包括基础 ISA 中的指令。若干指令只对某些 operands 有效；无效时，它们被标记为 `RES`、`NSE` 或 `HINT`：`RES` 表示 opcode 保留给未来标准扩展；`NSE` 表示 opcode 保留给 custom extensions；`HINT` 表示 opcode 保留给 microarchitectural hints（见 16.7 节）。

表 16.4：RVC opcode map。

| `inst[1:0]` / `inst[15:13]` | `000` | `001` | `010` | `011` | `100` | `101` | `110` | `111` |
|---|---|---|---|---|---|---|---|---|
| `00`, RV32 | `ADDI4SPN` | `FLD` | `LW` | `FLW` | Reserved | `FSD` | `SW` | `FSW` |
| `00`, RV64 | `ADDI4SPN` | `FLD` | `LW` | `LD` | Reserved | `FSD` | `SW` | `SD` |
| `00`, RV128 | `ADDI4SPN` | `LQ` | `LW` | `LD` | Reserved | `SQ` | `SW` | `SD` |
| `01`, RV32 | `ADDI` | `JAL` | `LI` | `LUI/ADDI16SP` | `MISC-ALU` | `J` | `BEQZ` | `BNEZ` |
| `01`, RV64 | `ADDI` | `ADDIW` | `LI` | `LUI/ADDI16SP` | `MISC-ALU` | `J` | `BEQZ` | `BNEZ` |
| `01`, RV128 | `ADDI` | `ADDIW` | `LI` | `LUI/ADDI16SP` | `MISC-ALU` | `J` | `BEQZ` | `BNEZ` |
| `10`, RV32 | `SLLI` | `FLDSP` | `LWSP` | `FLWSP` | `J[AL]R/MV/ADD` | `FSDSP` | `SWSP` | `FSWSP` |
| `10`, RV64 | `SLLI` | `FLDSP` | `LWSP` | `LDSP` | `J[AL]R/MV/ADD` | `FSDSP` | `SWSP` | `SDSP` |
| `10`, RV128 | `SLLI` | `LQSP` | `LWSP` | `LDSP` | `J[AL]R/MV/ADD` | `SQSP` | `SWSP` | `SDSP` |
| `11` | `>16b` | `>16b` | `>16b` | `>16b` | `>16b` | `>16b` | `>16b` | `>16b` |

表 16.5-16.7 列出 RVC 指令。

表 16.5：RVC Quadrant 0 指令列表。

| `inst[15:13]` | 编码字段 | `inst[1:0]` | 指令/状态 |
|---|---|---|---|
| `000` | `0 0 00` | `00` | Illegal instruction |
| `000` | `nzuimm[5:4|9:6|2|3] rd'` | `00` | `C.ADDI4SPN` (`RES` when `nzuimm=0`) |
| `001` | `uimm[5:3] rs1' uimm[7:6] rd'` | `00` | `C.FLD` (RV32/64) |
| `001` | `uimm[5:4|8] rs1' uimm[7:6] rd'` | `00` | `C.LQ` (RV128) |
| `010` | `uimm[5:3] rs1' uimm[2|6] rd'` | `00` | `C.LW` |
| `011` | `uimm[5:3] rs1' uimm[2|6] rd'` | `00` | `C.FLW` (RV32) |
| `011` | `uimm[5:3] rs1' uimm[7:6] rd'` | `00` | `C.LD` (RV64/128) |
| `100` | `-` | `00` | Reserved |
| `101` | `uimm[5:3] rs1' uimm[7:6] rs2'` | `00` | `C.FSD` (RV32/64) |
| `101` | `uimm[5:4|8] rs1' uimm[7:6] rs2'` | `00` | `C.SQ` (RV128) |
| `110` | `uimm[5:3] rs1' uimm[2|6] rs2'` | `00` | `C.SW` |
| `111` | `uimm[5:3] rs1' uimm[2|6] rs2'` | `00` | `C.FSW` (RV32) |
| `111` | `uimm[5:3] rs1' uimm[7:6] rs2'` | `00` | `C.SD` (RV64/128) |

表 16.6：RVC Quadrant 1 指令列表。

| `inst[15:13]` | 编码字段 | `inst[1:0]` | 指令/状态 |
|---|---|---|---|
| `000` | `nzimm[5] 0 nzimm[4:0]` | `01` | `C.NOP` (`HINT` when `nzimm!=0`) |
| `000` | `nzimm[5] rs1/rd!=0 nzimm[4:0]` | `01` | `C.ADDI` (`HINT` when `nzimm=0`) |
| `001` | `imm[11|4|9:8|10|6|7|3:1|5]` | `01` | `C.JAL` (RV32) |
| `001` | `imm[5] rs1/rd!=0 imm[4:0]` | `01` | `C.ADDIW` (RV64/128; `RES` when `rd=0`) |
| `010` | `imm[5] rd!=0 imm[4:0]` | `01` | `C.LI` (`HINT` when `rd=0`) |
| `011` | `nzimm[9] 2 nzimm[4|6|8:7|5]` | `01` | `C.ADDI16SP` (`RES` when `nzimm=0`) |
| `011` | `nzimm[17] rd!={0,2} nzimm[16:12]` | `01` | `C.LUI` (`RES` when `nzimm=0`; `HINT` when `rd=0`) |
| `100` | `nzuimm[5] 00 rs1'/rd' nzuimm[4:0]` | `01` | `C.SRLI` (RV32 `NSE` when `nzuimm[5]=1`) |
| `100` | `0 00 rs1'/rd' 0` | `01` | `C.SRLI64` (RV128; RV32/64 `HINT`) |
| `100` | `nzuimm[5] 01 rs1'/rd' nzuimm[4:0]` | `01` | `C.SRAI` (RV32 `NSE` when `nzuimm[5]=1`) |
| `100` | `0 01 rs1'/rd' 0` | `01` | `C.SRAI64` (RV128; RV32/64 `HINT`) |
| `100` | `imm[5] 10 rs1'/rd' imm[4:0]` | `01` | `C.ANDI` |
| `100` | `0 11 rs1'/rd' 00 rs2'` | `01` | `C.SUB` |
| `100` | `0 11 rs1'/rd' 01 rs2'` | `01` | `C.XOR` |
| `100` | `0 11 rs1'/rd' 10 rs2'` | `01` | `C.OR` |
| `100` | `0 11 rs1'/rd' 11 rs2'` | `01` | `C.AND` |
| `100` | `1 11 rs1'/rd' 00 rs2'` | `01` | `C.SUBW` (RV64/128; RV32 `RES`) |
| `100` | `1 11 rs1'/rd' 01 rs2'` | `01` | `C.ADDW` (RV64/128; RV32 `RES`) |
| `100` | `1 11 - 10 -` | `01` | Reserved |
| `100` | `1 11 - 11 -` | `01` | Reserved |
| `101` | `imm[11|4|9:8|10|6|7|3:1|5]` | `01` | `C.J` |
| `110` | `imm[8|4:3] rs1' imm[7:6|2:1|5]` | `01` | `C.BEQZ` |
| `111` | `imm[8|4:3] rs1' imm[7:6|2:1|5]` | `01` | `C.BNEZ` |

表 16.7：RVC Quadrant 2 指令列表。

| `inst[15:13]` | 编码字段 | `inst[1:0]` | 指令/状态 |
|---|---|---|---|
| `000` | `nzuimm[5] rs1/rd!=0 nzuimm[4:0]` | `10` | `C.SLLI` (`HINT` when `rd=0`; RV32 `NSE` when `nzuimm[5]=1`) |
| `000` | `0 rs1/rd!=0 0` | `10` | `C.SLLI64` (RV128; RV32/64 `HINT`; `HINT` when `rd=0`) |
| `001` | `uimm[5] rd uimm[4:3|8:6]` | `10` | `C.FLDSP` (RV32/64) |
| `001` | `uimm[5] rd!=0 uimm[4|9:6]` | `10` | `C.LQSP` (RV128; `RES` when `rd=0`) |
| `010` | `uimm[5] rd!=0 uimm[4:2|7:6]` | `10` | `C.LWSP` (`RES` when `rd=0`) |
| `011` | `uimm[5] rd uimm[4:2|7:6]` | `10` | `C.FLWSP` (RV32) |
| `011` | `uimm[5] rd!=0 uimm[4:3|8:6]` | `10` | `C.LDSP` (RV64/128; `RES` when `rd=0`) |
| `100` | `0 rs1!=0 0` | `10` | `C.JR` (`RES` when `rs1=0`) |
| `100` | `0 rd!=0 rs2!=0` | `10` | `C.MV` (`HINT` when `rd=0`) |
| `100` | `1 0 0` | `10` | `C.EBREAK` |
| `100` | `1 rs1!=0 0` | `10` | `C.JALR` |
| `100` | `1 rs1/rd!=0 rs2!=0` | `10` | `C.ADD` (`HINT` when `rd=0`) |
| `101` | `uimm[5:3|8:6] rs2` | `10` | `C.FSDSP` (RV32/64) |
| `101` | `uimm[5:4|9:6] rs2` | `10` | `C.SQSP` (RV128) |
| `110` | `uimm[5:2|7:6] rs2` | `10` | `C.SWSP` |
| `111` | `uimm[5:2|7:6] rs2` | `10` | `C.FSWSP` (RV32) |
| `111` | `uimm[5:3|8:6] rs2` | `10` | `C.SDSP` (RV64/128) |
