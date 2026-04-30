# Chapter 3 Hart to encoder interface

## 3.1 Interface requirements

本节以一般术语描述必须从 RISC-V hart 传递到 trace encoder 的信息，并区分 mandatory 与 optional。

以下信息是 mandatory：

- 正在 retired 的指令数量。
- 是否发生了 exception 或 interrupt；如果发生，还包括 cause，来自 `ucause/scause/mcause` CSR，以及 trap value，来自 `utval/stval/mtval` CSR。
- RISC-V hart 当前 privilege level。
- 已 retired 指令的 `instruction_type`，针对：
  - target 无法从 source code 推断的 jump；
  - taken branch 和 nontaken branch；
  - 从 exception 或 interrupt 返回，即 `*ret` instructions。
- `instruction_address`，针对：
  - target 无法从 source code 推断的 jump；
  - target 无法从 source code 推断的 jump 之后立即 retired 的指令，也称为该 jump 的 target 或 destination；
  - taken branch 和 nontaken branch；
  - exception 或 interrupt 之前 retired 的最后一条指令；
  - exception 或 interrupt 之后 retired 的第一条指令；
  - privilege change 之前 retired 的最后一条指令；
  - privilege change 之后 retired 的第一条指令。

以下信息是 optional：

- Context information：
  - context 和/或 hart ID；
  - context changes 时要采取的 action 类型。
- 指令的 `instruction_type`，针对：
  - target 无法从 source code 推断的 call；
  - target 可从 source code 推断的 call；
  - target 无法从 source code 推断的 tail-call；
  - target 可从 source code 推断的 tail-call；
  - target 无法从 source code 推断的 return；
  - target 可从 source code 推断的 return；
  - co-routine swap；
  - 不属于上述分类且 target 无法从 source code 推断的 jump；
  - 不属于上述分类且 target 可从 source code 推断的 jump。
- 如果支持 context，则包括以下 `instruction_address`：
  - context change 之前 retired 的最后一条指令；
  - context change 之后 retired 的第一条指令。
- jump target 是否 sequentially inferable。

mandatory information 是实现 Chapter 6 中 branch trace algorithm 所需的最低限度信息。optional information 支持替代或改进的 trace algorithm：

- implicit return mode（见 2.2.5）要求 encoder 跟踪 nested function calls 的数量；为此，无论 target 是否可推断，encoder 都必须知道所有 call 和 return。
- 对 basic code profiling 有用的较简单 algorithm 只报告 function call 和 return，同样不考虑 target 是否可推断。
- branch prediction 技术可进一步提升 encoder efficiency，尤其是对 loop 而言，见 2.2.6。这要求 encoder 知道所有 branch 的地址，无论它们是否 taken。
- 如果 jump 以及之前把 target 加载到寄存器的指令都已被 traced，则 uninferable jump 可作为 inferable 处理，也就是不需要在 trace output 中报告。

### 3.1.1 Jump classification and target inference

Jump 被分类为 inferable 或 uninferable。inferable jump 具有可从 binary executable 或其表示形式（例如 ELF）推导的 target。就本规范而言，采用以下严格定义：

如果 jump 的 target 通过嵌入 jump opcode 的常量提供，则它被分类为 inferable。不是 inferable 的 jump 按定义就是 uninferable。

不过，有些 jump target 虽然按上述定义被分类为 uninferable，但仍可通过考虑成对指令从 binary executable 推导出来。具体来说，jump target 通过以下方式提供：

- `lui` 或 `c.lui`，即包含常量的寄存器；
- `auipc`，即包含相对于 PC 的常量偏移的寄存器。

如果这对指令连续 retired，也就是 `auipc`、`lui` 或 `c.lui` 紧挨着位于 jump 之前，则这类 jump target 被分类为 sequentially inferable。注意：要求指令连续 retired 是为了最小化 hart 与 encoder 之间所需的额外 signalling；预计连续执行会是常态，所以对 trace efficiency 的影响应很小。支持 sequentially inferable jump 是 optional。

Jump 可选地按照推荐 calling convention 进一步分类：

- Calls：
  - `jal x1`
  - `jal x5`
  - `jalr x1, rs`，其中 `rs != x5`
  - `jalr x5, rs`，其中 `rs != x1`
  - `c.jalr rs1`，其中 `rs1 != x5`
  - `c.jal`
- Tail-calls：
  - `jal x0`
  - `c.j`
  - `jalr x0, rs`，其中 `rs != x1` 且 `rs != x5`
  - `c.jr rs1`，其中 `rs1 != x1` 且 `rs1 != x5`
- Returns：
  - `jalr rd, rs`，其中 `(rs == x1 or rs == x5)` 且 `rd != x1` 且 `rd != x5`
  - `c.jr rs1`，其中 `rs1 == x1 or rs1 == x5`
- Co-routine swap：
  - `jalr x1, x5`
  - `jalr x5, x1`
  - `c.jalr x5`
- Other：
  - `jal rd`，其中 `rd != x1` 且 `rd != x5`
  - `jalr rd, rs`，其中 `rs != x1` 且 `rs != x5` 且 `rd != x0` 且 `rd != x1` 且 `rd != x5`

### 3.1.2 Relationship between RISC-V core and the encoder

encoder 旨在编码单个 hart 上执行的指令。

不过，RISC-V core 包含多个 harts 是常见的。core 可以通过几种不同方式支持这一点：

- 为每个 hart 实现单独的 interface instance。每个 instance 可连接到单独的 encoder instance，从而允许所有 harts 并发 trace。另一种方式是配合单个 encoder 使用外部 muxing，以便一次 trace 某一个特定 hart。
- 为 core 实现一个 single interface，并在 core 内部使用 muxing 选择要连接到 interface 的 hart。

虽然在技术上可以用单个 encoder 配合多个以 fine-grained multi-threaded configuration 运行的 harts，但 thread-switching 导致的频繁 context changes 会使 encoding efficiency 极差，因此不推荐这种配置。

## 3.2 Instruction interface

本节描述 RISC-V hart 与 trace encoder 之间的 interface，该 interface 传达上一节描述的信息。signal 被分配到以下 group 之一：

- M：Mandatory。interface 必须包含该 signal 的一个 instance。
- O：Optional。interface 可以包含该 signal 的一个 instance。
- MR：Mandatory, may be replicated。对于每个 clock cycle 最多可 retire N 个 taken branches 的 hart，interface 必须包含该 signal 的 N 个 instance。
- OR：Optional, may be replicated。对于每个 clock cycle 最多可 retire N 个 taken branches 的 hart，interface 必须包含该 signal 的 0 个或 N 个 instance。
- BR：Block, may be replicated。对于可在 block 中 retire multiple instructions 的 hart 为 mandatory。复制规则同 OR。如果省略，则 interface 必须包含 SR group signals。
- SR：Single, may be replicated。对于只能在 block 中 retire one instruction 的 hart 为 mandatory。复制规则同 OR，见 3.2.2。如果省略，则 interface 必须包含 BR group signals。

Table 3.1 和 Table 3.2 列出旨在高效支持每周期 retire multiple instructions 的 interface signals。以下讨论描述 multiple-retirement behavior。对于一次只能 retire one instruction 的 hart，signalling 可以简化；见 3.2.1。

block 中呈现的信息表示从 `iaddr` 开始的一段连续指令，这些指令都在同一 cycle retired。注意，如果 `itype` 为 1 或 2，表示 exception 或 interrupt，则 retired 指令数量可以为零。`cause` 和 `tval` 仅在 `itype` 为 1 或 2 时有定义。如果 `iretire=0` 且 `itype=0`，所有其他 signals 的值均 undefined。

`iretire` 包含该 block 中 retired instructions 所代表的 half-words 数量，`ilastsize` 包含最后一条指令的 size。使用 half-words 而不是 instruction count，使 encoder 无需访问 block 中每条指令的 size 就能容易地计算 block 中最后一条指令的地址。

`itype` 可为 3 或 4 bits 宽。如果 `itype_width_p` 为 3，则使用单个 code `6` 表示所有 uninferable jumps。这实现更简单，但排除了 implicit return mode 的使用，见 2.2.5；该 mode 要求 jump type 被完整分类。

虽然 `iaddr` 通常是 virtual address，但如果它是 physical address，也不影响 encoder behavior。

对于每个 clock cycle 最多可 retire N 个 branches 的 hart，signal groups MR、OR 以及 BR 或 SR 必须复制 N 次。signal group 0 表示最旧 instruction block 的信息，group N-1 表示最新 instruction block。interface 每个 cycle 支持不超过一个 privilege、context、exception 或 interrupt，因此 M 和 O group 中的 signals 不复制。此外，`itype` 只能在一个 signal group 中取值 1 或 2，而且该 group 必须是最新的 valid group，即更高编号 group 的 `iretire` 和 `itype` 必须为零。如果一个 cycle retire 的 branches 少于 N 个，必须先使用低编号 group。例如，如果有一个 branch，只使用 group 0；如果有两个 branches，则直到第 1 个 branch 的指令必须在 group 0 报告，直到第 2 个 branch 的指令必须在 group 1 报告，依此类推。

`sijump` 是 optional；如果 hart 未实现检测 sequentially inferable jumps 的逻辑，可以省略。如果 encoder 提供 `sijump` input，则它还必须提供一个 parameter，说明该 input 是连接到实现此 capability 的 hart，还是 tie off。这是为了确保 decoder 能知道 hart 的 capability。如果 hart 不支持该能力，却在 encoder 和 decoder 中启用 sequentially inferable jump mode，会阻止 decoder 正确重建。

`context` field 可用于向 decoder 传达任何附加信息。例如：

- software thread ID；
- operating system 的 process ID；
- 当 CSR 被写入时，通过把 `context` 设置为 CSR number 和 value，向 decoder 传达 CSR 值；
- 在 single encoder 被多个 harts 共享的情况下，见 3.1.2，如果 hart ID 可以动态改变，也可用于指示 hart ID。

### Table 3.1 Instruction interface signals

| Signal | Group | Function |
| --- | --- | --- |
| `itype[itype_width_p-1:0]` | MR | instruction block 的 termination type。codes 6-15 的定义见 3.1.1：`0` block 中最终指令不是其他命名 `itype` code；`1` Exception，block 中最终 retired instruction 后发生 traps 的 exception；`2` Interrupt，block 中最终 retired instruction 后发生 traps 的 interrupt；`3` exception 或 interrupt return；`4` nontaken branch；`5` taken branch；`6` 若 `itype_width_p` 为 3 则为 uninferable jump，否则 reserved；`7` reserved；`8` uninferable call；`9` inferable call；`10` uninferable tail-call；`11` inferable tail-call；`12` co-routine swap；`13` return；`14` other uninferable jump；`15` other inferable jump。 |
| `cause[ecause_width_p-1:0]` | M | Exception 或 interrupt cause（`ucause/scause/mcause`）。除非 `itype=1` 或 `2`，否则忽略。 |
| `tval[iaddress_width_p-1:0]` | M | 相关 trap value，例如 address exception 的 faulting virtual address，如将写入 `utval/stval/mtval` CSR。未来 optional extension 可定义 `tval`，以便在当前提供零的情况下提供 ancillary information。除非 `itype=1` 或 `2`，否则忽略。 |
| `priv[privilege_width_p-1:0]` | M | 本 cycle retired 的所有指令的 privilege level。 |
| `iaddr[iaddress_width_p-1:0]` | MR | 本 block retired 的第一条指令的地址。若 `iretire=0` 则 invalid。 |
| `context[context_width_p-1:0]` | O | 本 cycle retired 的所有指令的 context。 |
| `ctype[ctype_width_p-1:0]` | O | `context` 的 reporting behavior：`0` Don't report；`1` Report imprecisely；`2` Report precisely；`3` Report as asynchronous discontinuity。 |
| `sijump` | OR | 如果 `itype` 指示该 block 以 uninferable discontinuity 结束，将此 signal 置 1 表示它是 sequentially inferable，并且如果前面的 `auipc`、`lui` 或 `c.lui` 已被 traced，encoder 可将其作为 inferable 处理。对于 8、10、12、14 以外的 `itype` code 忽略。 |

### Table 3.2 Instruction interface signals - multiple retirement per block

| Signal | Group | Function |
| --- | --- | --- |
| `iretire[iretire_width_p-1:0]` | BR | 本 block 中 retired instructions 所代表的 halfwords 数量。 |
| `ilastsize[ilastsize_width_p-1:0]` | BR | 最后一条 retired instruction 的 size 是 `2^ilastsize` 个 half-words。 |

### Table 3.3 Instruction interface signals - single retirement per block

| Signal | Group | Function |
| --- | --- | --- |
| `iretire[0:0]` | SR | 本 block 中 retired 的指令数量，0 或 1。 |

Table 3.4 规定各种 `ctype` 值的 actions。典型行为是该 signal 除 context change 后第一次 retirement 外保持为零。`ctype_width_p` 可以为 1 或 2。缩减宽度选项只支持 imprecisely 报告 context changes。

### Table 3.4 Context type `ctype` values and corresponding actions

| Type | Value | Actions |
| --- | --- | --- |
| Unreported | 0 | 无 action，不报告 context。 |
| Report context imprecisely | 1 | 例如 SW thread 或 operating system process change。尽早在方便的时机报告新 context value。报告时不包含任何 address information，并假定 context change 的精确点可从 source code 推导，例如 CSR write。 |
| Report context precisely | 2 | 报告本 block 中 retired 的第一条指令的地址以及新 context。如果此前有未报告 branches，需要先报告这些 branches。其处理方式与 privilege change 相同。 |
| Report context as an asynchronous discontinuity | 3 | 例如 hart change。需要报告 previous context 上 retired 的最后一条指令，以及 new context 上的第一条指令。其处理方式与 exception 相同。 |

### 3.2.1 Simplifications for single-retirement

对于一次只能 retire one instruction 的 hart，interface 可简化为 Table 3.1 和 Table 3.3 中列出的 signals。简化如下：

- 因为 block 中 retired 的指令数量只有 0 或 1，encoder 不需要信息来推导最后一条 retired instruction 的地址；它与第一条也是唯一一条 retired instruction 相同。因此不需要 `ilastsize`，`iretire` 只表示是否有一条指令 retired。

parameter `retires_p` 向 encoder 指示每 cycle 可 retired 的最大指令数。能够支持 single 或 multiple retirement 的 encoder 可用它选择对 `iretire` 的相应解释。当连接到不提供这些 outputs 的 single-retirement hart 时，`ilastsize` encoder input 必须 tie low。

### 3.2.2 Alternative multiple-retirement interface configurations

对于每 cycle 可 retire multiple instructions 但不超过一个 branch 的 hart，首选方案是使用 BR、MR 和 OR groups 中 signals 的一个 instance。不过，如果 hart 可在一个 cycle retire N 个 branches，则必须使用 MR、OR 以及 SR 或 BR groups 中 signals 的 N 个 instance；每个 instance 可以是 single instruction 或 block。

如果 hart 可每 cycle retire N 条 instructions，但只有一个 branch，则允许但不推荐通过使用 SR、MR 和 OR groups 中 signals 的 N 个 instances，显式提供每条 retired instruction 的细节。

### 3.2.3 Optional sideband signals

可以包含 optional sideband signals 来提供附加功能，如 Table 3.5 和 Table 3.6 所述。

注意，任何需要 encoder 输出的 user defined information 都需要通过 `context` input 应用。

### Table 3.5 Optional sideband encoder input signals

| Signal | Group | Function |
| --- | --- | --- |
| `impdef[impdef_width_p-1:0]` | O | Implementation defined sideband signals。典型用途是 filtering，见 Chapter 4。 |
| `trigger[2:0]` | OR | bit 0 上的 pulse 会使 encoder 开始 tracing，并在另行通知前继续，前提是也满足其他 filtering criteria。bit 1 上的 pulse 会使 encoder 停止 tracing，直到另行通知；见 3.2.4。 |
| `halted` | O | Hart is halted。assertion 时，encoder 会输出一个 packet 来报告 halt 前 retired 的最后一条 instruction 的地址，随后输出 support packet 表示 tracing 已停止。deassertion 时，encoder 会再次开始 tracing，从 synchronization packet 开始。 |
| `reset` | O | Hart is in reset。只要 encoder 与 hart 位于不同 reset domain，该 signal 允许 encoder 指示进入 reset 时 tracing 结束，退出 reset 时 tracing 重新开始。行为同上面对 `halt` 的描述。 |

### Table 3.6 Optional sideband encoder output signals

| Signal | Group | Function |
| --- | --- | --- |
| `stall` | O | Stall request to hart。有些应用可能要求 lossless trace，可在 trace encoder 无法输出 trace packet 时使用该 signal stall hart，例如由于 packet transport infrastructure 的 back-pressure。 |

### 3.2.4 Using trigger outputs from the Debug Module

RISC-V hart 的 debug module 可以有 trigger unit。它定义 match control register（`mcontrol`），其中包含 4-bit `action` field，并保留该 field 的 codes 2-5 供 trace 使用。这些 action codes 在此按 Table 3.7 定义。如果实现，每个 action 都必须在导致 trigger 的指令 retired 的同一个 cycle，在 hart 的 output 上生成 pulse。

### Table 3.7 Debug Module trigger support (`mcontrolaction`)

| Value | Description |
| --- | --- |
| 2 | Trace-on。若 encoder 提供 `trigger[0]`，它应连接到该 input。 |
| 3 | Trace-off。若 encoder 提供 `trigger[1]`，它应连接到该 input。 |
| 4 | Trace-notify。若 encoder 提供 `trigger[2]`，它应连接到该 input。如果 encoder enabled，这会使 encoder 输出一个包含 block 中最后一条 instruction 地址的 packet。 |

Trace-on 和 Trace-off actions 提供一种让 hart 控制何时 tracing 发生的方法。Trace-notify 提供一种确保指定 instruction 被显式报告的方法。该能力有时称为 watchpoint。

### 3.2.5 Example retirement sequences

### Table 3.8 Example 1: 9 Instructions retired over four cycles, 2 branches

| Retired Instruction | Trace Block |
| --- | --- |
| `1000: divuw` | `iretire=7, iaddr=0x1000, itype=8` |
| `1004: add` |  |
| `1008: or` |  |
| `100C: c.jalr` |  |
| `0940: addi` | `iretire=3, iaddr=0x0940, itype=4` |
| `0944: c.beq` |  |
| `0946: c.bnez` | `iretire=1, iaddr=0x0946, itype=5` |
| `0988: lbu` | `iretire=4, iaddr=0x0988, itype=0` |
| `098C: csrrw` |  |
