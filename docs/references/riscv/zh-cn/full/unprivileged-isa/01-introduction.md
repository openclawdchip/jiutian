# 第 1 章 引言

RISC-V（读作“risk-five”）是一种新的 instruction-set architecture（ISA）。它最初设计用于支持计算机体系结构研究和教学，但我们现在也希望它成为工业实现的一种标准、自由且开放的体系结构。我们定义 RISC-V 的目标包括：

- 一个完全开放的 ISA，可供学术界和工业界自由使用。
- 一个真正适合直接原生硬件实现的 ISA，而不只是用于仿真或二进制翻译。
- 一个避免为特定微架构风格（例如 microcoded、in-order、decoupled、out-of-order）或实现技术（例如 full-custom、ASIC、FPGA）“过度架构化”的 ISA，同时允许在这些风格和技术中高效实现。
- 一个分为小型 base integer ISA 和可选 standard extension 的 ISA；base integer ISA 可单独用作定制加速器的基础或教学用途，standard extension 则支持通用软件开发。
- 支持修订后的 2008 IEEE-754 floating-point standard。
- 支持广泛 ISA extension 和专用变体。
- 同时提供面向应用、操作系统内核和硬件实现的 32 位与 64 位地址空间变体。
- 支持高度并行的 multicore 或 manycore 实现，包括 heterogeneous multiprocessor。
- 支持可选 variable-length instruction，既扩展可用的 instruction encoding space，也支持可选的高密度 instruction encoding，以改善性能、静态代码大小和能效。
- 一个完全可虚拟化的 ISA，以简化 hypervisor 开发。
- 一个简化新 privileged architecture 设计实验的 ISA。

> 设计决策的 commentary 会采用本段这样的格式。若读者只关心规范本身，可以跳过这些非规范性文字。

RISC-V 这个名称表示 UC Berkeley 的第五个主要 RISC ISA 设计：RISC-I、RISC-II、SOAR 和 SPUR 是前四个。我们也借用了罗马数字 “V” 的双关，表示 “variations” 和 “vectors”，因为支持各种体系结构研究，包括各种 data-parallel accelerator，是 ISA 设计的明确目标。

RISC-V ISA 的定义尽量避免实现细节（虽然会包含由实现驱动的设计决策 commentary）。它应被理解为多种实现的软件可见接口，而不是某个特定硬件制品的设计。RISC-V 手册分为两卷。本卷覆盖 base unprivileged instruction 的设计，包括可选 unprivileged ISA extension。Unprivileged instruction 是通常可在所有 privileged architecture 的所有 privilege mode 中使用的指令，尽管其行为可能随 privilege mode 和 privilege architecture 而变化。第二卷提供第一个（“classic”）privileged architecture 的设计。手册使用 IEC 80000-13:2008 约定，一个 byte 为 8 bit。

> 在 unprivileged ISA 设计中，我们试图去除对特定微架构特性（例如 cache line size）或 privileged architecture 细节（例如 page translation）的任何依赖。这样做既是为了简洁，也是为了给替代微架构或替代 privileged architecture 留出最大灵活性。

## 1.1 RISC-V 硬件平台术语

一个 RISC-V hardware platform 可以包含一个或多个 RISC-V-compatible processing core，也可以包含其他 non-RISC-V-compatible core、fixed-function accelerator、各种 physical memory structure、I/O device，以及允许这些组件相互通信的 interconnect structure。

若一个组件包含独立的 instruction fetch unit，则称该组件为 core。一个 RISC-V-compatible core 可以通过 multithreading 支持多个 RISC-V-compatible hardware thread，简称 hart。

一个 RISC-V core 可以具有额外的专用 instruction-set extension，或附加的 coprocessor。本文使用 coprocessor 一词表示附着在 RISC-V core 上、主要由 RISC-V instruction stream 排序控制的单元；它包含额外 architectural state 和 instruction-set extension，并且可能相对于主 RISC-V instruction stream 具有某种有限自主性。

本文使用 accelerator 一词表示 non-programmable fixed-function unit，或表示可以自主运行但面向特定任务专门化的 core。在 RISC-V 系统中，我们预期许多 programmable accelerator 会是基于 RISC-V 的 core，并带有专用 instruction-set extension 和/或定制 coprocessor。RISC-V accelerator 的一个重要类别是 I/O accelerator，它们把 I/O processing task 从主 application core 上卸载出去。

RISC-V hardware platform 的系统级组织可以从 single-core microcontroller，一直到由 shared-memory manycore server node 组成的数千节点集群。即使是小型 system-on-chip，也可能组织成 multicomputer 和/或 multiprocessor 的层次结构，以模块化开发工作，或在子系统之间提供安全隔离。

## 1.2 RISC-V 软件执行环境和 hart

RISC-V 程序的行为取决于它运行所在的 execution environment。RISC-V execution environment interface（EEI）定义程序初始状态、环境中 hart 的数量和类型（包括 hart 支持的 privilege mode）、memory 和 I/O region 的可访问性和属性、每个 hart 上所有合法指令的行为（也就是说，ISA 是 EEI 的一个组成部分），以及执行期间引发的任何 interrupt 或 exception（包括 environment call）的处理方式。EEI 的例子包括 Linux application binary interface（ABI）或 RISC-V supervisor binary interface（SBI）。

RISC-V execution environment 的实现可以是纯硬件、纯软件，或硬件与软件的组合。例如，可以用 opcode trap 和 software emulation 实现硬件中未提供的功能。execution environment implementation 的例子包括：

- “Bare metal” hardware platform，其中 hart 由物理 processor thread 直接实现，指令可完全访问 physical address space。硬件平台定义一个从 power-on reset 开始的 execution environment。
- RISC-V operating system，它通过把 user-level hart 复用到可用物理 processor thread，并通过 virtual memory 控制 memory 访问，来提供多个 user-level execution environment。
- RISC-V hypervisor，它为 guest operating system 提供多个 supervisor-level execution environment。
- RISC-V emulator，例如 Spike、QEMU 或 rv8；它们在底层 x86 系统上模拟 RISC-V hart，并可提供 user-level 或 supervisor-level execution environment。

裸硬件平台可以视为定义了一个 EEI，其中可访问的 hart、memory 和其他 device 构成该环境，初始状态是 power-on reset 时的状态。

一般来说，大多数软件设计为使用更抽象的硬件接口，因为更抽象的 EEI 在不同硬件平台之间提供更好的可移植性。EEI 通常相互分层，一个较高层 EEI 使用另一个较低层 EEI。

从运行在给定 execution environment 中的软件视角看，hart 是一种资源，它在该 execution environment 中自主地获取并执行 RISC-V 指令。在这个意义上，即使 hart 被 execution environment 时间复用到真实硬件上，它对环境内部的软件而言也表现得像 hardware thread resource。一些 EEI 支持创建和销毁额外 hart，例如通过 environment call fork 新 hart。

execution environment 负责保证其每个 hart 最终前向进展。对给定 hart 来说，当该 hart 正在使用一种明确等待事件的机制时，这项责任被暂停；例如本规范第二卷定义的 wait-for-interrupt 指令。若 hart 被终止，这项责任结束。以下事件构成 forward progress：

- 一条指令退休。
- 一个 trap，如第 1.6 节所定义。
- 由扩展定义为构成 forward progress 的任何其他事件。

> hart 一词是在 Lithe 工作中引入的，目的是提供一个术语来表示抽象 execution resource，而不是软件线程这一编程抽象。

> hardware thread（hart）和 software thread context 之间的重要区别在于：运行在 execution environment 内的软件并不负责促成其每个 hart 的进展；这属于外层 execution environment 的责任。因此，从 execution environment 内部软件的角度看，该环境的 hart 像 hardware thread 一样运行。

> execution environment implementation 可以把一组 guest hart 时间复用到数量更少的 host hart 上；这些 host hart 由它自己的 execution environment 提供。但它必须以使 guest hart 表现得像独立 hardware thread 的方式这样做。特别是，如果 guest hart 多于 host hart，execution environment 必须能够抢占 guest hart，并且不得无限期等待某个 guest hart 上的 guest software “yield” 对该 guest hart 的控制。

## 1.3 RISC-V ISA 概览

RISC-V ISA 被定义为一个 base integer ISA 加上 base ISA 的可选 extension；任何实现都必须包含 base integer ISA。base integer ISA 与早期 RISC processor 的 ISA 非常相似，但没有 branch delay slot，并支持可选 variable-length instruction encoding。base 被谨慎限制为最小指令集合；这个集合足以为 compiler、assembler、linker 和 operating system（配合额外 privileged operation）提供合理目标，因此为构建更定制化 processor ISA 提供了方便的 ISA 和软件 toolchain “skeleton”。

虽然称其为 RISC-V ISA 很方便，但 RISC-V 实际上是一组相关 ISA 的家族，目前有四种 base ISA。每个 base integer instruction set 由 integer register 宽度、相应 address space 大小，以及 integer register 数量表征。两个主要 base integer 变体是第 2 章和第 5 章描述的 RV32I 和 RV64I，分别提供 32 位和 64 位地址空间。本文用 XLEN 表示 integer register 的 bit 宽度（32 或 64）。第 4 章描述 RV32I base instruction set 的 RV32E 子集变体；它为支持小型 microcontroller 而增加，integer register 数量减半。第 6 章概述未来的 RV128I base integer instruction set 变体，它支持 flat 128-bit address space（`XLEN=128`）。base integer instruction set 对 signed integer value 使用 two's-complement 表示。

> 虽然较大型系统需要 64 位地址空间，但我们认为，在未来数十年中，32 位地址空间对许多 embedded 和 client device 仍然足够，并且为了降低 memory traffic 和 energy consumption 仍然有吸引力。此外，32 位地址空间也足以满足教学用途。未来可能最终需要更大的 flat 128-bit address space，因此我们确保 RISC-V ISA 框架能够容纳这一点。

RISC-V 的四种 base ISA 被视为不同的 base ISA。一个常见问题是，为什么不只有单个 ISA；特别是，为什么 RV32I 不是 RV64I 的严格子集？一些较早的 ISA 设计（SPARC、MIPS）在增加地址空间大小时采用 strict superset 策略，以支持在新的 64 位硬件上运行既有 32 位二进制。

> 显式分离 base ISA 的主要优点是，每个 base ISA 都可以针对自身需要优化，而不必支持其他 base ISA 所需的全部操作。例如，RV64I 可以省略只为了处理 RV32I 中较窄寄存器而需要的指令和 CSR。RV32I 变体可以使用否则会为更宽地址空间变体所需指令保留的编码空间。

> 不把该设计视为单一 ISA 的主要缺点，是它会使在一种 base ISA 上模拟另一种 base ISA（例如在 RV64I 上模拟 RV32I）所需硬件复杂化。不过，寻址差异和 illegal instruction trap 通常意味着即使有完整 superset 指令编码，硬件也仍然需要某种 mode switch；而不同 RISC-V base ISA 足够相似，支持多个版本的成本相对较低。虽然有人提出 strict superset 设计会允许 legacy 32-bit library 与 64-bit code 链接，但实践中即使编码兼容，由于 software calling convention 和 system-call interface 的差异，这也并不可行。

> RISC-V privileged architecture 在 `misa` 中提供字段，用于控制各级 unprivileged ISA，以支持在同一硬件上模拟不同 base ISA。我们注意到，较新的 SPARC 和 MIPS ISA 修订版已经弃用在 64 位系统上不经修改运行 32 位代码的支持。

一个相关问题是，为什么 RV32I 中的 32-bit add（`ADD`）和 RV64I 中的 32-bit add（`ADDW`）使用不同编码？也可以在 RV32I 中用 `ADDW` opcode 表示 32-bit add，并在 RV64I 中用 `ADDD` 表示 64-bit add，而不是当前设计：在 RV32I 中用同一 `ADD` opcode 表示 32-bit add，在 RV64I 中用同一 `ADD` opcode 表示 64-bit add，并用不同 opcode `ADDW` 表示 RV64I 中的 32-bit add。这也会更符合 `LW` opcode 在 RV32I 和 RV64I 中都表示 32-bit load 的做法。RISC-V ISA 最早版本确实有过这种替代设计的一个变体，但 RISC-V 设计在 2011 年 1 月改为当前选择。

> 我们关注的是在 64 位 ISA 中支持 32 位整数，而不是提供与 32 位 ISA 的兼容性。动机是消除这样一种不对称：RV32I 中并非所有 opcode 都具有 `*W` 后缀（例如有 `ADDW`，但没有 `ANDW`）。事后看来，这个理由也许并不充分；它源自同时设计两个 ISA，而不是后来把一个放在另一个之上，也源自我们当时认为必须把平台要求纳入 ISA 规范，从而会意味着 RV64I 中必须包含所有 RV32I 指令。现在改变编码已经太晚，但基于上文所述原因，这也几乎没有实际影响。

> 有人指出，我们可以把 `*W` 变体作为 RV32I 系统的扩展启用，以便在 RV64I 和未来某个 RV32 变体之间提供共同编码。

RISC-V 设计为支持广泛定制和专门化。每个 base integer ISA 都可以通过一个或多个可选 instruction-set extension 扩展。我们把每个 RISC-V instruction-set encoding space（以及 CSR 等相关 encoding space）划分为三个互不相交的类别：standard、reserved 和 custom。Standard encoding 由 Foundation 定义，并且不得与同一 base ISA 的其他 standard extension 冲突。Reserved encoding 当前未定义，但为未来 standard extension 保留。本文用 non-standard 描述不由 Foundation 定义的扩展。Custom encoding 永远不得用于 standard extension，并提供给 vendor-specific non-standard extension 使用。本文用 non-conforming 描述使用 standard 或 reserved encoding 的 non-standard extension（也就是说，custom extension 不是 non-conforming）。Instruction-set extension 通常共享，但可能根据 base ISA 提供略有不同的功能。第 26 章描述扩展 RISC-V ISA 的各种方式。我们也为 RISC-V base instruction 和 instruction-set extension 制定了命名约定，第 27 章有详细说明。

为了支持更通用的软件开发，规范定义了一组 standard extension，用于提供 integer multiply/divide、atomic operation，以及 single-precision 和 double-precision floating-point arithmetic。base integer ISA 命名为 “I”（根据 integer register 宽度加上 RV32 或 RV64 前缀），包含 integer computational instruction、integer load、integer store 和 control-flow instruction。standard integer multiplication and division extension 命名为 “M”，增加对 integer register 中保存的值执行乘除的指令。standard atomic instruction extension 记为 “A”，增加原子地读取、修改和写入 memory 的指令，用于 inter-processor synchronization。standard single-precision floating-point extension 记为 “F”，增加 floating-point register、single-precision computational instruction，以及 single-precision load 和 store。standard double-precision floating-point extension 记为 “D”，扩展 floating-point register，并增加 double-precision computational instruction、load 和 store。standard “C” compressed instruction extension 为常见指令提供更窄的 16-bit 形式。

> 除了 base integer ISA 和 standard GC extension 之外，我们认为，很少有一条新指令会给所有应用带来显著收益，尽管它可能对某个特定领域非常有益。随着能效问题迫使更大程度的专门化，我们认为简化 ISA 规范的必需部分非常重要。其他体系结构通常把自己的 ISA 当作单一实体，随着时间加入指令而变成新版本；而 RISC-V 将努力使 base 和每个 standard extension 随时间保持不变，并把新指令作为进一步的可选 extension 分层加入。例如，无论后续有任何扩展，base integer ISA 都将继续作为完全支持的 standalone ISA。

## 1.4 内存

RISC-V hart 对所有 memory access 都具有一个 byte-addressable address space，大小为 `2^XLEN` byte。一个 memory word 定义为 32 bit（4 byte）。相应地，halfword 为 16 bit（2 byte），doubleword 为 64 bit（8 byte），quadword 为 128 bit（16 byte）。memory address space 是环形的，因此地址 `2^XLEN - 1` 处的 byte 与地址 0 处的 byte 相邻。因此，硬件执行的 memory address computation 忽略 overflow，而是按模 `2^XLEN` 回绕。

execution environment 决定硬件资源如何映射到 hart 的 address space。hart address space 的不同地址范围可以：（1）为空；或（2）包含 main memory；或（3）包含一个或多个 I/O device。对 I/O device 的读写可能具有可见 side effect，但对 main memory 的访问不能有可见 side effect。虽然 execution environment 可以把 hart address space 中的所有内容都称为 I/O device，但通常预期其中某一部分会被指定为 main memory。

当 RISC-V platform 具有多个 hart 时，任意两个 hart 的 address space 可以完全相同、完全不同，也可以部分不同但共享某些资源；共享资源可以映射到相同地址范围，也可以映射到不同地址范围。

对于纯 “bare metal” 环境，所有 hart 可能看到同一个 address space，并完全通过 physical address 访问。然而，当 execution environment 包含使用 address translation 的 operating system 时，通常会给每个 hart 一个很大程度上或完全属于它自己的 virtual address space。

执行每条 RISC-V machine instruction 都会产生一次或多次 memory access，分为 implicit access 和 explicit access。对每条执行的指令，都会执行一次 implicit memory read（instruction fetch），以取得要执行的 encoded instruction。许多 RISC-V 指令除了 instruction fetch 外不再执行其他 memory access。特定 load 和 store 指令会在由指令确定的地址上执行一次 explicit memory read 或 write。execution environment 可以规定，除了 unprivileged ISA 记载的访问外，指令执行还会产生其他 implicit memory access（例如用于实现 address translation）。

execution environment 决定非空 address space 的哪些部分可供每类 memory access 访问。例如，可被 instruction fetch 隐式读取的位置集合，可能与可由 load instruction 显式读取的位置集合没有任何重叠；可由 store instruction 显式写入的位置集合，也可能只是可读取位置的一个子集。通常，如果一条指令试图访问不可访问地址处的 memory，就会为该指令引发 exception。address space 中的空位置永远不可访问。

除非另有规定，不引发 exception 且没有 side effect 的 implicit read 可以任意提前并推测性发生，甚至可以在机器能够证明该读取会被需要之前发生。例如，一个合法实现可以在最早机会尝试读取整个 main memory，缓存尽可能多的可取指（可执行）byte 以供后续 instruction fetch 使用，并且从此不再为了 instruction fetch 读取 main memory。若要保证某些 implicit read 只在对同一 memory location 的 write 之后排序，软件必须执行为此目的定义的特定 fence 或 cache-control 指令（例如第 3 章定义的 `FENCE.I` 指令）。

一个 hart 所做的 memory access（implicit 或 explicit）在另一个 hart 或任何其他能访问同一 memory 的 agent 看来，可能以不同顺序出现。不过，这种 perceived reordering 始终受适用 memory consistency model 约束。RISC-V 的默认 memory consistency model 是 RISC-V Weak Memory Ordering（RVWMO），在第 14 章和附录中定义。可选地，实现可以采用更强的 Total Store Ordering 模型，如第 23 章所定义。execution environment 也可以增加约束，进一步限制 memory access 的 perceived reordering。由于 RVWMO 模型是任何 RISC-V 实现允许的最弱模型，为该模型编写的软件与所有 RISC-V 实现的实际 memory consistency rule 兼容。

与 implicit read 类似，若要保证超出所假设 memory consistency model 和 execution environment 要求的特定 memory access ordering，软件必须执行 fence 或 cache-control 指令。

## 1.5 基础指令长度编码

RISC-V base ISA 具有固定长度 32-bit instruction，并且这些指令必须在 32-bit 边界上自然对齐。不过，标准 RISC-V 编码方案设计为支持带有 variable-length instruction 的 ISA extension；每条指令长度可以是任意数量的 16-bit instruction parcel，并且 parcel 在 16-bit 边界上自然对齐。第 16 章描述的 standard compressed ISA extension 通过提供压缩 16-bit instruction 降低代码大小，并放宽对齐约束，允许所有指令（16 bit 和 32 bit）对齐到任意 16-bit 边界，以提高代码密度。

本文使用 IALIGN（以 bit 计）表示实现所强制的 instruction-address alignment constraint。base ISA 中 IALIGN 为 32 bit，但一些 ISA extension（包括 compressed ISA extension）把 IALIGN 放宽到 16 bit。IALIGN 不能取 16 或 32 以外的值。

本文使用 ILEN（以 bit 计）表示实现支持的最大 instruction length，并且 ILEN 始终是 IALIGN 的倍数。对于只支持 base instruction set 的实现，ILEN 为 32 bit。支持更长指令的实现具有更大的 ILEN 值。

图 1.1 展示标准 RISC-V instruction-length encoding 约定。base ISA 中所有 32-bit instruction 的最低两位均设置为 `11`。可选 compressed 16-bit instruction-set extension 的最低两位等于 `00`、`01` 或 `10`。

### 扩展的指令长度编码

32-bit instruction-encoding space 的一部分已暂定分配给长于 32 bit 的指令。该空间当前全部保留，下面关于长于 32 bit 指令编码的提案并不视为 frozen。

用多于 32 bit 编码的 standard instruction-set extension 具有额外设置为 1 的低位。48-bit 和 64-bit 长度约定如图 1.1 所示。80 bit 到 176 bit 之间的指令长度使用 bits `[14:12]` 中的 3-bit 字段编码，该字段给出除最初 `5 × 16-bit` word 之外的 16-bit word 数量。bits `[14:12]` 设置为 `111` 的编码为未来更长 instruction encoding 保留。

```text
xxxxxxxxxxxxxxaa                                  16-bit (aa != 11)
xxxxxxxxxxxxxxxx xxxxxxxxxxxbbb11                 32-bit (bbb != 111)
...xxxx xxxxxxxxxxxxxxxx xxxxxxxxxx011111         48-bit
...xxxx xxxxxxxxxxxxxxxx xxxxxxxxx0111111         64-bit
...xxxx xxxxxxxxxxxxxxxx xnnnxxxxx1111111         (80 + 16*nnn)-bit, nnn != 111
...xxxx xxxxxxxxxxxxxxxx x111xxxxx1111111         Reserved for >=192-bits
Byte Address: base+4 base+2 base
```

图 1.1：RISC-V instruction length encoding。目前只有 16-bit 和 32-bit 编码被视为 frozen。

> 鉴于 compressed format 在代码大小和能耗上的节省，我们希望从一开始就在 ISA encoding scheme 中内建对 compressed format 的支持，而不是事后追加；但为了允许更简单的实现，我们不希望让 compressed format 成为强制要求。我们也希望可选地允许更长指令，以支持实验和更大的 instruction-set extension。虽然我们的编码约定要求对核心 RISC-V ISA 进行更紧凑编码，但这带来了若干好处。

> standard IMAFD ISA 的实现只需要在 instruction cache 中保存最高 30 bit（节省 6.25%）。在 instruction cache refill 时，遇到任一低位为 0 的指令，都应在存入 cache 前重新编码为非法 30-bit instruction，以保留 illegal instruction exception 行为。

> 也许更重要的是，通过把 base ISA 压缩到 32-bit instruction word 的一个子集中，我们为 non-standard 和 custom extension 留出了更多空间。特别是，base RV32I ISA 使用的编码空间不到 32-bit instruction word 的 1/8。如第 26 章所述，不需要支持 standard compressed instruction extension 的实现，可以在保留对 standard >=32-bit instruction-set extension 支持的同时，把 3 个额外 non-conforming 30-bit instruction space 映射到 32-bit fixed-width format 中。此外，如果实现也不需要长于 32 bit 的指令，则可以为 non-conforming extension 进一步回收四个 major opcode。

bits `[15:0]` 全为 0 的编码被定义为 illegal instruction。这些指令被认为具有最小长度：如果存在任何 16-bit instruction-set extension，则为 16 bit；否则为 32 bit。bits `[ILEN-1:0]` 全为 1 的编码也是 illegal；该指令被认为具有 ILEN bit 长度。

> 任意长度、内容全为 0 bit 的指令都不合法，这是一个特性，因为它能快速捕获错误跳转到清零 memory region 的情况。类似地，我们也把全 1 的 instruction encoding 保留为 illegal instruction，以捕获未编程 non-volatile memory device、断开的 memory bus 或损坏 memory device 中观察到的另一种常见模式。

> 软件可以依赖一个自然对齐且内容为 0 的 32-bit word 在所有 RISC-V 实现上表现为 illegal instruction；当软件明确需要 illegal instruction 时可以使用它。为全 1 定义一个所有实现都知道的对应 illegal value 更困难，因为存在 variable-length encoding。软件通常不能使用 ILEN bit 全 1 的 illegal value，因为软件可能不知道最终目标机器的 ILEN（例如，软件被编译进供许多不同机器使用的标准 binary library）。也曾考虑把全 1 的 32-bit word 定义为 illegal，因为所有机器都必须支持 32-bit instruction size；但这会要求 ILEN > 32 的机器在这样一条指令跨越 protection boundary 时，由 instruction-fetch unit 报告 illegal instruction exception 而不是 access fault，从而使 variable-instruction-length fetch 和 decode 复杂化。

RISC-V base ISA 具有 little-endian 或 big-endian memory system，privileged architecture 进一步定义 bi-endian 操作。无论 memory system endianness 如何，指令都以 16-bit little-endian parcel 序列存放在 memory 中。构成一条指令的 parcel 存放在递增的 halfword 地址上，最低地址的 parcel 保存指令规范中编号最低的 bit。

> 我们最初为 RISC-V memory system 选择 little-endian byte ordering，是因为 little-endian 系统目前在商业上占主导地位（所有 x86 系统；ARM 上的 iOS、Android 和 Windows）。一个次要原因是，我们也发现 little-endian memory system 对硬件设计者更自然。不过，某些应用领域（例如 IP networking）操作 big-endian 数据结构，某些 legacy code base 也假定 big-endian processor，因此我们定义了 RISC-V 的 big-endian 和 bi-endian 变体。

> 我们必须固定 instruction parcel 在 memory 中的存储顺序，使其独立于 memory system endianness，以确保 length-encoding bit 总是在 halfword 地址顺序中首先出现。这让 instruction-fetch unit 只需检查第一个 16-bit instruction parcel 的前几个 bit，就能快速确定 variable-length instruction 的长度。

> 我们进一步把 instruction parcel 本身做成 little-endian，以便把 instruction encoding 与 memory system endianness 完全解耦。这个设计有利于软件工具和 bi-endian 硬件。否则，例如 RISC-V assembler 或 disassembler 将总是需要知道预期的活动 endianness；而在 bi-endian 系统中，endianness mode 可能在执行期间动态改变。相反，通过给指令固定 endianness，精心编写的软件有时即使以二进制形式也可以做到 endianness-agnostic，类似 position-independent code。

> 不过，指令只采用 little-endian 的选择也会影响编码或解码 machine instruction 的 RISC-V 软件。例如，big-endian JIT compiler 在写入 instruction memory 时必须交换 byte order。

> 一旦我们决定固定使用 little-endian instruction encoding，自然就会把 length-encoding bit 放在 instruction format 的 LSB 位置，以避免打断 opcode field。

## 1.6 异常、trap 和 interrupt

本文使用 exception 表示运行时发生且与当前 RISC-V hart 中一条指令相关的异常条件。本文使用 interrupt 表示可能使 RISC-V hart 经历意外控制转移的外部异步事件。本文使用 trap 表示由 exception 或 interrupt 导致控制权转移到 trap handler。

后续章节中的指令描述会说明执行期间可能引发 exception 的条件。大多数 RISC-V EEI 的一般行为是：当一条指令发出 exception 信号时，会 trap 到某个 handler（floating-point exception 除外；在 standard floating-point extension 中，它们不会导致 trap）。interrupt 如何生成、如何路由到 hart、如何由 hart 启用，取决于 EEI。

> 我们对 “exception” 和 “trap” 的使用与 IEEE-754 floating-point standard 中的用法兼容。

trap 如何被处理，以及如何对运行在 hart 上的软件可见，取决于包围它的 execution environment。从运行在 execution environment 内的软件视角看，hart 在运行时遇到的 trap 可以有四种不同效果：

**Contained Trap：** trap 对运行在 execution environment 内的软件可见，并由该软件处理。例如，在一个同时为 hart 提供 supervisor mode 和 user mode 的 EEI 中，user-mode hart 发出的 `ECALL` 通常会导致控制权转移到运行在同一 hart 上的 supervisor-mode handler。类似地，在同一环境中，当 hart 被 interrupt 时，会在该 hart 上以 supervisor mode 运行 interrupt handler。

**Requested Trap：** trap 是一种 synchronous exception，它显式调用 execution environment，请求其代表 execution environment 内的软件执行某个动作。system call 就是一个例子。在这种情况下，execution environment 执行被请求动作后，hart 上的执行可能恢复，也可能不恢复。例如，system call 可能移除 hart，或导致整个 execution environment 有序终止。

**Invisible Trap：** trap 由 execution environment 透明处理，并在处理后正常恢复执行。例子包括模拟缺失指令、在 demand-paged virtual-memory system 中处理 non-resident page fault，或在 multiprogrammed machine 中处理另一个作业的 device interrupt。在这些情况下，运行在 execution environment 内的软件不会意识到 trap（这些定义忽略时序影响）。

**Fatal Trap：** trap 表示致命失败，并导致 execution environment 终止执行。例子包括 virtual-memory page-protection check 失败，或允许 watchdog timer 过期。每个 EEI 应定义执行如何终止，以及如何向外部环境报告。

下表展示每种 trap 的特征：

| 特征 | Contained | Requested | Invisible | Fatal |
|---|---|---|---|---|
| 执行会终止吗？ | N | N¹ | N | Y |
| 软件会毫无察觉吗？ | N | N | Y | Y² |
| 由 environment 处理吗？ | N | Y | Y | Y |

表 1.1：trap 的特征。注：1）可以请求终止；2）不精确的 fatal trap 可能被软件观察到。

EEI 为每个 trap 定义它是否被精确处理，不过建议在可能时保持精确性。Contained trap 和 requested trap 可以被 execution environment 内的软件观察为不精确。Invisible trap 按定义不能被运行在 execution environment 内的软件观察为精确或不精确。若已知错误的指令不会导致立即终止，则 fatal trap 可以被运行在 execution environment 内的软件观察为不精确。

由于本文档描述 unprivileged instruction，trap 很少被提及。处理 contained trap 的架构机制在 privileged architecture manual 中定义，该手册还定义支持更丰富 EEI 的其他特性。那些仅为导致 requested trap 而定义的 unprivileged instruction 记录在本文档中。Invisible trap 由于其本质，不属于本文档范围。本文档未定义、也未通过其他方式定义的 instruction encoding 可能导致 fatal trap。

## 1.7 UNSPECIFIED 行为和值

体系结构完整描述实现必须做什么，以及对实现可做什么施加的任何约束。在体系结构有意不约束实现的情况下，会显式使用 unspecified 一词。

unspecified 一词指有意不加约束的行为或值。这些行为或值的定义可以由 extension、platform standard 或 implementation 开放补充。extension、platform standard 或 implementation documentation 可以提供规范性内容，进一步约束 base architecture 定义为 unspecified 的情况。

与 base architecture 一样，extension 应完整描述允许的行为和值，并在有意不约束的情况下使用 unspecified 一词。这些情况可以由其他 extension、platform standard 或 implementation 约束或定义。
