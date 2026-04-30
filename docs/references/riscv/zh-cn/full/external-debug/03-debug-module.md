# 第 3 章 Debug Module (DM)

Debug Module 实现 abstract debug operation 与其具体实现之间的转换接口。它可能支持以下操作：

1. 向 debugger 提供关于实现的必要信息。（必需）
2. 允许任意单个 hart 被 halted 和 resumed。（必需）
3. 提供哪些 hart 已 halted 的状态。（必需）
4. 提供对 halted hart 的 GPR 的读写访问。（必需）
5. 提供对 reset 信号的访问，使得从 reset 后第一条指令开始调试成为可能。（必需）
6. 提供对其他 hart register 的访问。（可选）
7. 提供 Program Buffer，以强制 hart 执行任意指令。（可选）
8. 允许同时 halt、resume 并/或 reset 多个 hart。（可选）
9. 允许直接 System Bus Access。（可选）

为了实现 memory access，target 必须实现 Program Buffer 或 System Bus Access 二者之一。

单个 DM 最多可以调试 1024 个 hart。

## 3.1 Debug Module Interface (DMI)

Debug Module 是名为 Debug Module Interface（DMI）的总线上的 slave。该总线的 master 是 Debug Transport Module。Debug Module Interface 可以是只有一个 master 和一个 slave 的简单总线，也可以使用功能更完整的总线，例如 TileLink 或 AMBA Advanced Peripheral Bus。细节留给系统设计者决定。

DMI 使用 7 到 32 个地址 bit。它支持 read 和 write 操作。地址空间底部用于 DM。额外空间可用于 custom debug device、其他 core、额外 DM 等。

Debug Module 通过访问其 DMI address space 中的寄存器来控制。

表 3.1：Debug Module Interface 地址空间

| 地址 | 含义 |
|---|---|
| `0x00`-`0x3f` | 第 3.11 节描述的寄存器。 |
| `0x40`-`0x5f` | 称为 halt region。这 32 个 32-bit word 地址为最多 1024 个 hart 提供 halt bit 访问。如果 hart 已 halted，则 bit 为 1；否则为 0。hart 0 的 bit 是 `0x40` 处 32-bit word 的 LSB。hart 1023 的 bit 是 `0x5f` 处 32-bit word 的 MSB。 |

## 3.2 Reset Control

Debug Module 控制全局 reset 信号 `ndmreset`（non-debug module reset）。该信号可以 reset 或保持 reset 平台中除 Debug Module 和 Debug Transport Module 之外的每个组件。只要能够从第一条执行指令开始调试程序，该 reset 具体影响什么由实现定义。Debug Module 自身的状态和寄存器应只在上电时，以及 `dmcontrol` 中 `dmactive` 为 0 时 reset。只要 `dmactive` 为 1，hart 的 halt state 应在 system reset 期间保持，尽管 trigger CSR 可能被清除。

由于跨 clock domain 和 power domain 的问题，跨 system reset 进行任意 DMI 访问可能不可行。当 `ndmreset` 或任何 external reset 被 asserted 时，唯一支持的 DM 操作是访问 `dmcontrol`。其他访问的行为未定义。

规范不要求 `ndmreset` asserted 的持续时间。实现必须保证先写 `ndmreset=1`、再写 `ndmreset=0` 会触发 system reset。系统可能需要任意长时间才脱离 reset，这通过 `allunavail`、`anyunavail` 或其他实现特定指示器报告。

当 hart 已 reset 时，它们必须设置 sticky `havereset` state bit。概念上的 `havereset` state bit 可以通过 `dmstatus` 中选中 hart 的 `anyhavereset` 和 `allhavereset` 读取。无论 reset 原因是什么，这些 bit 都必须设置。选中 hart 的 `havereset` bit 可以通过向 `dmcontrol` 中 `ackhavereset` 写 1 来清除。当 `dmactive` 为低时，`havereset` bit 可以被清除，也可以不被清除。

## 3.3 Selecting Harts

最多 1024 个 hart 可以连接到单个 DM。debugger 选择一个 hart，随后 halt、resume、reset 和 debugging command 都特定于该 hart。

debugger 可以枚举连接到 DM 的全部 hart：从 0 开始逐个选择 hart，直到 `dmstatus` 中 `anynonexistent` 为 1。

debugger 可以通过使用接口读取 `mhartid`，或通过读取系统的 Device Tree，发现 hart index 与 `mhartid` 的映射。

### 3.3.1 Selecting a Single Hart

所有 debug module 都必须支持选择单个 hart。debugger 可以通过把 hart 的 index 写入 `hartsel` 来选择 hart。hart index 从 0 开始，并连续到最后一个 index。

### 3.3.2 Selecting Multiple Harts

Debug Module 可以选择实现 Hart Array Mask register，以允许一次选择多个 hart。debugger 可以使用 `hawindowsel` 和 `hawindow` 设置 hart array mask register 中的 bit，然后通过设置 `hasel` 对所有选中 hart 应用动作。如果支持该特性，则可以同时 halt、resume 和 reset 多个 hart。

只有由 `dmcontrol` 发起的动作可以一次应用到多个 hart；Abstract Command 只应用于 `hartsel` 选中的 hart。

## 3.4 Run Control

对于每个 hart，Debug Module 包含 3 个概念状态 bit：halt request、resume request 和 hart reset。（hart reset bit 是可选的。）这些 bit 全部 reset 为 0。debugger 可以通过 `dmcontrol` 中的 `haltreq`、`resumereq` 和 `hartreset` 为当前选中的 hart 写这些 bit。此外，DM 从每个 hart 接收 `halted`、`running` 和 `resume ack` 信号。

当 running hart 收到 halt request 时，它通过 halt 并 assert 其 `halted` 信号来响应。所有选中 hart 的 `halted` 信号反映在 `allhalted` 和 `anyhalted` bit 中。`haltreq` 会被 halted hart 忽略。

当 halted hart 收到 resume request 时，它通过 resume、清除其 `halted` 信号、assert 其 `running` 和 `resume ack` 信号来响应。resume request deasserted 时，`resume ack` 信号降低。所有选中 hart 的这些状态信号反映在 `allresumeack`、`anyresumeack`、`allrunning` 和 `anyrunning` 中。`resumereq` 会被 running hart 忽略。

当请求 halt 或 resume 时，除非 hart unavailable，否则 hart 必须在不到 1 秒内响应。（规范不进一步规定如何实现；更典型的延迟会是几个 clock cycle。）

## 3.5 Abstract Commands

DM 支持一组 abstract command，其中大多数是可选的。取决于实现，debugger 可能即使在选中 hart 未 halted 时也能执行某些 abstract command。debugger 只能通过尝试命令、然后查看 `abstractcs` 中 `cmderr` 是否成功，来确定给定 hart 在给定状态下支持哪些 abstract command。

debugger 通过把 abstract command 写入 `command` 来执行它。debugger 可以通过读取 `abstractcs` 中 `busy` 来确定 abstract command 是否完成。如果命令需要参数，debugger 必须在写 `command` 前把参数写入 data register。如果命令返回结果，Debug Module 必须保证结果在 `busy` 被清除前放入 data register。参数使用哪些 data register 见表 3.2。在所有情况下，最低有效 word 放入编号最低的 data register。

表 3.2：Data register 的使用

| XLEN | `arg0`/return value | `arg1` | `arg2` |
|---|---|---|---|
| 32 | `data0` | `data1` | `data2` |
| 64 | `data0`, `data1` | `data2`, `data3` | `data4`, `data5` |
| 128 | `data0`-`data3` | `data4`-`data7` | `data8`-`data11` |

### 3.5.1 Abstract Command Listing

本节描述每种 abstract command，以及它们写入 `command` 时字段应如何解释。每个 abstract command 是 32-bit 值。最高 8 bit 包含 `cmdtype`，它决定命令种类。

表 3.3：`cmdtype` 的含义

| `cmdtype` | Command |
|---|---|
| 0 | Access Register Command |
| 1 | Quick Access |

#### 3.5.1.1 Access Register

该命令使 debugger 能访问 CPU register 和 program buffer。它执行以下操作序列：

1. 如果 `write` 清零且 `transfer` 置位，则把 `regno` 指定的 register 中的数据复制到 data 的 `arg0` 区域。
2. 如果 `write` 置位且 `transfer` 置位，则把 data 的 `arg0` 区域中的数据复制到 `regno` 指定的 register。
3. 如果 `postexec` 置位，则执行 Program Buffer。

如果任何操作失败，则设置 `cmderr`，并且不执行剩余步骤。实现可以提前检测即将发生的失败，并在到达会导致失败的步骤之前使整个命令失败。

Debug Module 必须实现该命令，并且必须在选中 hart halted 时支持对所有 GPR 的读写访问。Debug Module 可以选择支持访问其他 register，或在 hart running 时访问 register。如果该命令在 hart running 时支持某个 register，则它在 hart halted 时也必须支持该 register。每个单独 register（GPR 以外）在 read、write 和 halt status 上的支持可以不同。

`size` 的编码被选择为匹配 `sbcs` 中的 `sbaccess`。

Access Register 字段：

| Field | Description |
|---|---|
| `cmdtype` | 为 0，表示 Access Register Command。 |
| `size` | 2：访问 register 的最低 32 bit。3：访问最低 64 bit。4：访问最低 128 bit。如果 `size` 指定的大小大于 register 实际大小，则访问必须失败。如果某个 register 可访问，则必须支持小于或等于该 register 实际大小的 `size` read。 |
| `postexec` | 为 1 时，在执行 transfer（若有）之后，将 Program Buffer 中的程序恰好执行一次。 |
| `transfer` | 0：不执行 `write` 指定的操作。1：执行 `write` 指定的操作。该 bit 可用于只执行 Program Buffer，而无需担心把有效值放入 `size` 或 `regno`。 |
| `write` | 当 `transfer` 置位时：0 表示把指定 register 中的数据复制到 data 的 `arg0` 部分；1 表示把 data 的 `arg0` 部分复制到指定 register。 |
| `regno` | 要访问的 register 编号，见表 3.4。如果该命令在非 halted hart 上受支持，`dpc` 可作为 PC 的别名。 |

#### 3.5.1.2 Quick Access

执行以下操作序列：

1. 如果 hart 已 halted，则命令把 `cmderr` 设置为 halt/resume，并且不继续。
2. Halt hart。如果 hart 因其他原因 halt（例如 breakpoint），命令把 `cmderr` 设置为 halt/resume，并且不继续。
3. 执行 Program Buffer。如果发生 exception，则 `cmderr` 被设置为 exception，program buffer execution 结束，但 quick access command 继续。
4. Resume hart。

实现该命令是可选的。

字段：

| Field | Description |
|---|---|
| `cmdtype` | 为 1，表示 Quick Access command。 |

表 3.4：Abstract Register Numbers

| 范围 | 含义 |
|---|---|
| `0x0000`-`0x0fff` | CSR。“PC”可通过 `dpc` 在这里访问。 |
| `0x1000`-`0x101f` | GPR |
| `0x1020`-`0x103f` | Floating point register |
| `0xc000`-`0xffff` | 为非标准扩展和内部使用保留。 |

## 3.6 Program Buffer

为了支持在 halted hart 上执行任意指令，Debug Module 可以包含 Program Buffer，debugger 可以把小程序写入其中。只使用 abstract command 就支持全部必要功能的系统，可以选择省略 Program Buffer。

debugger 可以把一个小程序写入 Program Buffer，然后使用 Access Register Abstract Command 并设置 `command` 中 `postexec` bit，把它恰好执行一次。debugger 可以写入任何想要的程序（包括跳出 Program Buffer），但程序必须以 `ebreak` 或 `c.ebreak` 结束。为了节省硬件，实现可以支持隐式 `ebreak`，当 hart 跑到 Program Buffer 末尾之后不存在的 word 时执行。该特性由 `impebreak` 指示。有了该特性，仅 2 个 32-bit word 的 Program Buffer 就能提供高效调试。

如果 `progbufsize` 为 1，则 Program Buffer 只能容纳单条指令，并且 `impebreak` 必须为 1。这条指令可以是一条 32-bit 指令，也可以是低 16 bit 中的一条 compressed instruction 加上高 16 bit 中的 compressed nop。

如果 debugger 执行的程序没有用 `ebreak` instruction 终止，hart 将保持在 Debug Mode，直到它被 reset。

执行这些程序时，hart 不离开 Debug Mode（见第 4.1 节）。如果 Program Buffer 执行期间遇到 exception，则不再执行更多指令，hart 保持在 Debug Mode，并且 `cmderr` 设置为 3（exception error）。如果 debugger 执行了不会终止的程序，则它会失去对 hart 的控制。

执行 Program Buffer 可能 clobber `dpc`。如果会发生这种情况，则必须能够使用未设置 `postexec` 的 abstract command 读写 `dpc`。debugger 必须尝试在 halt 和执行 Program Buffer 之间保存 `dpc`，并在离开 Debug Mode 之前恢复 `dpc`。允许 Program Buffer execution clobber `dpc`，使那些没有单独 PC register、并且执行 Program Buffer 时需要使用 PC 的直接实现成为可能。

Program Buffer 可以实现为 hart 可作为 RAM memory 访问的 RAM。debugger 可以通过执行小程序来确定是否如此，这些小程序在从 Program Buffer 执行期间尝试相对于 `pc` 写入和读回。如果是这样，debugger 对 program buffer 能做的事情就更灵活。

## 3.7 Overview of States

图 3.1 给出一个概念视图，展示 hart 在 run/halt debugging 中受 `dmcontrol`、`abstractcs`、`abstractauto` 和 `command` 不同字段影响所经过的状态。因为 debugger 只能看到少量状态，所以图中的状态和转换是概念性的。

## 3.8 System Bus Access

当 Program Buffer 存在时，debugger 可以通过让 RISC-V hart 执行所需访问来访问 system bus。无论是否实现 Program Buffer，Debug Module 也可以包含 System Bus Access block，在不涉及 hart 的情况下提供 memory access。System Bus Access block 使用 physical address。

取决于微架构，通过 System Bus Access 访问的数据不一定总是与每个 hart 观察到的数据一致。（例如，hart 可能有不 snoop 或非 write-through 的 cache。）如果实现不保证一致性，则由 debugger 强制保证 coherency。本规范不定义完成此事的标准方式，因为它依赖于实现/平台。可能做法包括使用 System Bus Interface 并/或 Program Buffer 写入特殊 memory-mapped location，或通过 Program Buffer 执行特殊指令。

即使 Debug Module 也实现 Program Buffer，实现 System Bus Access block 仍有若干好处。第一，可以以最小影响访问 running system 中的 memory。第二，访问 memory 时可能提升性能。第三，它可以访问 hart 无权访问的 device。

## 3.9 Quick Access

取决于正在执行的任务，有些 hart 只能被非常短暂地 halted。存在几种机制，允许以对 running hart 最小的影响访问此类 running system 中的资源。

第一，实现可以允许某些 abstract command 在不 halt hart 的情况下执行。第二，Quick Access abstract command 可用于 halt hart、快速执行 Program Buffer 内容、然后让 hart 再次运行。结合第 3.11.3 节描述的允许 Program Buffer code 访问 data register 的指令，这可用于快速执行 memory 或 register access。对某些系统而言这仍过于侵入，但许多不能长时间 halt 的系统可以承受偶发的、不超过约百个 cycle 的 hiccup。第三，如果实现了 System Bus Access block，则它可以在 hart running 时用于访问 system memory。

## 3.10 Security

为了保护知识产权，可能希望锁定对 Debug Module 的访问。为了在制造流程期间允许访问而之后不允许，一个合理方案是在 Debug Module 中增加 fuse bit，以便永久 disable 它。由于这依赖于技术，规范不进一步处理。

另一种选择是只允许拥有 access key 的用户 unlock DM。`dmstatus` 和 `authdata` 中的少量 bit 可以支持任意复杂的 authentication mechanism。当 `authenticated` 清零时，DM 必须完全不以任何方式与平台其余部分交互。

## 3.11 Debug Module DMI Registers

读取未实现的 Debug Module DMI Register 时返回 0。写入它们没有效果。

表 3.5：Debug Module Debug Bus Registers

| Address | Name |
|---|---|
| `0x04` | Abstract Data 0 |
| `0x0f` | Abstract Data 11 |
| `0x10` | Debug Module Control |
| `0x11` | Debug Module Status |
| `0x12` | Hart Info |
| `0x13` | Halt Summary |
| `0x14` | Hart Array Window Select |
| `0x15` | Hart Array Window |
| `0x16` | Abstract Control and Status |
| `0x17` | Abstract Command |
| `0x18` | Abstract Command Autoexec |
| `0x19` | Device Tree Addr 0 |
| `0x1a` | Device Tree Addr 1 |
| `0x1b` | Device Tree Addr 2 |
| `0x1c` | Device Tree Addr 3 |
| `0x20` | Program Buffer 0 |
| `0x2f` | Program Buffer 15 |
| `0x30` | Authentication Data |
| `0x38` | System Bus Access Control and Status |
| `0x39` | System Bus Address 31:0 |
| `0x3a` | System Bus Address 63:32 |
| `0x3b` | System Bus Address 95:64 |
| `0x3c` | System Bus Data 31:0 |
| `0x3d` | System Bus Data 63:32 |
| `0x3e` | System Bus Data 95:64 |
| `0x3f` | System Bus Data 127:96 |

### 3.11.1 Debug Module Status (`dmstatus`, at `0x11`)

该寄存器地址未来不会改变，因为它包含 `version`。它相对于本规范 0.11 版已经变化。

该寄存器报告整个 debug module 的状态，以及按 `hasel` 定义的当前选中 hart 的状态。

如果 hart 无论用户等待多久都永远不会成为该系统的一部分，则它是 nonexistent。例如，在简单单 hart 系统中只有一个 hart 存在，其他 hart 都是 nonexistent。

如果 hart 可能在稍后存在/变为可用，则它是 unavailable。例如，在多 hart 系统中，某些 hart 可能暂时掉电，或者系统可能支持 hot-swapping hart。

`dmstatus` 字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `dmerr` | 若 Debug Module 被错误访问，则置位。0（none）：无错误。1（badaddr）：访问了未实现的 Debug Module 地址。7（other）：访问因其他原因失败。 | R/W1C | 0 |
| `impebreak` | 若为 1，则 Program Buffer 后面紧接着的不存在 word 处有隐式 `ebreak` instruction。这使 debugger 不必自己写 `ebreak`，并允许 Program Buffer 小一个 word。当 `progbufsize` 为 1 时它必须为 1。 | R | Preset |
| `allhavereset` | 当前所有选中 hart 已 reset 但 reset 尚未 acknowledged 时为 1。 | R | - |
| `anyhavereset` | 当前任一选中 hart 已 reset 但 reset 尚未 acknowledged 时为 1。 | R | - |
| `allresumeack` | 当前所有选中 hart 已 acknowledged 前一次 resume request 时为 1。 | R | - |
| `anyresumeack` | 当前任一选中 hart 已 acknowledged 前一次 resume request 时为 1。 | R | - |
| `allnonexistent` | 当前所有选中 hart 在本系统中不存在时为 1。 | R | - |
| `anynonexistent` | 当前任一选中 hart 在本系统中不存在时为 1。 | R | - |
| `allunavail` | 当前所有选中 hart unavailable 时为 1。 | R | - |
| `anyunavail` | 当前任一选中 hart unavailable 时为 1。 | R | - |
| `allrunning` | 当前所有选中 hart running 时为 1。 | R | - |
| `anyrunning` | 当前任一选中 hart running 时为 1。 | R | - |
| `allhalted` | 当前所有选中 hart halted 时为 1。 | R | - |
| `anyhalted` | 当前任一选中 hart halted 时为 1。 | R | - |
| `authenticated` | 使用 DM 前需要 authentication 时为 0；authentication check 已通过时为 1。不实现 authentication 的组件必须把该 bit preset 为 1。 | R | Preset |
| `authbusy` | 0：authentication module 准备好处理下一次对 `authdata` 的 read/write。1：authentication module busy；访问 `authdata` 导致 unspecified behavior。`authbusy` 只会在访问 `authdata` 的立即响应中置位。 | R | 0 |
| `devtreevalid` | 0：`devtreeaddr0`-`devtreeaddr3` 持有与 Device Tree 无关的信息。1：这些寄存器持有 Device Tree 地址。 | R | Preset |
| `version` | 0：不存在 Debug Module。1：存在 Debug Module，符合本规范 0.11。2：存在 Debug Module，符合本规范 0.13。15：存在 Debug Module，但不符合本规范任何可用版本。 | R | 2 |

### 3.11.2 Debug Module Control (`dmcontrol`, at `0x10`)

该寄存器控制整体 debug module，以及按 `hasel` 定义的当前选中 hart。

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `haltreq` | 为所有当前选中 hart 写 halt request bit。置 1 时，每个选中 hart 若当前未 halted 将 halt。对已经 halted 的 hart 写 1 或 0 没有效果，但在 hart resumed 前该 bit 必须清零。写入应用于 `hartsel` 和 `hasel` 的新值。 | W | - |
| `resumereq` | 为所有当前选中 hart 写 resume request bit。置 1 时，每个选中 hart 若当前 halted 将 resume。当 halt request bit 置位时，resume request bit 被忽略。写入应用于 `hartsel` 和 `hasel` 的新值。 | W | - |
| `hartreset` | 可选字段，为所有当前选中 hart 写 reset bit。debugger 写 1 执行 reset，然后写 0 deassert reset signal。如果未实现该特性，bit 始终保持 0，因此 debugger 写 1 后可以读回寄存器判断是否支持。写入应用于 `hartsel` 和 `hasel` 的新值。 | R/W | 0 |
| `ackhavereset` | 向该 bit 写 1 会清除任何选中 hart 的 `havereset` bit。写入应用于 `hartsel` 和 `hasel` 的新值。 | W | - |
| `hasel` | 选择当前选中 hart 的定义。0：只有单个当前选中 hart，即 `hartsel` 选中的 hart。1：可能有多个当前选中 hart，即 `hartsel` 选中的 hart 加上 hart array mask register 选中的 hart。不实现 hart array mask register 的实现应把该字段绑为 0。希望使用 hart array mask register 特性的 debugger 应设置该 bit 并读回，以判断功能是否支持。 | R/W | 0 |
| `hartsel` | 要选择的 hart 的 DM-specific index。该 hart 总是当前选中 hart 的一部分。 | R/W | 0 |
| `ndmreset` | 该 bit 控制从 DM 到系统其余部分的 reset signal。该信号应 reset 系统的每一部分，包括每个 hart，但不包括 DM 和访问 DM 所需的任何逻辑。为了执行 system reset，debugger 写 1，然后写 0 deassert reset。 | R/W | 0 |
| `dmactive` | 该 bit 作为 Debug Module 自身的 reset signal。0：module 状态（包括 authentication mechanism）取 reset value（`dmactive` bit 是唯一可被写为非 reset value 的 bit）。1：module 正常工作。除 power up 之外，不应存在任何其他机制可导致 Debug Module reset，包括 platform system reset 或 Debug Transport reset signal。debugger 可以把该 bit pulse low，使 debug module 进入已知状态。实现可以使用该 bit 辅助调试，例如在 debugging active 时阻止 Debug Module 被 power gated。 | R/W | 0 |

### 3.11.3 Hart Info (`hartinfo`, at `0x12`)

该寄存器给出 `hartsel` 当前选中 hart 的信息。该寄存器是可选的；若不存在，应读为全 0。若包含该寄存器，debugger 可以通过写显式访问 data 并/或 `dscratch` register 的程序，更充分地使用 Program Buffer。整个寄存器只读。

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `nscratch` | debugger 在 program buffer execution 期间可使用的 `dscratch` register 数量，从 `dscratch0` 开始。debugger 不能假定命令之间这些寄存器的内容。 | R | Preset |
| `dataaccess` | 0：data register 在 hart 中由 CSR register shadow。每个 CSR register 为 XLEN bit，对应表 3.2 中的单个 argument。1：data register 在 hart memory map 中 shadow。每个 register 在 memory map 中占 4 byte。 | R | Preset |
| `datasize` | 若 `dataaccess` 为 0：专用于 shadow data register 的 CSR register 数量。若 `dataaccess` 为 1：memory map 中专用于 shadow data register 的 32-bit word 数量。 | R | Preset |
| `dataaddr` | 若 `dataaccess` 为 0：专用于 shadow data register 的第一个 CSR 的编号。若 `dataaccess` 为 1：data register 被 shadow 的 RAM signed address，用于相对于 zero 访问。 | R | Preset |

### 3.11.4 Halt Summary (`haltsum`, at `0x13`)

该寄存器包含哪些 hart 已 halted 的摘要。每个 bit 包含 32 个 halt bit 的逻辑 OR。当系统中有大量 hart 时，debugger 可以先读取该寄存器，再从 halt region（`0x40`-`0x5f`）读取，以确定哪个 hart halted。整个寄存器只读。

字段按 bit 从高到低分别汇总：`halt1023:992`、`halt991:960`、`halt959:928`、`halt927:896`、`halt895:864`、`halt863:832`、`halt831:800`、`halt799:768`、`halt767:736`、`halt735:704`、`halt703:672`、`halt671:640`、`halt639:608`、`halt607:576`、`halt575:544`、`halt543:512`、`halt511:480`、`halt479:448`、`halt447:416`、`halt415:384`、`halt383:352`、`halt351:320`、`halt319:288`、`halt287:256`、`halt255:224`、`halt223:192`、`halt191:160`、`halt159:128`、`halt127:96`、`halt95:64`、`halt63:32`、`halt31:0`。

### 3.11.5 Hart Array Window Select (`hawindowsel`, at `0x14`)

该寄存器选择 hart array mask register 的哪个 32-bit 部分可通过 `hawindow` 访问。

hart array mask register 为 debug module 控制的所有 hart 提供 mask。若 hart array mask register 中对应 bit 被设置且 `dmcontrol` 中 `hasel` 为 1，或者 hart 被 `hartsel` 选中，则该 hart 是当前选中 hart 的一部分。

字段：`hawindowsel` 选择窗口编号，其余 bit 为 0。

### 3.11.6 Hart Array Window (`hawindow`, at `0x15`)

该寄存器提供对 hart array mask register 的一个 32-bit 部分的 R/W 访问。窗口位置由 `hawindowsel` 决定。即 bit 0 指 hart `hawindowsel * 32`，bit 31 指 hart `hawindowsel * 32 + 31`。

字段：`maskdata[31:0]`。

### 3.11.7 Abstract Control and Status (`abstractcs`, at `0x16`)

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `progbufsize` | Program Buffer 大小，单位为 32-bit word。合法大小为 0-16。 | R | Preset |
| `busy` | 1：当前正在执行 abstract command。该 bit 在 `command` 被写入后立即置位，直到该命令完成才清零。 | R | 0 |
| `cmderr` | 若 abstract command 失败则置位。字段 bit 保持置位，直到向它们写 1 清除。在值 reset 为 0 前，不会启动任何 abstract command。0（none）：无错误。1（busy）：当 abstract command 正在执行时写入了 `command`、`abstractcs`、`abstractauto`，或读写了某个 `data`/`progbuf` register。2（not supported）：请求的命令不受支持；hart running 时不支持的命令在 halted 时可能支持。3（exception）：执行命令时发生 exception，例如执行 Program Buffer 时。4（halt/resume）：由于 hart 不在期望状态（running/halted），abstract command 无法执行。7（other）：命令因其他原因失败。 | R/W1C | 0 |
| `datacount` | 作为 abstract command interface 一部分实现的 data register 数量。合法大小为 0-12。 | R | Preset |

### 3.11.8 Abstract Command (`command`, at `0x17`)

写该寄存器会导致对应 abstract command 执行。当 abstract command 正在执行时写入会导致 `cmderr` 置位。如果 `cmderr` 非 0，对该寄存器的写入会被忽略。

`cmderr` 会抑制新命令启动，以适配那些出于性能原因连续发送若干命令、期间不检查 `cmderr` 的 debugger。它们可以安全地这样做，并在末尾检查 `cmderr`，不用担心某个命令失败但后续可能依赖它成功的命令却通过。

| Field | Description | Access | Reset |
|---|---|---|---|
| `cmdtype` | 类型决定该 abstract command 的整体功能。 | W | 0 |
| `control` | 该字段以命令特定方式解释，在各 abstract command 中描述。 | W | 0 |

### 3.11.9 Abstract Command Autoexec (`abstractauto`, at `0x18`)

该寄存器是可选的。包含它允许更高效的 burst access。debugger 可以尝试设置 bit 并读回，以确定功能是否支持。

| Field | Description | Access | Reset |
|---|---|---|---|
| `autoexecprogbuf` | 当该字段中的某个 bit 为 1 时，对相应 `progbuf` word 的 read 或 write access 会导致 `command` 中的命令再次执行。 | R/W | 0 |
| `autoexecdata` | 当该字段中的某个 bit 为 1 时，对相应 `data` word 的 read 或 write access 会导致 `command` 中的命令再次执行。 | R/W | 0 |

### 3.11.10 Device Tree Addr 0 (`devtreeaddr0`, at `0x19`)

当 `devtreevalid` 置位时，读取该寄存器返回 Device Tree 地址的 bit 31:0。读取其他 `devtreeaddr` register 返回地址的高 bit。

当实现 system bus mastering 时，这必须是可由 System Bus Access module 使用的地址。否则，这必须是 hart ID 0 可用于访问 Device Tree 的地址。

如果 `devtreevalid` 为 0，则 `devtreeaddr` register 持有本文档未进一步规定的 identifier information。Device Tree 本身在 RISC-V Privileged Specification 中描述。整个寄存器只读，字段为 `addr[31:0]`。

### 3.11.11 Abstract Data 0 (`data0`, at `0x04`)

基本 read/write register，可由 abstract command 读取或改变。当 abstract command 正在执行时访问它们会导致 `cmderr` 置位。当 `busy` 置位时尝试写入不会改变其值。

这些寄存器中的值在 abstract command 执行后可能不被保留。关于其内容的唯一保证是相关命令给出的保证。如果命令失败，则不能对这些寄存器的内容作任何假设。字段为 `data[31:0]`。

### 3.11.12 Program Buffer 0 (`progbuf0`, at `0x20`)

`progbuf` register 提供对可选 program buffer 的 read/write 访问。当 abstract command 正在执行时访问它们会导致 `cmderr` 置位。当 `busy` 置位时尝试写入不会改变其值。字段为 `data[31:0]`。

### 3.11.13 Authentication Data (`authdata`, at `0x30`)

该寄存器作为通往 authentication module 的 32-bit serial port。当 `authbusy` 清零时，debugger 可以通过读写该寄存器与 authentication module 通信。没有单独机制来表示 overflow/underflow。字段为 `data[31:0]`。

### 3.11.14 System Bus Access Control and Status (`sbcs`, at `0x38`)

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `sbsingleread` | 向此处写 1，会使用 `sbaccess` 设置的 access size，在 `sbaddress` 中的地址触发一次 read。 | W1 | 0 |
| `sbaccess` | 选择由写 `sbaddress` register 或 `sbdata0` 触发的 system bus access 使用的 access size。0：8-bit。1：16-bit。2：32-bit。3：64-bit。4：128-bit。若写入不支持的 system bus access size，DM 不执行访问并把 `sberror` 置为 3。 | R/W | 2 |
| `sbautoincrement` | 为 1 时，每次 system bus access 后，`sbaddress` 按 `sbaccess` 选择的 access size（byte 数）递增。 | R/W | 0 |
| `sbautoread` | 为 1 时，每次读取 `sbdata0` 都自动在（可能已 auto-incremented 的）地址触发一次 system bus read。 | R/W | 0 |
| `sberror` | 当 debug module 的 system bus master 导致 bus error 时置位。该字段 bit 保持置位，直到写 1 清除。当该字段非 0 时，debug module 不能发起更多 system bus access。0：无 bus error。1：timeout。2：访问 bad address。3：其他错误，例如 alignment。4：写某个 `sbaddress` 或 `sbdata` register 时 system bus master busy，或在 `sbdata0` 有 stale data 时读取了 `sbdata0`。 | R/W1C | 0 |
| `sbasize` | system bus address 宽度，单位为 bit。（0 表示不支持 bus access。） | R | Preset |
| `sbaccess128` | 支持 128-bit system bus access 时为 1。 | R | Preset |
| `sbaccess64` | 支持 64-bit system bus access 时为 1。 | R | Preset |
| `sbaccess32` | 支持 32-bit system bus access 时为 1。 | R | Preset |
| `sbaccess16` | 支持 16-bit system bus access 时为 1。 | R | Preset |
| `sbaccess8` | 支持 8-bit system bus access 时为 1。 | R | Preset |

### 3.11.15 System Bus Address 31:0 (`sbaddress0`, at `0x39`)

如果 `sbasize` 为 0，则该寄存器不存在。当 system bus master busy 时，写该寄存器会设置 `sberror`。如果 `sberror` 为 0 且 `sbautoread` 已设置，则 system bus master 会在从 `address` 更新地址后开始 read。access size 由 `sbcs` 中 `sbaccess` 控制。如果 `sbsingleread` 被设置，该 bit 会被清除。

字段：`address` 访问 `sbaddress` 中 physical address 的 bit 31:0。Access R/W，Reset 0。

### 3.11.16 System Bus Address 63:32 (`sbaddress1`, at `0x3a`)

字段：`address` 访问 `sbaddress` 中 physical address 的 bit 63:32（如果 system address bus 有这么宽）。Access R/W，Reset 0。

### 3.11.17 System Bus Address 95:64 (`sbaddress2`, at `0x3b`)

如果 `sbasize` 小于 65，则该寄存器不存在。字段：`address` 访问 `sbaddress` 中 physical address 的 bit 95:64（如果 system address bus 有这么宽）。Access R/W，Reset 0。

### 3.11.18 System Bus Data 31:0 (`sbdata0`, at `0x3c`)

如果 `sbcs` 中所有 `sbaccess` bit 都为 0，则该寄存器不存在。任何成功的 system bus read 都会更新该寄存器中的 data，并把它标记为不再 stale。如果 `sberror` 不为 0，则访问不做任何事。

写该寄存器：

1. 如果 bus master busy，则访问设置 `sberror`，且不做其他事。
2. 启动一次从 `sbdata` 到 `sbaddress` 的 bus write。
3. 如果设置了 `sbautoincrement`，递增 `sbaddress`。

读该寄存器：

1. 如果该寄存器标记为 stale，则设置 `sberror`，且不做其他事。
2. “返回” data。
3. 把寄存器标记为 stale。
4. 如果设置了 `sbautoincrement`，递增 `sbaddress`。
5. 如果设置了 `sbautoread`，启动另一次 system bus read。

只有 `sbdata0` 有该行为。其他 `sbdata` register 没有副作用。在 bus 宽于 32 bit 的系统上，debugger 应在访问其他 `sbdata` register 之后访问 `sbdata0`。

字段：`data` 访问 `sbdata` 的 bit 31:0。Access R/W，Reset 0。

### 3.11.19 System Bus Data 63:32 (`sbdata1`, at `0x3d`)

如果 `sbaccess64` 和 `sbaccess128` 为 0，则该寄存器不存在。字段：`data` 访问 `sbdata` 的 bit 63:32（如果 system bus 有这么宽）。Access R/W，Reset 0。

### 3.11.20 System Bus Data 95:64 (`sbdata2`, at `0x3e`)

该寄存器仅在 `sbaccess128` 为 1 时存在。字段：`data` 访问 `sbdata` 的 bit 95:64（如果 system bus 有这么宽）。Access R/W，Reset 0。

### 3.11.21 System Bus Data 127:96 (`sbdata3`, at `0x3f`)

该寄存器仅在 `sbaccess128` 为 1 时存在。字段：`data` 访问 `sbdata` 的 bit 127:96（如果 system bus 有这么宽）。Access R/W，Reset 0。
