# 1. Introduction

本文档是 RISC-V vector extension 的 1.0 版本，用于公开评审。

> Note：此 1.0 版本作为 RISC-V International 批准流程的一部分，被认为是公开评审冻结版本。1.0 版本被认为已经足够稳定，可以开始开发工具链、功能模拟器和实现，包括上游软件项目中的实现；除非在批准过程中发现严重问题，否则预期不会发生不兼容变更。一旦批准，规范将被赋予 2.0 版本号。

本规范包含当前已经冻结的完整 vector 指令集合。开发过程中曾经考虑、但未出现在本文档中的其他指令，不包含在本次评审和批准流程中，并且可能被完全修订或放弃。第 18 章 Standard Vector Extensions 列出了标准 vector 扩展，以及每个扩展支持哪些指令和元素宽度。

# 2. Implementation-defined Constant Parameters

每个支持 vector extension 的 hart 定义两个参数：

1. 任意操作可以产生或消费的 vector 元素最大位数，`ELEN >= 8`，并且必须是 2 的幂。
2. 单个 vector register 的位数，`VLEN >= ELEN`，必须是 2 的幂，并且不得大于 `2^16`。

标准 vector 扩展和 architecture profile 可以对 `ELEN` 与 `VLEN` 施加进一步约束。

> Note：未来扩展可以允许 `ELEN > VLEN`，方法是用多个 vector register 中的位保存一个元素；但当前提案不包含此选项。

> Note：`VLEN` 的上限使软件能够知道索引可装入 16 bit。最大 `VLMAX` 为 65,536，发生在 `LMUL=8`、`SEW=8`、`VLEN=65,536` 时。任何未来超过每个 vector register 64 Kib 的扩展，都需要新的配置指令，使使用旧配置指令的软件不会看到更大的 vector length。

vector extension 支持编写二进制代码，使其在满足若干约束时可以在 `VLEN` 参数不同的 hart 上可移植执行，前提是这些 hart 支持所需元素类型和指令。

> Note：可以编写暴露实现参数差异的代码。

> Note：通常，带有活动 vector 状态的线程上下文不能在执行期间迁移到 `VLEN` 或 `ELEN` 参数不同的 hart。

# 3. Vector Extension Programmer's Model

vector extension 在基础标量 RISC-V ISA 上增加 32 个 vector register，以及 7 个非特权 CSR：`vstart`、`vxsat`、`vxrm`、`vcsr`、`vtype`、`vl`、`vlenb`。

表 1. 新增 vector CSR

| Address | Privilege | Name | Description |
|---|---|---|---|
| `0x008` | `URW` | `vstart` | Vector start position |
| `0x009` | `URW` | `vxsat` | Fixed-Point Saturate Flag |
| `0x00A` | `URW` | `vxrm` | Fixed-Point Rounding Mode |
| `0x00F` | `URW` | `vcsr` | Vector control and status register |
| `0xC20` | `URO` | `vl` | Vector length |
| `0xC21` | `URO` | `vtype` | Vector data type register |
| `0xC22` | `URO` | `vlenb` | `VLEN/8`，vector register 的字节长度 |

> Note：4 个 CSR 编号 `0x00B`-`0x00E` 暂时保留给未来 vector CSR，其中一些可能会镜像到 `vcsr`。

## 3.1. Vector Registers

vector extension 在基础标量 RISC-V ISA 上增加 32 个架构 vector register，`v0`-`v31`。每个 vector register 有固定的 `VLEN` bit 状态。

## 3.2. Vector Context Status in `mstatus`

vector context status 字段 `VS` 被加入 `mstatus[10:9]`，并在 `sstatus[10:9]` 中提供影子副本。它的定义类似 floating-point context status 字段 `FS`。

当 `mstatus.VS` 设为 Off 时，试图执行任何 vector 指令，或访问 vector CSR，都会引发 illegal-instruction exception。

当 `mstatus.VS` 设为 Initial 或 Clean 时，执行任何改变 vector 状态的指令，包括改变 vector CSR 的指令，都会把 `mstatus.VS` 改为 Dirty。实现也可以在任何时间把 `mstatus.VS` 从 Initial 或 Clean 改为 Dirty，即使 vector 状态没有改变。

> Note：精确设置 `mstatus.VS` 是一种优化。软件通常使用 `VS` 减少上下文切换开销。

如果 `mstatus.VS` 为 Dirty，则 `mstatus.SD` 为 1；否则 `mstatus.SD` 按既有规范设置。实现可以有可写的 `misa.V` 字段。类似浮点单元的处理方式，即使 `misa.V` 清零，`mstatus.VS` 字段也可以存在。

> Note：允许在 `misa.V` 清零时仍存在 `mstatus.VS`，可支持 vector 仿真，并简化具有可写 `misa.V` 的系统中对 `mstatus.VS` 的处理。

## 3.3. Vector Context Status in `vsstatus`

当存在 hypervisor extension 时，vector context status 字段 `VS` 被加入 `vsstatus[10:9]`。它的定义类似 floating-point context status 字段 `FS`。

当 `V=1` 时，`vsstatus.VS` 和 `mstatus.VS` 同时生效：若任一字段设为 Off，则试图执行任何 vector 指令或访问 vector CSR 都会引发 illegal-instruction exception。

当 `V=1` 且 `vsstatus.VS` 与 `mstatus.VS` 均未设为 Off 时，执行任何改变 vector 状态的指令，包括 vector CSR，都会把 `mstatus.VS` 与 `vsstatus.VS` 都改为 Dirty。实现也可以在任何时间把 `mstatus.VS` 或 `vsstatus.VS` 从 Initial 或 Clean 改为 Dirty，即使 vector 状态没有改变。

如果 `vsstatus.VS` 为 Dirty，则 `vsstatus.SD` 为 1；否则 `vsstatus.SD` 按既有规范设置。如果 `mstatus.VS` 为 Dirty，则 `mstatus.SD` 为 1；否则 `mstatus.SD` 按既有规范设置。对于具有可写 `misa.V` 字段的实现，即使 `misa.V` 清零，`vsstatus.VS` 字段也可以存在。

## 3.4. Vector type register, `vtype`

只读、XLEN 宽的 vector type CSR `vtype` 提供解释 vector register file 内容所使用的默认类型，并且只能由 `vset{i}vl{i}` 指令更新。vector type 决定每个 vector register 中元素的组织方式，以及多个 vector register 如何分组。`vtype` 还指示 vector 结果中被 mask 关闭的元素，以及当前 vector length 之后的元素应如何处理。

> Note：只允许通过 `vset{i}vl{i}` 指令更新，可以简化 `vtype` register 状态维护。

`vtype` register 有 5 个字段：`vill`、`vma`、`vta`、`vsew[2:0]`、`vlmul[2:0]`。`vtype[XLEN-2:8]` 应写为 0；该字段中的非零值被保留。

表 2. `vtype` register 布局

| Bits | Name | Description |
|---|---|---|
| `XLEN-1` | `vill` | 若置位，表示 illegal value |
| `XLEN-2:8` | `0` | 非零时保留 |
| `7` | `vma` | Vector mask agnostic |
| `6` | `vta` | Vector tail agnostic |
| `5:3` | `vsew[2:0]` | Selected element width (`SEW`) setting |
| `2:0` | `vlmul[2:0]` | Vector register group multiplier (`LMUL`) setting |

> Note：图示布局针对 RV32 系统；一般情况下，`vill` 应位于 bit `XLEN-1`。

> Note：支持 `ELEN=32` 的小实现只需要 `vtype` 中 7 bit 状态：`ma` 与 `ta` 2 bit、`vsew[1:0]` 2 bit、`vlmul[2:0]` 3 bit。由 `vill` 表示的 illegal value 可在内部用 `vsew[1:0]` 中非法的 64 bit 组合编码，而不需要额外存储位保存 `vill`。

> Note：进一步的标准和自定义 vector 扩展可以扩展这些字段，以支持更丰富的数据类型。

> Note：`vtype` CSR 的主要动机，是让 vector 指令集能够装入 32 bit 指令编码空间。独立的 `vset{i}vl{i}` 指令可在执行 vector 指令之前设置 `vl` 和/或 `vtype` 字段，实现可以选择把这两条指令融合成一个内部 vector microop。在许多情况下，`vl` 与 `vtype` 值可被多条指令复用，从而减少 `vset{i}vl{i}` 指令的静态和动态指令开销。预期未来扩展的 64 bit 指令编码可允许这些字段静态指定在指令编码中。

### 3.4.1. Vector selected element width `vsew[2:0]`

`vsew` 中的值设置动态 selected element width (`SEW`)。默认情况下，一个 vector register 被看作划分为 `VLEN/SEW` 个元素。

表 3. `vsew[2:0]` 编码

| `vsew[2:0]` | `SEW` |
|---|---|
| `000` | 8 |
| `001` | 16 |
| `010` | 32 |
| `011` | 64 |
| `1XX` | Reserved |

> Note：虽然预期较大的 `vsew[2:0]` 编码 `100`-`111` 会用于编码更大的 `SEW`，但这些编码当前形式上保留。

表 4. 示例：`VLEN = 128` bit

| `SEW` | 每个 vector register 的元素数 |
|---|---|
| 64 | 2 |
| 32 | 4 |
| 16 | 8 |
| 8 | 16 |

支持的元素宽度可以随 `LMUL` 改变。

> Note：当前标准 vector 扩展集合不会使支持的元素宽度随 `LMUL` 改变。某些未来扩展可以只在用 `LMUL` 合并多个 vector register 的位时支持更大的 `SEW`。在这种情况下，依赖大 `SEW` 的软件应尝试使用最大的 `LMUL`，也就是最少的 vector register group，以提高代码可运行实现的数量。设置 `vtype` 后应检查 `vtype` 中的 `vill` 位，确认配置是否受支持；若不支持，应提供替代代码路径。或者，profile 可以规定每个 `LMUL` 设置下的最小 `SEW`。

### 3.4.2. Vector Register Grouping (`vlmul[2:0]`)

多个 vector register 可以分组，使单条 vector 指令可操作多个 vector register。本文用 vector register group 一词指一个或多个作为一条 vector 指令的单个操作数使用的 vector register。vector register group 可为更长应用 vector 提供更高执行效率，但引入它们的主要原因，是允许 double-width 或更宽元素以与 single-width 元素相同的 vector length 被操作。当 vector length multiplier `LMUL` 大于 1 时，它表示默认合并形成一个 vector register group 的 vector register 数量。实现必须支持 `LMUL` 的整数值 1、2、4、8。

> Note：vector 架构包含一些指令，它们具有元素宽度不同、但元素数量相同的多个源和目的 vector 操作数。每个 vector 操作数的 effective LMUL (`EMUL`) 由保存这些元素所需的寄存器数量决定。例如，widening add 操作把 32 bit 值相加以产生 64 bit 结果时，double-width 结果需要 single-width 输入两倍的 `LMUL`。

`LMUL` 也可以是分数值，从而减少单个 vector register 中使用的 bit 数。fractional `LMUL` 用于在混合宽度值上操作时增加有效可用 vector register group 的数量。

> Note：若只有整数 `LMUL` 值，一个在多种大小上操作的循环必须为最窄数据类型分配至少一个完整 vector register (`LMUL=1`)，随后为每个更宽的 vector 操作数消耗多个 vector register (`LMUL>1`) 形成 vector register group。这会限制可用 vector register group 的数量。使用 fractional `LMUL` 时，最宽值只需占用单个 vector register，而更窄值可占用单个 vector register 的一部分，从而即使处理混合宽度值，也允许全部 32 个架构 vector register 名称用于 vector 循环中的不同值。fractional `LMUL` 意味着 vector register 的一部分未被使用，但在某些情况下，拥有更多较短的驻留寄存器 vector，比拥有更少较长的驻留寄存器 vector 更高效。

实现必须提供 fractional `LMUL` 设置，使最窄受支持类型能够占用一个 vector register 的某个分数，该分数对应最窄受支持类型宽度与最大受支持类型宽度之比。一般要求是支持 `LMUL >= SEWMIN/ELEN`，其中 `SEWMIN` 是最窄的受支持 `SEW` 值，`ELEN` 是最宽的受支持 `SEW` 值。在标准扩展中，`SEWMIN=8`。对于 `ELEN=32` 的标准 vector 扩展，必须支持 fractional `LMUL` 1/2 和 1/4。对于 `ELEN=64` 的标准 vector 扩展，必须支持 fractional `LMUL` 1/2、1/4 和 1/8。

> Note：当 `LMUL < SEWMIN/ELEN` 时，不能保证实现会在 fractional vector register 中有足够位来存放至少一个元素，因为 `VLEN=ELEN` 是合法实现选择。例如，当 `VLEN=ELEN=32` 且 `SEWMIN=8` 时，`LMUL=1/8` 只会在 vector register 中提供 4 bit 存储。

对于给定的受支持 fractional `LMUL` 设置，实现必须支持 `SEWMIN` 到 `LMUL * ELEN`（含两端）之间的 `SEW` 设置。

试图设置不受支持的 `SEW` 和 `LMUL` 组合会设置 `vtype` 中的 `vill` 位。使用 `LMUL < SEWMIN/ELEN` 的 `vtype` 编码被保留，但如果实现不支持这些配置，可以设置 `vill`。

> Note：要求所有实现在这种情况下都设置 `vill` 会禁止未来扩展对此情况进行定义。因此，为允许未来定义 `LMUL < SEWMIN/ELEN` 行为，本文把这种用法视为 reserved。

> Note：建议汇编器在 `vsetvli` 指令尝试写入 `LMUL < SEWMIN/ELEN` 时给出 warning，而不是 error。

`LMUL` 由 `vtype` 中的有符号 `vlmul` 字段设置，即 `LMUL = 2^vlmul[2:0]`。派生值 `VLMAX = LMUL * VLEN / SEW` 表示在当前 `SEW` 与 `LMUL` 设置下，单条 vector 指令可操作的最大元素数。

| `vlmul[2:0]` | `LMUL` | `#groups` | `VLMAX` | 与 register `n` 分组的寄存器 |
|---|---:|---:|---|---|
| `100` | reserved | - | - | - |
| `101` | 1/8 | 32 | `VLEN/SEW/8` | `v n` |
| `110` | 1/4 | 32 | `VLEN/SEW/4` | `v n` |
| `111` | 1/2 | 32 | `VLEN/SEW/2` | `v n` |
| `000` | 1 | 32 | `VLEN/SEW` | `v n` |
| `001` | 2 | 16 | `2*VLEN/SEW` | `v n`, `v n+1` |
| `010` | 4 | 8 | `4*VLEN/SEW` | `v n` ... `v n+3` |
| `011` | 8 | 4 | `8*VLEN/SEW` | `v n` ... `v n+7` |

当 `LMUL=2` 时，vector register group 包含 `v n` 与 `v n+1`，提供两倍 bit 数的 vector length。指定 `LMUL=2` vector register group 且使用奇数编号 vector register 的指令被保留。

当 `LMUL=4` 时，vector register group 包含 4 个 vector register；指定 `LMUL=4` vector register group 且使用非 4 的倍数寄存器编号的指令被保留。

当 `LMUL=8` 时，vector register group 包含 8 个 vector register；指定 `LMUL=8` vector register group 且使用非 8 的倍数寄存器编号的指令被保留。

无论 `LMUL` 如何，mask register 始终包含在单个 vector register 中。

### 3.4.3. Vector Tail Agnostic and Vector Mask Agnostic `vta` and `vma`

这两个 bit 分别修改 vector 指令执行期间 destination tail elements 与 destination inactive masked-off elements 的行为。tail 集合与 inactive 集合包含在 vector 操作期间不会接收新结果的元素位置，其定义见 5.4。

所有系统必须支持全部四种选项：

| `vta` | `vma` | Tail Elements | Inactive Elements |
|---|---|---|---|
| 0 | 0 | undisturbed | undisturbed |
| 0 | 1 | undisturbed | agnostic |
| 1 | 0 | agnostic | undisturbed |
| 1 | 1 | agnostic | agnostic |

mask destination tail elements 始终按 tail-agnostic 处理，不受 `vta` 设置影响。

当某个集合标记为 undisturbed 时，vector register group 中对应的 destination elements 保持先前值。当某个集合标记为 agnostic 时，任一 vector destination operand 中对应的 destination elements 可以保持先前值，也可以被覆写为全 1。在单条 vector 指令内，每个 destination element 都可以任意组合地保持不变或覆写为全 1；当指令以相同输入执行时，该保持或覆写模式不要求确定性。

> Note：agnostic 策略被加入是为了适配带 vector register renaming 的机器。若采用 undisturbed 策略，必须从旧物理 destination vector register 读取全部元素，再复制到新的物理 destination vector register。当后续计算不需要这些 inactive 或 tail 值时，这会造成低效。

> Note：选择全 1 而不是全 0 作为覆写值，是为了阻止软件开发者依赖写入值。

> Note：简单的 in-order 实现可以忽略这些设置，并简单地用 undisturbed 策略执行所有 vector 指令。为兼容性和线程迁移支持，`vtype` 中仍必须提供 `vta` 与 `vma` 状态位。

> Note：out-of-order 实现可以选择用 tail-agnostic + mask-undisturbed 来实现 tail-agnostic + mask-agnostic，以降低实现复杂度。

> Note：agnostic 结果策略定义得较宽松，是为了适配应用线程在小型 in-order core（很可能保持 agnostic 区域不变）和带 register renaming 的大型 out-of-order core（很可能把 agnostic 元素覆写为 1）之间迁移。由于可能需要从中间重启，本文允许单条 vector 指令内任意混合 agnostic 策略。这种允许混合策略也支持按 vector register 不同粒度改变策略的实现，例如在正在被主动操作的 granule 内使用 undisturbed，但在 tail granule 上 rename 为全 1。

此外，除 mask load 指令外，mask 结果 tail 中的任何元素也可被写成 mask-producing 操作在 `vl=VLMAX` 时将计算出的值。进一步地，对于 mask-logical 指令以及 `vmsbf.m`、`vmsif.m`、`vmsof.m` mask-manipulation 指令，结果 tail 中的任何元素可被写为该 mask-producing 操作在 `vl=VLEN`、`SEW=8`、`LMUL=8` 时将计算出的值，也就是 mask register 的全部 bit 都可被覆写。

> Note：mask tail 始终按 agnostic 处理，以降低管理 bit 粒度 mask 数据的复杂度。软件似乎很少需要支持 mask register 值的 tail-undisturbed。允许 mask-generating 指令写回指令结果，可以避免为 tail 清零或屏蔽的逻辑；但 mask load 不能把内存值写入 destination mask tail，因为这将意味着访问超过软件意图的内存。

汇编语法给 `vsetvli` 指令增加两个强制 flag：

```asm
ta   # Tail agnostic
tu   # Tail undisturbed
ma   # Mask agnostic
mu   # Mask undisturbed

vsetvli t0, a0, e32, m4, ta, ma   # Tail agnostic, mask agnostic
vsetvli t0, a0, e32, m4, tu, ma   # Tail undisturbed, mask agnostic
vsetvli t0, a0, e32, m4, ta, mu   # Tail agnostic, mask undisturbed
vsetvli t0, a0, e32, m4, tu, mu   # Tail undisturbed, mask undisturbed
```

> Note：在 v0.9 之前，当 `vsetvli` 未指定这些 flag 时，它们默认是 mask-undisturbed/tail-undisturbed。不带这些 flag 的 `vsetvli` 用法已被弃用，并且现在必须指定 flag 设置。默认值也许本应是 tail-agnostic/mask-agnostic，使软件只在关心非参与元素时才显式指定；但考虑到引入这些 flag 前该指令的历史含义，最终决定未来汇编代码总是要求显式写出它们。

### 3.4.4. Vector Type Illegal `vill`

`vill` 位用于编码：先前的 `vset{i}vl{i}` 指令尝试向 `vtype` 写入不受支持的值。

> Note：`vill` 位位于 CSR 的 bit `XLEN-1`，以支持通过检查符号位分支来检测非法值。

在判断实现是否支持某个值时，必须考虑 `vtype` 参数的全部 bit。

> Note：必须检查全部 bit，以确保假设 `vtype` 中不受支持 vector 特性的新代码，在较旧实现上 trap，而不是错误执行。

`vill` 位置位的 `vtype` 值是不受支持的值。若 `vill` 位置位，则任何试图执行依赖 `vtype` 的 vector 指令都会引发 illegal-instruction exception。

> Note：`vset{i}vl{i}` 以及 whole-register loads、stores、moves 不依赖 `vtype`。

当 `vill` 位置位时，`vtype` 中其他 `XLEN-1` 个 bit 应为 0。

## 3.5. Vector Length Register `vl`

XLEN bit 宽的只读 `vl` CSR 只能由 `vset{i}vl{i}` 指令和 fault-only-first vector load 指令变体更新。

`vl` register 保存一个无符号整数，指定 vector 指令要用结果更新的元素数量，详见 5.4。

> Note：`vl` 中实现的 bit 数取决于实现对最小受支持类型的最大 vector length。最小 vector 实现若 `VLEN=32` 且支持 `SEW=8`，至少需要 `vl` 中 6 bit 来保存 0-32 的值，因为 `VLEN=32`、`LMUL=8`、`SEW=8` 得到 `VLMAX=32`。

## 3.6. Vector Byte Length `vlenb`

XLEN bit 宽的只读 CSR `vlenb` 保存 `VLEN/8`，即 vector register 的字节长度。

> Note：在任一实现中，`vlenb` 的值都是设计时常量。

> Note：若没有此 CSR，需要多条指令计算以字节为单位的 `VLEN`，且代码必须扰动当前 `vl` 和 `vtype` 设置，因此还要保存和恢复它们。

## 3.7. Vector Start Index CSR `vstart`

读写 CSR `vstart` 指定 vector 指令要执行的第一个元素的索引，详见 5.4。

通常，`vstart` 只由硬件在 vector 指令 trap 时写入；`vstart` 值表示发生 trap 的元素（同步异常或异步中断），也是可恢复 trap 处理完毕后执行应恢复的位置。

所有 vector 指令都定义为从 `vstart` CSR 给出的元素号开始执行，使 destination vector 中更早的元素保持不变，并在执行结束时把 `vstart` CSR 复位为 0。

> Note：所有 vector 指令，包括 `vset{i}vl{i}`，都会把 `vstart` CSR 复位为 0。

引发 illegal-instruction exception 的 vector 指令不会修改 `vstart`。

`vstart` CSR 定义为只有足以保存最大元素索引（最大 `VLMAX` 减 1）的可写 bit。

> Note：最大 vector length 用最大 `LMUL` 设置 8 和最小 `SEW` 设置 8 获得，因此 `VLMAX_max = 8*VLEN/8 = VLEN`。例如，`VLEN=256` 时，`vstart` 需要 8 bit 表示 0 到 255 的索引。

使用大于当前 `SEW` 设置下最大元素索引的 `vstart` 值被保留。

> Note：建议实现当 `vstart` 越界时 trap。规范不要求必须 trap，因为未来一种可能用途是在 `vstart` 高位中存储 imprecise trap 信息。

`vstart` CSR 可由非特权代码写入，但非零 `vstart` 值可能使某些实现上的 vector 指令显著变慢，所以应用程序员不应使用 `vstart`。少数 vector 指令不能在非零 `vstart` 值下执行，并将如下文所定义引发 illegal instruction exception。

> Note：让非特权代码可见 `vstart` 支持用户级线程库。

当试图用某个 `vstart` 值执行一条 vector 指令，而实现以相同 `vtype` 设置执行同一条指令时永远不会产生该 `vstart` 值，实现被允许引发 illegal instruction exception。

> Note：例如，某些实现永远不会在 vector arithmetic 指令执行期间响应中断，而是等待指令完成后再响应中断。这类实现被允许在 `vstart` 非零时试图执行 vector arithmetic 指令时引发 illegal instruction exception。

> Note：当软件线程在两种微架构不同的 hart 之间迁移时，新的 hart 微架构可能不支持该 `vstart` 值。接收 hart 上的 runtime 可能需要仿真指令执行，直到下一个受支持的 `vstart` 元素位置。或者，可约束迁移事件只发生在双方都支持的 `vstart` 位置。

## 3.8. Vector Fixed-Point Rounding Mode Register `vxrm`

vector fixed-point rounding-mode register 在最低有效 bit 中保存 2 bit 读写 rounding-mode 字段 `vxrm[1:0]`。高位 `vxrm[XLEN-1:2]` 应写为 0。

vector fixed-point rounding-mode 有独立 CSR 地址以允许独立访问，同时也作为 `vcsr` 中的字段反映。

> Note：可用单条 `csrwi` 指令在保存原 rounding mode 的同时设置新的 rounding mode。

fixed-point rounding 算法如下。假定舍入前结果为 `v`，其中 `d` bit 要被舍去。舍入后结果为 `(v >> d) + r`，其中 `r` 依 rounding mode 如下表所示。

表 5. `vxrm` 编码

| `vxrm[1:0]` | Abbreviation | Rounding Mode | Rounding increment, `r` |
|---|---|---|---|
| `00` | `rnu` | round-to-nearest-up，加 `+0.5 LSB` | `v[d-1]` |
| `01` | `rne` | round-to-nearest-even | `v[d-1] & (v[d-2:0] != 0 | v[d])` |
| `10` | `rdn` | round-down，truncate | `0` |
| `11` | `rod` | round-to-odd，把 bit OR 进 LSB，也称 "jam" | `!v[d] & v[d-1:0] != 0` |

舍入函数：

```text
roundoff_unsigned(v, d) = (unsigned(v) >> d) + r
roundoff_signed(v, d)   = (signed(v) >> d) + r
```

用于在后续指令描述中表示此操作。

## 3.9. Vector Fixed-Point Saturation Flag `vxsat`

`vxsat` CSR 有一个读写最低有效 bit `vxsat[0]`，指示 fixed-point 指令是否为了适配 destination format 而不得不饱和输出值。`vxsat[XLEN-1:1]` 应写为 0。

`vxsat` bit 镜像在 `vcsr` 中。

## 3.10. Vector Control and Status Register `vcsr`

独立的 `vxrm` 与 `vxsat` CSR 也可通过 vector control and status CSR `vcsr` 中的字段访问。

表 6. `vcsr` 布局

| Bits | Name | Description |
|---|---|---|
| `2:1` | `vxrm[1:0]` | Fixed-point rounding mode |
| `0` | `vxsat` | Fixed-point accrued saturation flag |

## 3.11. State of Vector Extension at Reset

vector extension 在 reset 时必须具有一致状态。特别地，`vtype` 与 `vl` 必须具有可被读取并随后由单条 `vsetvl` 指令恢复的值。

> Note：建议 reset 时设置 `vtype.vill`，`vtype` 中其余 bit 为 0，并把 `vl` 设为 0。

`vstart`、`vxrm`、`vxsat` CSR 在 reset 时可以具有任意值。

> Note：vector unit 的多数使用都需要初始 `vset{i}vl{i}`，它会复位 `vstart`。`vxrm` 与 `vxsat` 字段应由软件在使用前显式复位。

vector register 在 reset 时可以具有任意值。

# 4. Mapping of Vector Elements to Vector Register State

下列图示说明：在当前 `SEW` 和 `LMUL` 设置，以及实现 `VLEN` 下，不同宽度元素如何打包进 vector register 的字节。元素按 least-significant byte 位于最低编号 bit 的方式打包进每个 vector register。

该映射被选择来为软件提供最简单且最可移植的模型，但在某些操作上，对于较宽 vector datapath，它可能看起来会产生较大的布线成本。vector 指令集明确设计为支持这样的实现：实现可在内部为不同 `SEW` 重新排列 vector 数据以减少 datapath 布线成本，同时在外部保持简单的软件模型。

> Note：例如，微架构可跟踪写入 vector register 时使用的 `EEW`，然后在以不同 `EEW` 访问该寄存器时插入额外 scrambling 操作来重新排列数据。

## 4.1. Mapping for `LMUL = 1`

当 `LMUL=1` 时，元素简单地按顺序从 vector register 的 least-significant bit 到 most-significant bit 打包。

> Note：为提高可读性，vector register 布局图以从右到左的字节顺序绘制，字节地址递增。元素内 bit 以 little-endian 格式编号，bit 索引从右到左递增，对应数值权重递增。

## 4.2. Mapping for `LMUL < 1`

当 `LMUL` 为 fractional 时，一个 vector register 只使用其一部分来形成 vector register group。元素仍从所分配部分的最低编号 bit 开始、按递增元素索引连续打包。未属于该 fractional group 的 bit 不属于该操作数的架构元素集合。

fractional `LMUL` 的目标是在混合宽度循环中保留更多架构寄存器名；窄元素操作可用 `mf2`、`mf4`、`mf8` 等设置，使它们与较宽元素操作在同一循环中拥有相同元素数。

## 4.3. Mapping for `LMUL > 1`

当 `LMUL` 大于 1 时，一个 vector register group 由多个连续 vector register 组成。元素先填满组中最低编号 register，再继续填入下一个 register。寄存器组起始编号必须满足 `LMUL` 对齐要求：`LMUL=2` 时起始编号为偶数，`LMUL=4` 时为 4 的倍数，`LMUL=8` 时为 8 的倍数。

## 4.4. Mapping across Mixed-Width Operations

混合宽度操作使用 effective element width (`EEW`) 和 effective LMUL (`EMUL`) 来描述每个源或目的操作数实际占用的 register group 大小。拓宽操作的目的 `EMUL` 通常大于源 `LMUL`；缩窄操作的目的 `EMUL` 通常小于源 `LMUL`。所有操作数的元素数量保持由当前 `vl` 定义，尽管不同操作数每个元素的 bit 宽度不同。

对于 mixed-width 操作，指令编码和汇编器必须保证 register group 不越过 `v31`，满足对齐要求，并遵守允许或禁止重叠的规则。保留编码不应用于可移植程序。

## 4.5. Mask Register Layout

vector mask register 布局与 `SEW` 无关。mask 元素每个占 1 bit，元素 `i` 的 mask 位控制元素 `i`。mask 始终位于单个 vector register 中，通常为 `v0`，并且不因 `LMUL` 改变而扩展成 register group。

# 5. Vector Instruction Formats

vector 指令格式提供 vector-vector、vector-scalar、vector-immediate 和 mask 形式。常见字段包括 destination vector register group `vd`、source vector register group `vs1`/`vs2`、标量寄存器 `rs1`、immediate 字段和 mask 控制 bit `vm`。

## 5.1. Scalar Operands

整数操作的标量操作数可以来自 5 bit immediate `imm[4:0]`，也可以来自标量 `x` register `rs1`。若 `XLEN > SEW`，则使用 `x` register 的最低 `SEW` bit；若 `XLEN < SEW`，值按指令语义扩展。浮点操作的标量操作数来自标量 `f` register。若 `FLEN > SEW`，`f` register 中的值按当前元素格式解释；若 `FLEN < SEW`，则所需扩展由相关浮点扩展约束。

## 5.2. Vector Operands

vector 操作数由当前 `vtype` 和指令本身决定其 `SEW`、`LMUL`、`EEW`、`EMUL`。指令可以读取或写入一个或多个 vector register group。若 register group 起始编号不满足对齐要求，或者所需 group 超出 `v31`，指令编码被保留或产生 illegal-instruction exception，取决于规范对该情况的定义。

## 5.3. Vector Masking

多数 vector 指令带 `vm` bit。当 `vm=1` 时，指令不受 mask 影响；当 `vm=0` 时，`v0` 用作 mask register，只有 mask 位为 1 的元素成为 active element。汇编语法中通常以 `, v0.t` 后缀表示使用 `v0` true mask。

mask-off 的 inactive element 是否保持原值或变为 agnostic，由 `vtype.vma` 决定。未在当前 `vl` 内的 tail element 是否保持原值或变为 agnostic，由 `vtype.vta` 决定，但 mask destination tail 始终为 tail-agnostic。

## 5.4. Prestart, Active, Inactive, Body, and Tail Element Definitions

vector 指令执行期间，元素位置按如下集合定义：

| 集合 | 定义 |
|---|---|
| prestart | 元素索引小于 `vstart`；本次指令不执行这些元素，destination 保持不变。 |
| active | `vstart <= i < vl` 且 mask 允许该元素；这些元素执行指令语义并写入结果。 |
| inactive | `vstart <= i < vl` 但 mask 关闭；这些元素受 `vma` 策略约束。 |
| body | `vstart <= i < vl` 的全部元素，包括 active 与 inactive。 |
| tail | `i >= vl` 且小于当前 `VLMAX` 的元素；这些元素受 `vta` 策略约束。 |

若 `vstart >= vl`，则没有 body 元素被执行；指令仍在结束时将 `vstart` 复位为 0，除非发生不会修改 `vstart` 的异常情况。

# 6. Configuration-Setting Instructions (`vsetvli`/`vsetivli`/`vsetvl`)

配置指令设置 `vl` 与 `vtype`。它们使软件可用 stripmining 循环在未知 `VLEN` 的实现上运行。程序把 application vector length (`AVL`) 传给配置指令，硬件根据 `AVL`、当前或请求的 `vtype`、实现支持的 `VLEN/ELEN` 返回实际 `vl`。

典型形式：

```asm
vsetvli rd, rs1, vtypei
vsetivli rd, uimm, vtypei
vsetvl  rd, rs1, rs2
```

`vsetvli` 使用 `rs1` 提供 `AVL`，使用 immediate 编码请求 `vtype`；`vsetivli` 使用小 immediate 作为 `AVL`；`vsetvl` 从 `rs2` 获取完整 `vtype` 值，常用于保存/恢复 context。三者都把新 `vl` 写入 `rd`，并更新 `vl` 与 `vtype` CSR。若 `rd=x0`，返回值被丢弃。

## 6.1. `vtype` encoding

`vtype` immediate 编码包含 `vsew`、`vlmul`、`vta`、`vma`。汇编写法使用 `e8/e16/e32/e64` 表示 `SEW`，使用 `m1/m2/m4/m8/mf2/mf4/mf8` 表示 `LMUL`，并强制写出 `ta/tu` 与 `ma/mu` 策略。

若请求的 `SEW`、`LMUL`、tail/mask 策略或保留 bit 组合不受支持，实现设置 `vtype.vill=1`，并使 `vtype` 其他 bit 为 0。可移植软件应避免不受扩展保证的配置，或在设置后检查 `vill`。

## 6.2. `AVL` encoding

`AVL` 是应用希望本次处理的元素数量。`vsetvli` 从 `rs1` 读取，`vsetivli` 从 immediate 读取，`vsetvl` 从 `rs1` 读取。特殊寄存器组合用于表达常见模式，例如请求最大 vector length 或保持现有 `vl`。配置指令的目的寄存器 `rd` 接收结果 `vl`；当 `rd=x0` 时，不写回通用寄存器。

## 6.3. Constraints on Setting `vl`

配置指令必须按下列约束设置 `vl`：

1. 若 `AVL <= VLMAX`，则 `vl = AVL`。
2. 若 `AVL < 2 * VLMAX`，则 `ceil(AVL / 2) <= vl <= VLMAX`。
3. 若 `AVL >= 2 * VLMAX`，则 `vl = VLMAX`。
4. 对同一实现、相同 `AVL` 与 `VLMAX` 输入，结果必须确定。
5. 这些性质支持可移植 stripmining：第一个迭代不会处理超过剩余元素数量，循环最终完成所有元素，且在最后两次迭代中负载可以相对均衡。

> Note：允许实现对 `AVL` 在 `VLMAX` 与 `2*VLMAX` 之间的情况选择小于 `VLMAX` 的 `vl`，可帮助某些实现平衡最后两次迭代，减少很小尾迭代造成的开销。

## 6.4. Example of stripmining and changes to `SEW`

stripmining 循环通常如下：把剩余元素数传给 `vsetvli`，根据返回的 `vl` 执行一组 vector load/compute/store，随后用 `vl` 更新指针和计数，直到剩余数为 0。

当循环中需要改变 `SEW` 时，代码可保持 `SEW/LMUL` 比值不变，以在不同元素宽度之间维持相同 `VLMAX`。例如先用 `e8,m1` 计算 byte predicate，再用 `e32,m4` 处理 32 bit 数据，使 mask 与计算拥有相同元素数量。若改变 `SEW` 后不保持元素数量，软件必须小心更新 `vl` 与指针，避免 mask 和数据元素错位。
