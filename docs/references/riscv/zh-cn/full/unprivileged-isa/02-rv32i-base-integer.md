# 第 2 章 RV32I 基础整数指令集，版本 2.1

本章描述 RV32I base integer instruction set 的 2.0 版本。

RV32I 的设计目标是足以形成 compiler target，并支持现代 operating system environment。该 ISA 也被设计为减少最小实现所需的硬件。RV32I 包含 40 条唯一指令；不过，一个简单实现可以用一条始终 trap 的 `SYSTEM` 硬件指令覆盖 `ECALL`/`EBREAK` 指令，并且可以把 `FENCE` 指令实现为 `NOP`，从而把 base instruction count 减少到总共 38 条。RV32I 几乎可以模拟任何其他 ISA extension（`A` 扩展除外，因为它需要额外硬件支持 atomicity）。

> 实践中，一个包含 machine-mode privileged architecture 的硬件实现还会需要 6 条 CSR 指令。

> base integer ISA 的子集可能对教学用途有用，但 base 已经定义成这样：真实硬件实现除了省略对 misaligned memory access 的支持，以及把所有 `SYSTEM` 指令作为单一 trap 处理之外，应该没有太大动力继续裁剪。

> RV32I 的大部分 commentary 也适用于 RV64I base。

## 2.1 基础整数 ISA 的程序员模型

图 2.1 展示 base integer ISA 的 unprivileged state。对于 RV32I，32 个 `x` register 每个都是 32 bit 宽，即 `XLEN=32`。寄存器 `x0` 硬连为所有 bit 均等于 0。通用寄存器 `x1`-`x31` 保存的值，会被不同指令解释为 Boolean value 集合、two's complement signed binary integer，或 unsigned binary integer。

还有一个额外的 unprivileged register：program counter `pc` 保存当前指令的地址。

```text
XLEN-1                                                    0
x0 / zero
x1
x2
...
x31
XLEN

XLEN-1                                                    0
pc
XLEN
```

图 2.1：RISC-V base unprivileged integer register state。

Base Integer ISA 中没有专用 stack pointer，也没有专用 subroutine return address link register；指令编码允许任意 `x` register 用于这些用途。不过，标准 software calling convention 使用寄存器 `x1` 保存 call 的 return address，并提供寄存器 `x5` 作为 alternate link register。标准 calling convention 使用寄存器 `x2` 作为 stack pointer。

> 硬件可以选择加速使用 `x1` 或 `x5` 的 function call 和 return。参见 `JAL` 和 `JALR` 指令的描述。

> 可选的 compressed 16-bit instruction format 围绕以下假设设计：`x1` 是 return address register，`x2` 是 stack pointer。使用其他约定的软件仍会正确运行，但代码大小可能更大。

可用 architectural register 的数量会显著影响代码大小、性能和能耗。虽然对运行编译代码的 integer ISA 来说，16 个寄存器也可以说是足够的，但无法使用 3-address format 在 16-bit 指令中编码完整 ISA。虽然 2-address format 是可能的，但它会增加 instruction count 并降低效率。我们希望避免中间指令大小（例如 Xtensa 的 24-bit 指令），以简化 base 硬件实现；一旦采用 32-bit instruction size，支持 32 个 integer register 就很直接。更多 integer register 也有助于高性能代码的性能，在这些代码中可能大量使用 loop unrolling、software pipelining 和 cache tiling。

> 基于这些原因，我们为 base ISA 选择了传统规模的 32 个 integer register。动态寄存器使用往往由少数频繁访问的寄存器主导，regfile 实现可以优化以降低频繁访问寄存器的访问能耗。可选 compressed 16-bit instruction format 大多只访问 8 个寄存器，因此能提供高密度 instruction encoding；如果需要，额外 instruction-set extension 也可以支持更大的 register space（flat 或 hierarchical）。

> 对资源受限的 embedded application，我们定义了只具有 16 个寄存器的 RV32E 子集（第 4 章）。

## 2.2 基础指令格式

在 base RV32I ISA 中，有四种核心指令格式（`R`/`I`/`S`/`U`），如图 2.2 所示。所有指令都是固定 32 bit 长度，并且在 memory 中必须对齐到 4-byte 边界。如果 taken branch 或 unconditional jump 的 target address 不是 4-byte 对齐，则产生 instruction-address-misaligned exception。该 exception 报告在 branch 或 jump 指令上，而不是报告在 target instruction 上。对于未 taken 的 conditional branch，不产生 instruction-address-misaligned exception。

> 当加入具有 16-bit 长度或其他 16-bit 奇数倍长度的 instruction extension 时，base ISA 指令的对齐约束放宽为 2-byte 边界（即 `IALIGN=16`）。

> instruction-address-misaligned exception 报告在会导致指令未对齐的 branch 或 jump 上，这有助于调试，也简化 `IALIGN=32` 系统的硬件设计，因为这些位置是唯一可能发生未对齐的地方。

解码 reserved instruction 时的行为是 unspecified。

> 某些平台可能要求为标准用途保留的 opcode 引发 illegal-instruction exception。其他平台可能允许 reserved opcode space 用于 non-conforming extension。

RISC-V ISA 在所有格式中把 source register（`rs1` 和 `rs2`）与 destination register（`rd`）保持在相同位置，以简化解码。除 CSR 指令（第 9 章）中使用的 5-bit immediate 外，immediate 总是 sign-extended，并且通常打包在指令中最左侧可用 bit 处；这些分配旨在降低硬件复杂度。特别地，所有 immediate 的 sign bit 始终位于指令 bit 31，以加速 sign-extension 电路。

> register specifier 的解码通常位于实现的 critical path 上，因此指令格式被选择为让所有 register specifier 在所有格式中保持相同位置，代价是必须在不同格式之间移动 immediate bit（RISC-IV，也就是 SPUR，也具有这一性质）。

```text
31      25 24   20 19   15 14  12 11    7 6     0
funct7     rs2     rs1    funct3   rd      opcode   R-type
imm[11:0]          rs1    funct3   rd      opcode   I-type
imm[11:5] rs2      rs1    funct3   imm[4:0] opcode  S-type
imm[31:12]                         rd      opcode   U-type
```

图 2.2：RISC-V base instruction format。每个 immediate 子字段用它所产生的 immediate value 中的 bit 位置（`imm[x]`）标注，而不是像通常做法那样用 instruction immediate field 内的 bit 位置标注。

> 实践中，大多数 immediate 要么很小，要么需要所有 XLEN bit。我们选择了非对称 immediate 划分（常规指令中 12 bit，加上一条具有 20 bit 的特殊 load-upper-immediate 指令），以增加常规指令可用的 opcode space。

> immediate 使用 sign-extension，是因为我们没有观察到像 MIPS ISA 那样对某些 immediate 使用 zero-extension 会带来收益，并且我们希望尽量保持 ISA 简单。

## 2.3 立即数编码变体

基于 immediate 的处理方式，还有另外两种指令格式变体（`B`/`J`），如图 2.3 所示。

```text
31      30 25 24 21 20 19 15 14 12 11 8 7 6 0
funct7  rs2      rs1    funct3 rd       opcode           R-type
imm[11:0]        rs1    funct3 rd       opcode           I-type
imm[11:5] rs2    rs1    funct3 imm[4:0] opcode           S-type
imm[12] imm[10:5] rs2 rs1 funct3 imm[4:1] imm[11] opcode B-type
imm[31:12]                       rd     opcode           U-type
imm[20] imm[10:1] imm[11] imm[19:12] rd opcode           J-type
```

图 2.3：展示 immediate 变体的 RISC-V base instruction format。

`S` 格式和 `B` 格式之间唯一的区别是：`B` 格式中 12-bit immediate field 用于编码以 2 为倍数的 branch offset。与通常在硬件中把 instruction-encoded immediate 的所有 bit 左移一位不同，中间 bit（`imm[10:1]`）和 sign bit 保持在固定位置，而 `S` 格式中的最低 bit（`inst[7]`）在 `B` 格式中编码一个高位 bit。

类似地，`U` 格式和 `J` 格式之间唯一的区别是：20-bit immediate 在形成 `U` immediate 时左移 12 bit，在形成 `J` immediate 时左移 1 bit。`U` 和 `J` 格式 immediate 中 instruction bit 的位置被选择为最大化与其他格式以及彼此之间的重叠。

图 2.4 展示每种 base instruction format 产生的 immediate，并标注哪个 instruction bit（`inst[y]`）产生 immediate value 的每个 bit。

```text
31        30 20       19 12       11    10 5       4 1 0
-- inst[31] --        inst[30:25] inst[24:21] inst[20]      I-immediate
-- inst[31] --        inst[30:25] inst[11:8]  inst[7]       S-immediate
-- inst[31] --        inst[7]     inst[30:25] inst[11:8] 0  B-immediate
inst[31] inst[30:20]  inst[19:12] --          0 --          U-immediate
-- inst[31] --        inst[19:12] inst[20]    inst[30:25] inst[24:21] 0 J-immediate
```

图 2.4：RISC-V 指令产生的 immediate 类型。字段标注为用于构造其值的 instruction bit。Sign extension 始终使用 `inst[31]`。

> Sign-extension 是 immediate 上最关键的操作之一（尤其当 `XLEN > 32` 时）。在 RISC-V 中，所有 immediate 的 sign bit 始终保存在指令 bit 31 中，从而允许 sign-extension 与 instruction decoding 并行进行。

> 虽然更复杂的实现可能具有用于 branch 和 jump 计算的独立 adder，因此不会从跨指令类型保持 immediate bit 位置不变中获益，但我们希望降低最简单实现的硬件成本。通过在 `B` 和 `J` immediate 的 instruction encoding 中旋转 bit，而不是使用动态硬件 mux 将 immediate 乘以 2，我们把 instruction signal fanout 和 immediate mux 成本降低约 2 倍。打乱的 immediate encoding 对静态编译或 ahead-of-time compilation 增加的时间可以忽略不计。对于动态生成指令，有一些小额额外开销，但最常见的短 forward branch 具有直接的 immediate encoding。

## 2.4 整数计算指令

大多数 integer computational instruction 对 integer register file 中保存的 XLEN bit 值进行操作。Integer computational instruction 要么编码为使用 `I-type` 格式的 register-immediate operation，要么编码为使用 `R-type` 格式的 register-register operation。register-immediate 和 register-register 指令的 destination 都是寄存器 `rd`。没有 integer computational instruction 会导致 arithmetic exception。

> 我们没有在 base instruction set 中包含用于 integer arithmetic operation overflow check 的专门 instruction-set 支持，因为许多 overflow check 可以使用 RISC-V branch 低成本实现。Unsigned addition 的 overflow checking 只需在加法后增加一条 branch 指令：
>
> ```asm
> add  t0, t1, t2
> bltu t0, t1, overflow
> ```
>
> 对 signed addition，如果一个 operand 的符号已知，overflow checking 只需在加法后增加一条 branch：
>
> ```asm
> addi t0, t1, +imm
> blt  t0, t1, overflow
> ```
>
> 这覆盖了与 immediate operand 相加的常见情况。
>
> 对一般 signed addition，利用这样一个观察：sum 小于某个 operand 当且仅当另一个 operand 为负数。因此加法后需要三条额外指令：
>
> ```asm
> add  t0, t1, t2
> slti t3, t2, 0
> slt  t4, t0, t1
> bne  t3, t4, overflow
> ```
>
> 在 RV64I 中，可以通过比较 operand 上 `ADD` 和 `ADDW` 的结果，进一步优化 32-bit signed addition 的检查。

### 整数 register-immediate 指令

```text
31       20 19 15 14 12 11 7 6 0
imm[11:0]  rs1  funct3 rd   opcode
12         5    3      5    7

I-immediate[11:0] src ADDI/SLTI[U] dest OP-IMM
I-immediate[11:0] src ANDI/ORI/XORI dest OP-IMM
```

`ADDI` 把 sign-extended 12-bit immediate 加到寄存器 `rs1`。Arithmetic overflow 被忽略，结果只是完整结果的低 XLEN bit。`ADDI rd, rs1, 0` 用于实现 assembler pseudoinstruction `MV rd, rs1`。

`SLTI`（set less than immediate）在寄存器 `rs1` 小于 sign-extended immediate 时，把值 1 放入寄存器 `rd`；二者都按 signed number 处理。否则向 `rd` 写入 0。`SLTIU` 类似，但把值作为 unsigned number 比较（即 immediate 先 sign-extended 到 XLEN bit，再作为 unsigned number 处理）。注意，`SLTIU rd, rs1, 1` 在 `rs1` 等于零时把 `rd` 置为 1，否则把 `rd` 置为 0（assembler pseudoinstruction `SEQZ rd, rs`）。

`ANDI`、`ORI`、`XORI` 是 logical operation，对寄存器 `rs1` 和 sign-extended 12-bit immediate 执行 bitwise AND、OR、XOR，并把结果放入 `rd`。注意，`XORI rd, rs1, -1` 对寄存器 `rs1` 执行 bitwise logical inversion（assembler pseudoinstruction `NOT rd, rs`）。

```text
31      25 24   20 19 15 14 12 11 7 6 0
imm[11:5] imm[4:0] rs1 funct3 rd opcode
7          5        5   3      5  7

0000000 shamt[4:0] src SLLI dest OP-IMM
0000000 shamt[4:0] src SRLI dest OP-IMM
0100000 shamt[4:0] src SRAI dest OP-IMM
```

按常量移位被编码为 `I-type` 格式的特化形式。待移位的 operand 位于 `rs1`，移位量编码在 I-immediate field 的低 5 bit 中。右移类型编码在 bit 30 中。`SLLI` 是 logical left shift（0 被移入低位）；`SRLI` 是 logical right shift（0 被移入高位）；`SRAI` 是 arithmetic right shift（原始 sign bit 被复制到空出的高位）。

```text
31       12 11 7 6 0
imm[31:12] rd  opcode
20         5   7

U-immediate[31:12] dest LUI
U-immediate[31:12] dest AUIPC
```

`LUI`（load upper immediate）用于构造 32-bit 常量，并使用 `U-type` 格式。`LUI` 把 U-immediate 值放入 destination register `rd` 的最高 20 bit，并用零填充最低 12 bit。

`AUIPC`（add upper immediate to `pc`）用于构造 pc-relative address，并使用 `U-type` 格式。`AUIPC` 从 20-bit U-immediate 形成 32-bit offset，最低 12 bit 填 0，把该 offset 加到 `AUIPC` 指令的地址，然后把结果放入寄存器 `rd`。

> `AUIPC` 指令支持用两条指令序列访问相对于 PC 的任意 offset，包括 control-flow transfer 和 data access。`AUIPC` 与 `JALR` 中的 12-bit immediate 组合，可以把控制转移到任意 32-bit PC-relative address；`AUIPC` 加上普通 load 或 store 指令中的 12-bit immediate offset，可以访问任意 32-bit PC-relative data address。

> 当前 PC 可以通过把 U-immediate 设置为 0 获得。虽然也可以使用 `JAL +4` 指令获得 local PC（即 `JAL` 后一条指令的地址），但它可能在更简单的微架构中导致 pipeline break，或在更复杂微架构中污染 BTB 结构。

### 整数 register-register 操作

RV32I 定义了若干 arithmetic `R-type` operation。所有 operation 都读取 `rs1` 和 `rs2` 寄存器作为 source operand，并把结果写入寄存器 `rd`。`funct7` 和 `funct3` 字段选择 operation 类型。

```text
31      25 24 20 19 15 14 12 11 7 6 0
funct7     rs2   rs1   funct3 rd   opcode
7          5     5     3      5    7

0000000 src2 src1 ADD/SLT/SLTU dest OP
0000000 src2 src1 AND/OR/XOR   dest OP
0000000 src2 src1 SLL/SRL      dest OP
0100000 src2 src1 SUB/SRA      dest OP
```

`ADD` 执行 `rs1` 和 `rs2` 的加法。`SUB` 从 `rs1` 中减去 `rs2`。Overflow 被忽略，结果的低 XLEN bit 写入 destination `rd`。`SLT` 和 `SLTU` 分别执行 signed compare 和 unsigned compare；若 `rs1 < rs2`，向 `rd` 写 1，否则写 0。注意，`SLTU rd, x0, rs2` 在 `rs2` 不等于零时把 `rd` 置为 1，否则把 `rd` 置为零（assembler pseudoinstruction `SNEZ rd, rs`）。`AND`、`OR` 和 `XOR` 执行 bitwise logical operation。

`SLL`、`SRL` 和 `SRA` 对寄存器 `rs1` 中的值分别执行 logical left、logical right 和 arithmetic right shift，移位量保存在寄存器 `rs2` 的低 5 bit 中。

### `NOP` 指令

```text
31       20 19 15 14 12 11 7 6 0
imm[11:0]  rs1  funct3 rd   opcode
12         5    3      5    7

0          0    ADDI   0    OP-IMM
```

`NOP` 指令不改变任何 architecturally visible state，除了推进 `pc` 并增加任何适用 performance counter。`NOP` 编码为 `ADDI x0, x0, 0`。

`NOP` 可用于把 code segment 对齐到对微架构有意义的地址边界，或为 inline code modification 留出空间。虽然有许多可能方式编码 `NOP`，但我们定义 canonical `NOP` encoding，以允许微架构优化，并使 disassembly 输出更易读。其他 `NOP` 编码提供给 `HINT` 指令使用（第 2.9 节）。

> 选择 `ADDI` 作为 `NOP` 编码，是因为它在各种系统中执行时最可能占用最少资源（如果未在 decode 时优化掉）。特别是，该指令只读取一个寄存器。此外，在 superscalar 设计中，`ADDI` functional unit 更可能可用，因为 add 是最常见操作。尤其是，address-generation functional unit 可以用 base+offset address calculation 所需的同一硬件执行 `ADDI`，而 register-register `ADD` 或 logical/shift operation 需要额外硬件。

## 2.5 控制转移指令

RV32I 提供两类 control transfer instruction：unconditional jump 和 conditional branch。RV32I 中的 control transfer instruction 没有 architecturally visible delay slot。

### Unconditional Jump

jump and link（`JAL`）指令使用 `J-type` 格式，其中 J-immediate 编码以 2 byte 为倍数的 signed offset。该 offset 被 sign-extended，并加到 jump 指令的地址上，形成 jump target address。因此 jump 可以定位到 ±1 MiB 范围内的目标。

`JAL` 把 jump 后一条指令的地址（`pc+4`）保存到寄存器 `rd`。标准 software calling convention 使用 `x1` 作为 return address register，并使用 `x5` 作为 alternate link register。alternate link register 支持调用 millicode routine（例如 compressed code 中保存和恢复寄存器的例程），同时保留常规 return address register。选择寄存器 `x5` 作为 alternate link register，是因为它在标准 calling convention 中映射为 temporary，并且其编码与常规 link register 只差 1 bit。

普通 unconditional jump（assembler pseudoinstruction `J`）编码为 `rd=x0` 的 `JAL`。

```text
31      30 21 20 19 12 11 7 6 0
imm[20] imm[10:1] imm[11] imm[19:12] rd opcode
1       10        1       8          5  7

offset[20:1] dest JAL
```

indirect jump 指令 `JALR`（jump and link register）使用 `I-type` 编码。target address 通过把 sign-extended 12-bit I-immediate 加到寄存器 `rs1` 得到，然后把结果的 least-significant bit 置为零。jump 后一条指令的地址（`pc+4`）写入寄存器 `rd`。如果不需要结果，可以使用寄存器 `x0` 作为 destination。

```text
31       20 19 15 14 12 11 7 6 0
imm[11:0]  rs1 funct3 rd   opcode
12         5   3      5    7

offset[11:0] base 0 dest JALR
```

> Unconditional jump 指令全部使用 PC-relative addressing，以帮助支持 position-independent code。定义 `JALR` 指令是为了支持一个两条指令序列跳转到 32-bit absolute address range 中的任何位置。`LUI` 指令可以先把 target address 的高 20 bit 载入 `rs1`，然后 `JALR` 加入低位。类似地，`AUIPC` 后接 `JALR` 可以跳转到 32-bit pc-relative address range 中的任何位置。

> 注意，与 conditional branch 指令不同，`JALR` 指令不把 12-bit immediate 视为 2 byte 的倍数。这样可以在硬件中避免再增加一种 immediate format。实践中，`JALR` 的大多数用法要么具有零 immediate，要么与 `LUI` 或 `AUIPC` 成对使用，因此范围略微减小并不重要。

> 在计算 `JALR` target address 时清除 least-significant bit，既略微简化了硬件，也允许 function pointer 的低 bit 用于保存辅助信息。虽然这可能略微损失错误检查能力，但实践中跳转到错误 instruction address 通常会很快引发 exception。

> 当使用 `rs1=x0` 作为 base 时，`JALR` 可用于从 address space 中任意位置实现一条指令的 subroutine call，调用最低 2 KiB 或最高 2 KiB 地址区域；这可用于快速调用小型 runtime library。另一种方式是 ABI 可以专用一个 general-purpose register，使其指向 address space 中其他位置的库。

如果 target address 未对齐到 4-byte 边界，`JAL` 和 `JALR` 指令会产生 instruction-address-misaligned exception。

> 在支持具有 16-bit 对齐指令的 extension 的机器上，例如 compressed instruction-set extension `C`，不可能发生 instruction-address-misaligned exception。

Return-address prediction stack 是高性能 instruction-fetch unit 的常见特性，但要有效工作，需要准确检测哪些指令用于 procedure call 和 return。对 RISC-V 来说，对指令用途的 hint 通过所用寄存器编号隐式编码。只有当 `rd=x1/x5` 时，`JAL` 指令才应把 return address push 到 return-address stack（RAS）。`JALR` 指令应按表 2.1 所示 push/pop RAS。

> 一些其他 ISA 在 indirect-jump 指令中增加显式 hint bit，以指导 return-address stack 操作。我们使用与寄存器编号和 calling convention 绑定的隐式 hint，以减少这些 hint 使用的 encoding space。

| `rd` | `rs1` | `rs1=rd` | RAS action |
|---|---|---|---|
| `!link` | `!link` | - | none |
| `!link` | `link` | - | pop |
| `link` | `!link` | - | push |
| `link` | `link` | 0 | pop, then push |
| `link` | `link` | 1 | push |

表 2.1：寄存器指示符中编码的 return-address stack prediction hint。上表中，当寄存器为 `x1` 或 `x5` 时，`link` 为 true。

> 当 `rs1` 和 `rd` 给出两个不同 link register（`x1` 和 `x5`）时，RAS 同时 pop 和 push，以支持 coroutine。如果 `rs1` 和 `rd` 是同一个 link register（`x1` 或 `x5`），RAS 只 push，以支持以下序列的 macro-op fusion：
>
> ```asm
> lui   ra, imm20
> jalr  ra, imm12(ra)
>
> auipc ra, imm20
> jalr  ra, imm12(ra)
> ```

### Conditional Branch

所有 branch 指令都使用 `B-type` instruction format。12-bit B-immediate 编码以 2 byte 为倍数的 signed offset。该 offset 被 sign-extended，并加到 branch 指令的地址上，得到 target address。conditional branch range 为 ±4 KiB。

```text
31      30 25 24 20 19 15 14 12 11 8 7 6 0
imm[12] imm[10:5] rs2 rs1 funct3 imm[4:1] imm[11] opcode
1       6         5   5   3      4        1       7

offset[12|10:5] src2 src1 BEQ/BNE offset[11|4:1] BRANCH
offset[12|10:5] src2 src1 BLT[U]  offset[11|4:1] BRANCH
offset[12|10:5] src2 src1 BGE[U]  offset[11|4:1] BRANCH
```

branch 指令比较两个寄存器。`BEQ` 和 `BNE` 分别在寄存器 `rs1` 与 `rs2` 相等或不相等时采取分支。`BLT` 和 `BLTU` 分别使用 signed comparison 和 unsigned comparison，在 `rs1` 小于 `rs2` 时采取分支。`BGE` 和 `BGEU` 分别使用 signed comparison 和 unsigned comparison，在 `rs1` 大于或等于 `rs2` 时采取分支。注意，`BGT`、`BGTU`、`BLE` 和 `BLEU` 可分别通过反转 `BLT`、`BLTU`、`BGE` 和 `BGEU` 的 operand 合成。

> Signed array bounds 可以用一条 `BLTU` 指令检查，因为任何负索引都会比较为大于任何非负 bound。

软件应优化为让 sequential code path 成为最常见路径，并把较少采取的 code path 放在 out of line 位置。软件还应假定 backward branch 会预测为 taken，forward branch 会预测为 not taken，至少在首次遇到时如此。Dynamic predictor 应很快学习任何可预测 branch 行为。

与某些其他体系结构不同，RISC-V jump（`rd=x0` 的 `JAL`）指令应始终用于 unconditional branch，而不是使用具有 always-true 条件的 conditional branch 指令。RISC-V jump 也是 PC-relative 的，支持比 branch 宽得多的 offset range，并且不会污染 conditional-branch prediction table。

> conditional branch 被设计为包含两个寄存器之间的 arithmetic comparison operation（PA-RISC、Xtensa 和 MIPS R6 也这样做），而不是使用 condition code（x86、ARM、SPARC、PowerPC），或只把一个寄存器与零比较（Alpha、MIPS），或只比较两个寄存器是否相等（MIPS）。这一设计的动机是：合并的 compare-and-branch 指令适合常规 pipeline，避免额外 condition code state 或 temporary register 的使用，并减少 static code size 和 dynamic instruction fetch traffic。另一点是，与零比较需要非平凡的 circuit delay（尤其是在先进工艺中转向 static logic 之后），因此几乎与 arithmetic magnitude compare 一样昂贵。fused compare-and-branch 指令的另一个优点是 branch 在 front-end instruction stream 中更早被观察到，因此可以更早预测。对于多个 branch 可基于相同 condition code 采取的情况，使用 condition code 的设计或许有优势，但我们认为这种情况相对少见。

> 我们考虑过但没有在 instruction encoding 中包含 static branch hint。这些 hint 可以减轻 dynamic predictor 压力，但需要更多 instruction encoding space，并且为了获得最佳结果需要 software profiling；如果 production run 与 profiling run 不匹配，还可能导致性能较差。

> 我们考虑过但没有包含 conditional move 或 predicated instruction；它们可以有效替代不可预测的短 forward branch。二者中 conditional move 更简单，但难以用于可能导致 exception 的条件代码（memory access 和 floating-point operation）。Predication 会向系统增加额外 flag state，增加设置和清除 flag 的指令，并在每条指令上增加额外 encoding overhead。conditional move 和 predicated instruction 都会增加 out-of-order microarchitecture 的复杂度，因为当 predicate 为 false 时，需要把 destination architectural register 的原始值复制到 renamed destination physical register 中，从而增加一个隐式 third source operand。此外，编译期静态决定使用 predication 而不是 branch，可能在不包含于 compiler training set 的输入上导致较低性能；尤其考虑到不可预测 branch 很少见，并且随着 branch prediction 技术改善正变得更少见。

> 我们注意到，存在各种微架构技术可动态地把不可预测短 forward branch 转换为内部 predicated code，以避免 branch mispredict 时 flush pipeline 的成本，并且这些技术已经在商业处理器中实现。最简单的技术只是降低从 mispredicted short forward branch 恢复的代价：只 flush branch shadow 中的指令，而不是整个 fetch pipeline；或者使用宽 instruction fetch 或空闲 instruction fetch slot 从两个方向取指。面向 out-of-order core 的更复杂技术，会在 branch shadow 中的指令上增加 internal predicate，并由 branch 指令写入 internal predicate value，从而允许 branch 和后续指令相对于其他代码被 speculative 和 out-of-order 执行。

如果 target address 未对齐到 4-byte 边界，并且 branch condition 计算为 true，conditional branch 指令会产生 instruction-address-misaligned exception。如果 branch condition 计算为 false，则不会引发 instruction-address-misaligned exception。

> 在支持具有 16-bit 对齐指令的 extension 的机器上，例如 compressed instruction-set extension `C`，不可能发生 instruction-address-misaligned exception。

## 2.6 Load 和 Store 指令

RV32I 是 load-store architecture，只有 load 和 store 指令访问 memory，arithmetic 指令只对 CPU register 操作。RV32I 提供 byte-addressed 的 32-bit address space。EEI 会定义 address space 的哪些部分可由哪些指令合法访问（例如，某些地址可能只读，或只支持 word access）。destination 为 `x0` 的 load 仍必须引发任何 exception，并导致任何其他 side effect，即使 load value 被丢弃。

EEI 会定义 memory system 是 little-endian 还是 big-endian。在 RISC-V 中，endianness 是 byte-address invariant。

> 在 endianness 为 byte-address invariant 的系统中，以下性质成立：如果某个 byte 在某种 endianness 下存储到 memory 中某地址，那么在任何 endianness 下从该地址执行 byte-sized load 都会返回该存储值。

> 在 little-endian 配置中，multibyte store 把 least-significant register byte 写到最低 memory byte address，然后按照显著性递增的顺序写入其他 register byte。load 类似地把较低 memory byte address 的内容传送到较低显著性的 register byte。

> 在 big-endian 配置中，multibyte store 把 most-significant register byte 写到最低 memory byte address，然后按照显著性递减的顺序写入其他 register byte。load 类似地把较高 memory byte address 的内容传送到较低显著性的 register byte。

```text
31       20 19 15 14 12 11 7 6 0
imm[11:0]  rs1 funct3 rd   opcode
12         5   3      5    7
offset[11:0] base width dest LOAD

31      25 24 20 19 15 14 12 11 7 6 0
imm[11:5] rs2 rs1 funct3 imm[4:0] opcode
7         5   5   3      5        7
offset[11:5] src base width offset[4:0] STORE
```

Load 和 store 指令在 register 和 memory 之间传送一个值。Load 编码为 `I-type` 格式，store 编码为 `S-type`。effective address 通过把寄存器 `rs1` 与 sign-extended 12-bit offset 相加得到。Load 把值从 memory 复制到寄存器 `rd`。Store 把寄存器 `rs2` 中的值复制到 memory。

`LW` 指令从 memory 加载 32-bit 值到 `rd`。`LH` 从 memory 加载 16-bit 值，然后在存入 `rd` 前 sign-extend 到 32 bit。`LHU` 从 memory 加载 16-bit 值，但在存入 `rd` 前 zero-extend 到 32 bit。`LB` 和 `LBU` 对 8-bit 值作类似定义。`SW`、`SH` 和 `SB` 指令把寄存器 `rs2` 低位中的 32-bit、16-bit 和 8-bit 值存储到 memory。

无论 EEI 如何，effective address 自然对齐的 load 和 store 不应引发 address-misaligned exception。effective address 未按所引用 datatype 自然对齐的 load 和 store（即 32-bit access 未对齐到 4-byte 边界，16-bit access 未对齐到 2-byte 边界），其行为依赖 EEI。

EEI 可以保证完全支持 misaligned load 和 store，因此运行在 execution environment 内的软件永远不会经历 contained 或 fatal address-misaligned trap。在这种情况下，misaligned load 和 store 可以由硬件处理，也可以通过进入 execution environment implementation 的 invisible trap 处理，或根据地址由硬件和 invisible trap 组合处理。

EEI 也可以不保证 misaligned load 和 store 会被不可见地处理。在这种情况下，未自然对齐的 load 和 store 可能成功完成执行，也可能引发 exception。引发的 exception 可以是 address-misaligned exception，也可以是 access-fault exception。对于除了 misalignment 之外本来可以完成的 memory access，如果该 misaligned access 不应被模拟，例如访问具有 side effect 的 memory region，那么可以引发 access exception，而不是 address-misaligned exception。当 EEI 不保证 misaligned load 和 store 被不可见处理时，EEI 必须定义由 address misalignment 导致的 exception 是产生 contained trap（允许运行在 execution environment 内的软件处理该 trap）还是 fatal trap（终止执行）。

> 移植 legacy code 时偶尔需要 misaligned access；在使用任何形式的 packed-SIMD extension 或处理外部 packed data structure 时，它们也有助于应用性能。我们允许 EEI 选择通过普通 load 和 store 指令支持 misaligned access，理由是为了简化 misaligned 硬件支持的添加。
>
> 一种选择本来是在 base ISA 中禁止 misaligned access，然后为 misaligned access 提供某种单独 ISA 支持：要么提供特殊指令帮助软件处理 misaligned access，要么为 misaligned access 提供新的硬件 addressing mode。特殊指令难以使用，会使 ISA 复杂化，并且常常增加新的 processor state（例如 SPARC VIS align address offset register），或使访问既有 processor state 复杂化（例如 MIPS `LWL`/`LWR` partial register write）。此外，对于 loop-oriented packed-SIMD code，当 operand 未对齐时，额外开销会促使软件根据 operand alignment 提供多种 loop 形式，这会使 code generation 复杂化，并增加 loop startup overhead。新的 misaligned hardware addressing mode 会占用相当多 instruction encoding 空间，或要求非常简化的 addressing mode（例如仅 register indirect）。

即使 misaligned load 和 store 成功完成，这些 access 根据实现也可能运行得极慢（例如通过 invisible trap 实现时）。此外，虽然自然对齐的 load 和 store 保证原子执行，但 misaligned load 和 store 可能不是原子的，因此需要额外 synchronization 来保证 atomicity。

> 我们不强制 misaligned access 具有 atomicity，因此 execution environment implementation 可以使用 invisible machine trap 和 software handler 处理部分或全部 misaligned access。如果提供硬件 misaligned 支持，软件可以直接使用普通 load 和 store 指令利用它。硬件随后可以根据运行时地址是否对齐自动优化访问。

## 2.7 Memory Ordering 指令

```text
31 28 27 26 25 24 23 22 21 20 19 15 14 12 11 7 6 0
fm    PI PO PR PW SI SO SR SW rs1 funct3 rd opcode
4     1  1  1  1  1  1  1  1  5   3      5  7

FM predecessor successor 0 FENCE 0 MISC-MEM
```

`FENCE` 指令用于按照其他 RISC-V hart、external device 或 coprocessor 所观察到的顺序，对 device I/O 和 memory access 排序。device input（`I`）、device output（`O`）、memory read（`R`）和 memory write（`W`）的任意组合，都可以相对于同类的任意组合排序。非正式地说，其他 RISC-V hart 或 external device 不能观察到 `FENCE` 后 successor set 中的任何 operation，早于 `FENCE` 前 predecessor set 中的任何 operation。第 14 章提供 RISC-V memory consistency model 的精确定义。

EEI 会定义哪些 I/O operation 是可能的；特别是，定义通过 load 和 store 指令访问哪些 memory address 时，会分别被视作 device input 和 device output operation，而不是 memory read 和 write。例如，memory-mapped I/O device 通常会使用 uncached load 和 store 访问，并用 `I` 和 `O` bit 而不是 `R` 和 `W` bit 排序。Instruction-set extension 也可能描述新的 I/O 指令，这些指令也会使用 `FENCE` 中的 `I` 和 `O` bit 排序。

| `fm` field | Mnemonic | Meaning |
|---|---|---|
| `0000` | none | Normal Fence |
| `1000` | `TSO` | 与 `FENCE RW,RW` 一起使用时：排除 write-to-read ordering；其他情况下保留供未来使用 |
| other |  | 保留供未来使用 |

表 2.2：Fence mode encoding。

fence mode field `fm` 定义 `FENCE` 的语义。`fm=0000` 的 `FENCE` 把 predecessor set 中的所有 memory operation 排在 successor set 中的所有 memory operation 之前。

可选的 `FENCE.TSO` 指令编码为一条 `FENCE` 指令，其中 `fm=1000`、`predecessor=RW`、`successor=RW`。`FENCE.TSO` 把 predecessor set 中的所有 load operation 排在 successor set 中的所有 memory operation 之前，并把 predecessor set 中的所有 store operation 排在 successor set 中的所有 store operation 之前。这使 `FENCE.TSO` 的 predecessor set 中的 non-AMO store operation 与 successor set 中的 non-AMO load 不排序。

> `FENCE.TSO` 编码作为原始 base `FENCE` 指令编码的可选扩展加入。base 定义要求实现忽略任何被置位的 bit，并把 `FENCE` 当作 global fence，因此这是一个 backward-compatible extension。

`FENCE` 指令中未使用字段 `rs1` 和 `rd` 为未来扩展中的 finer-grain fence 保留。为了前向兼容，base implementation 应忽略这些字段，standard software 应把这些字段置零。同样，表 2.2 中许多 `fm` 和 predecessor/successor set 设置也为未来使用保留。Base implementation 应把所有这类 reserved configuration 视为 `fm=0000` 的 normal fence，standard software 只应使用 non-reserved configuration。

> 我们选择 relaxed memory model，是为了让简单机器实现以及未来可能的 coprocessor 或 accelerator extension 获得高性能。我们把 I/O ordering 与 memory R/W ordering 分开，以避免 device-driver hart 内不必要的 serialization，并支持用于控制新增 coprocessor 或 I/O device 的替代 non-memory path。
>
> 简单实现还可以忽略 predecessor 和 successor 字段，并始终对所有 operation 执行保守 fence。

## 2.8 Environment Call 和 Breakpoint

`SYSTEM` 指令用于访问可能需要 privileged access 的 system functionality，并使用 `I-type` instruction format 编码。它们可以分成两个主要类别：一类是原子地 read-modify-write control and status register（CSR）的指令，另一类是所有其他 potentially privileged instruction。CSR 指令在第 9 章描述，base unprivileged instruction 在下一节描述。

> 定义 `SYSTEM` 指令，是为了允许更简单的实现总是 trap 到单一 software trap handler。更复杂的实现可以用硬件执行每条 system instruction 的更多部分。

```text
31      20 19 15 14 12 11 7 6 0
funct12    rs1 funct3 rd   opcode
12         5   3      5    7

ECALL  0 PRIV 0 SYSTEM
EBREAK 0 PRIV 0 SYSTEM
```

这两条指令会导致 precise requested trap 到支持它们的 execution environment。

`ECALL` 指令用于向 execution environment 发出 service request。EEI 会定义 service request 的参数如何传递，但通常这些参数位于 integer register file 中定义的位置。

`EBREAK` 指令用于把控制权返回 debugging environment。

> `ECALL` 和 `EBREAK` 过去分别名为 `SCALL` 和 `SBREAK`。这些指令具有相同功能和编码，但被重命名，以反映它们可比调用 supervisor-level operating system 或 debugger 更一般地使用。

> `EBREAK` 主要设计为供 debugger 使用，使执行停止并回退到 debugger。标准 gcc compiler 也使用 `EBREAK` 标记不应执行的 code path。

`EBREAK` 的另一个用途是支持 “semihosting”。在这种情况下，execution environment 包含一个 debugger，它可以通过围绕 `EBREAK` 指令构建的替代 system call interface 提供服务。由于 RISC-V base ISA 没有提供多于一条 `EBREAK` 指令，RISC-V semihosting 使用一个特殊指令序列，把 semihosting `EBREAK` 与 debugger 插入的 `EBREAK` 区分开。

```asm
slli   x0, x0, 0x1f   # Entry NOP
ebreak                 # Break to debugger
srai   x0, x0, 7      # NOP encoding the semihosting call number 7
```

注意，这三条指令必须是 32-bit-wide instruction，也就是说，它们不能属于第 16 章描述的 compressed 16-bit instruction。

shift `NOP` 指令仍被视为可作为 `HINT` 使用。

> Semihosting 是一种 service call，更自然的编码方式是使用既有 ABI 的 `ECALL`；但这要求 debugger 能够拦截 `ECALL`，而这是 debug standard 中较新的增加项。我们打算转向使用带标准 ABI 的 `ECALL`，届时 semihosting 可以与既有标准共享 service ABI。

> 我们注意到，在较新设计中，ARM processor 也已经转向使用 `SVC` 而不是 `BKPT` 进行 semihosting call。

## 2.9 `HINT` 指令

RV32I 为 `HINT` 指令保留了大量 encoding space，这些指令通常用于向微架构传达 performance hint。`HINT` 编码为 `rd=x0` 的 integer computational instruction。因此，像 `NOP` 指令一样，`HINT` 不改变任何 architecturally visible state，除了推进 `pc` 和任何适用 performance counter。实现始终允许忽略编码的 hint。

> 选择这种 `HINT` 编码，是为了让简单实现可以完全忽略 `HINT`，而是把 `HINT` 作为一条恰好不会改变 architectural state 的普通 computational instruction 执行。例如，如果 destination register 是 `x0`，`ADD` 就是一条 `HINT`；5-bit `rs1` 和 `rs2` 字段编码 `HINT` 的参数。不过，简单实现可以直接把该 `HINT` 作为 `rs1` 和 `rs2` 的 `ADD` 执行，并写入 `x0`，这没有 architecturally visible effect。

表 2.3 列出所有 RV32I `HINT` code point。`HINT` 空间的 91% 保留给 standard `HINT`，但目前尚未定义任何 standard `HINT`。`HINT` 空间剩余部分保留给 custom `HINT`：该子空间中永远不会定义 standard `HINT`。

> 目前尚未定义 standard hint。我们预期 standard hint 最终会包括 memory-system spatial and temporal locality hint、branch prediction hint、thread-scheduling hint、security tag，以及用于 simulation/emulation 的 instrumentation flag。

| Instruction | Constraints | Code Points | Purpose |
|---|---|---:|---|
| `LUI` | `rd=x0` | `2^20` | Reserved for future standard use |
| `AUIPC` | `rd=x0` | `2^20` | Reserved for future standard use |
| `ADDI` | `rd=x0`，且 `rs1!=x0` 或 `imm!=0` | `2^17 - 1` | Reserved for future standard use |
| `ANDI` | `rd=x0` | `2^17` | Reserved for future standard use |
| `ORI` | `rd=x0` | `2^17` | Reserved for future standard use |
| `XORI` | `rd=x0` | `2^17` | Reserved for future standard use |
| `ADD` | `rd=x0` | `2^10` | Reserved for future standard use |
| `SUB` | `rd=x0` | `2^10` | Reserved for future standard use |
| `AND` | `rd=x0` | `2^10` | Reserved for future standard use |
| `OR` | `rd=x0` | `2^10` | Reserved for future standard use |
| `XOR` | `rd=x0` | `2^10` | Reserved for future standard use |
| `SLL` | `rd=x0` | `2^10` | Reserved for future standard use |
| `SRL` | `rd=x0` | `2^10` | Reserved for future standard use |
| `SRA` | `rd=x0` | `2^10` | Reserved for future standard use |
| `FENCE` | `pred=0` 或 `succ=0` | `2^5 - 1` | Reserved for future standard use |
| `SLTI` | `rd=x0` | `2^17` | Reserved for custom use |
| `SLTIU` | `rd=x0` | `2^17` | Reserved for custom use |
| `SLLI` | `rd=x0` | `2^10` | Reserved for custom use |
| `SRLI` | `rd=x0` | `2^10` | Reserved for custom use |
| `SRAI` | `rd=x0` | `2^10` | Reserved for custom use |
| `SLT` | `rd=x0` | `2^10` | Reserved for custom use |
| `SLTU` | `rd=x0` | `2^10` | Reserved for custom use |

表 2.3：RV32I `HINT` 指令。
