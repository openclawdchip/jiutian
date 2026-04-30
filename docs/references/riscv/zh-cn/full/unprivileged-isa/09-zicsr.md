# 第 9 章 `Zicsr`，Control and Status Register（CSR）指令，版本 2.0

RISC-V 为每个 hart 定义了一个独立的地址空间，其中包含 4096 个 Control and Status register。本章定义对这些 CSR 进行操作的完整 CSR 指令集合。

虽然 CSR 主要由 privileged architecture 使用，但在 unprivileged code 中也有若干用途，包括 counters 和 timers，以及 floating-point status。

> counters 和 timers 不再被视为 standard base ISA 的 mandatory part，因此访问它们所需的 CSR 指令已经从 base ISA 章节移入本独立章节。

## 9.1 CSR 指令

所有 CSR 指令都对单个 CSR 执行 atomic read-modify-write；CSR specifier 编码在指令 bits 31-20 的 12-bit `csr` 字段中。immediate 形式使用一个 5-bit zero-extended immediate，该 immediate 编码在 `rs1` 字段中。

```text
31   20 19 15 14 12 11 7 6 0
csr     rs1   funct3 rd   opcode
12      5     3      5    7

source/dest source     CSRRW  dest SYSTEM
source/dest source     CSRRS  dest SYSTEM
source/dest source     CSRRC  dest SYSTEM
source/dest uimm[4:0]  CSRRWI dest SYSTEM
source/dest uimm[4:0]  CSRRSI dest SYSTEM
source/dest uimm[4:0]  CSRRCI dest SYSTEM
```

`CSRRW`（Atomic Read/Write CSR）指令在 CSR 和 integer register 之间原子地交换值。`CSRRW` 读取 CSR 的旧值，把该值 zero-extend 到 XLEN bit，然后写入 integer register `rd`。`rs1` 中的初始值被写入 CSR。如果 `rd=x0`，则该指令不应读取 CSR，也不应导致 CSR read 上可能发生的任何 side effect。

| Operand 类型 | Instruction | `rd` | `rs1` / `uimm` | read CSR? | write CSR? |
|---|---|---|---|---|---|
| Register operand | `CSRRW` | `x0` | - | no | yes |
| Register operand | `CSRRW` | `!x0` | - | yes | yes |
| Register operand | `CSRRS/C` | - | `x0` | yes | no |
| Register operand | `CSRRS/C` | - | `!x0` | yes | yes |
| Immediate operand | `CSRRWI` | `x0` | - | no | yes |
| Immediate operand | `CSRRWI` | `!x0` | - | yes | yes |
| Immediate operand | `CSRRS/CI` | - | `0` | yes | no |
| Immediate operand | `CSRRS/CI` | - | `!0` | yes | yes |

表 9.1：显示 CSR 指令是否读取或写入给定 CSR 的表。`CSRRS` 和 `CSRRC` 指令具有相同行为，因此表中显示为 `CSRRS/C`。

`CSRRS`（Atomic Read and Set Bits in CSR）指令读取 CSR 的值，把该值 zero-extend 到 XLEN bit，并写入 integer register `rd`。integer register `rs1` 中的初始值被视为 bit mask，指定要在 CSR 中置位的 bit position。`rs1` 中任何为 high 的 bit 都会使 CSR 中对应 bit 被置位，前提是该 CSR bit 可写。CSR 中其他 bit 不受影响（不过 CSR 在被写入时可能具有 side effect）。

`CSRRC`（Atomic Read and Clear Bits in CSR）指令读取 CSR 的值，把该值 zero-extend 到 XLEN bit，并写入 integer register `rd`。integer register `rs1` 中的初始值被视为 bit mask，指定要在 CSR 中清除的 bit position。`rs1` 中任何为 high 的 bit 都会使 CSR 中对应 bit 被清除，前提是该 CSR bit 可写。CSR 中其他 bit 不受影响。

对于 `CSRRS` 和 `CSRRC`，如果 `rs1=x0`，则该指令完全不会写 CSR，因此不应导致 CSR write 上本来可能发生的任何 side effect，例如访问 read-only CSR 时引发 illegal instruction exception。`CSRRS` 和 `CSRRC` 总是读取被寻址 CSR，并且无论 `rs1` 和 `rd` 字段如何，都会导致任何 read side effect。注意，如果 `rs1` 指定的寄存器不是 `x0`，但该寄存器保存的值为零，该指令仍会尝试把未修改的值写回 CSR，并导致任何伴随 side effect。`rs1=x0` 的 `CSRRW` 会尝试向 destination CSR 写入零。

`CSRRWI`、`CSRRSI` 和 `CSRRCI` 变体分别类似于 `CSRRW`、`CSRRS` 和 `CSRRC`。区别在于，它们使用一个 XLEN-bit 值更新 CSR；该值通过 zero-extend 编码在 `rs1` 字段中的 5-bit unsigned immediate（`uimm[4:0]`）得到，而不是来自 integer register。对于 `CSRRSI` 和 `CSRRCI`，如果 `uimm[4:0]` 字段为零，则这些指令不会写 CSR，也不应导致 CSR write 上本来可能发生的任何 side effect。对于 `CSRRWI`，如果 `rd=x0`，则该指令不应读取 CSR，也不应导致 CSR read 上可能发生的任何 side effect。`CSRRSI` 和 `CSRRCI` 总是读取 CSR，并且无论 `rd` 和 `rs1` 字段如何，都会导致任何 read side effect。

表 9.1 汇总了 CSR 指令在是否读取和/或写入 CSR 方面的行为。

> 到目前为止定义的 CSR，在读取时除了在不允许访问的情况下引发 illegal instruction exception 之外，没有任何 architectural side effect。Custom extension 可能增加在读取时具有 side effect 的 CSR。

某些 CSR，例如 instructions-retired counter `instret`，可能作为指令执行的 side effect 被修改。在这些情况下，如果 CSR access instruction 读取 CSR，它读取的是该指令执行之前的值。如果 CSR access instruction 写入这样的 CSR，则该写入代替 increment。特别地，一条指令写入 `instret` 的值，会成为下一条指令读到的值。

读取 CSR 的 assembler pseudoinstruction `CSRR rd, csr` 编码为：

```asm
CSRRS rd, csr, x0
```

写入 CSR 的 assembler pseudoinstruction `CSRW csr, rs1` 编码为：

```asm
CSRRW x0, csr, rs1
```

而 `CSRWI csr, uimm` 编码为：

```asm
CSRRWI x0, csr, uimm
```

当不需要旧值时，还定义了进一步的 assembler pseudoinstruction，用于设置和清除 CSR 中的 bit：

```asm
CSRS/CSRC   csr, rs1
CSRSI/CSRCI csr, uimm
```

### CSR Access Ordering

在给定 hart 上，explicit 和 implicit CSR access 相对于那些执行行为受所访问 CSR 状态影响的指令，按 program order 执行。特别地，CSR access 在 program order 中任何更早的、其行为会修改或受 CSR state 修改的指令执行之后执行，并在 program order 中任何更晚的、其行为会修改或受 CSR state 修改的指令执行之前执行。此外，CSR read access instruction 返回该指令执行之前被访问的 CSR state，而 CSR write access instruction 在该指令执行之后更新被访问的 CSR state。

当上述 program order 不成立时，CSR access 是 weakly ordered 的，本地 hart 或其他 hart 可能观察到 CSR access 的顺序不同于 program order。此外，CSR access 相对于 explicit memory access 不排序，除非 CSR access 修改执行 explicit memory access 的指令的执行行为，或者 CSR access 与 explicit memory access 通过 memory model 定义的 syntactic dependency 或本手册第二卷 Memory-Ordering PMAs 小节定义的 ordering requirement 排序。若要在所有其他情况下强制 ordering，软件应在相关 access 之间执行 `FENCE` 指令。就 `FENCE` 指令而言，CSR read access 分类为 device input（`I`），CSR write access 分类为 device output（`O`）。

非正式地说，CSR space 的行为类似于本手册第二卷 Memory-Ordering PMAs 小节定义的 weakly ordered memory-mapped I/O region。因此，CSR access 相对于所有其他 access 的顺序，受约束此类 region 的 memory-mapped I/O access 顺序的同样机制约束。

> 这些 CSR-ordering constraint 主要是为了支持将 main memory 和 memory-mapped I/O access 相对于 `time` CSR 的读取进行排序。除了 `time`、`cycle` 和 `mcycle` CSR 之外，到目前为止在本规范第一卷和第二卷中定义的 CSR 不能由其他 hart 或 device 直接访问，也不会导致对其他 hart 或 device 可见的 side effect。因此，对上述三个 CSR 之外 CSR 的访问，可以相对于 `FENCE` 指令自由重排序，而不违反本规范。

对于会导致 side effect 的 CSR access，上述 ordering constraint 适用于这些 side effect 的发起顺序，但不一定适用于这些 side effect 的完成顺序。

hardware platform 可以定义对某些 CSR 的访问是 strongly ordered，含义如本手册第二卷 Memory-Ordering PMAs 小节所定义。对 strongly ordered CSR 的访问，相对于对 weakly ordered CSR 的访问以及对 memory-mapped I/O region 的访问，都具有更强的 ordering constraint。
