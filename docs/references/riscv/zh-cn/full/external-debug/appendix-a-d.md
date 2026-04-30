# 附录 A Hardware Implementations

下面给出两种可能实现。设计者可以选择其中一种、混合搭配，或提出自己的设计。

## A.1 Abstract Command Based

halt 通过 stall processor execution pipeline 发生。

register file 上的 mux 允许使用 Access Register abstract command 访问 GPR 和 CSR。

System Bus Access 允许访问 main memory。

## A.2 Execution Based

该实现只为 halted hart 上的 GPR 实现 Access Register abstract command，并依赖 Program Buffer 执行所有其他操作。

该方法使用 processor 现有 pipeline 以及从任意 memory location 执行的能力，避免修改 processor datapath。当 halt request bit 置位时，Debug Module 向选中 hart raise 一个特殊 interrupt。该 interrupt 使每个 hart 进入 Debug Mode，并跳转到由 DM 服务的已定义 memory region。接收该 exception 时，`pc` 保存到 `dpc`，并且 `dcsr` 中的 `cause` 更新。

Debug Module 中的代码使 hart 执行 “park loop”。在 park loop 中，hart 把自己的 `mhartid` 写到 Debug Module 内的某个 memory location，以指示自己 halted。为了允许 DM 在多个 halted hart 中单独控制一个 hart，每个 hart 轮询 DM 控制的 memory location 中的 flag，以确定 debugger 是否希望它执行 Program Buffer 或执行 resume。

为了执行 abstract command，DM 先根据 `command` 填充若干内部 program buffer word。当 `transfer` 置位时，debugger 用 `lw <gpr>, 0x400(zero)` 或 `sw 0x400(zero), <gpr>` 填充这些 word。64-bit 和 128-bit access 分别使用 `ld`/`sd` 和 `lq`/`sq`。如果 `transfer` 未置位，这些 instruction 填充为 `nop`。如果 `execute` 置位，执行继续到 debugger 控制的 Program Buffer；否则 debug module 使 `ebreak` 立即执行。

当 `ebreak` 执行时（表示 Program Buffer code 结束），hart 返回 park loop。如果遇到 exception，hart 跳到 Debug Module 内已定义的 debug exception address。该地址处的代码使 hart 写 Debug Module 中某个表示 exception 的地址。然后 hart 跳回 park loop。DM 从该 write 推断发生了 exception，并相应设置 `cmderr`。

为了 resume execution，debug module 设置一个 flag，使 core 执行 `dret`。当 `dret` 执行时，`pc` 从 `dpc` 恢复，normal execution 以 `prv` 设置的 privilege 恢复。

`data0` 等映射到普通 memory 中相对于 zero、仅使用 12-bit immediate 的地址。确切地址是实现细节，debugger 绝不能依赖它。例如，data register 可能映射到 `0x400`。

为获得额外灵活性，`progbuf0` 等紧邻 `data0` 之前映射到普通 memory，从而形成一个连续 memory region，可用于 program execution 或 data transfer。

# 附录 B Debugger Implementation

本节详述外部 debugger 可能如何使用所描述的 debug interface，在 RISC-V core 上执行一些常见操作。示例使用附录中描述的 JTAG DTM。所有示例都假定 32-bit core，但应易于适配到 64-bit 或 128-bit core。

为保持示例可读，它们都假定一切成功，并且完成速度快于 debugger 执行下一次访问的速度。在典型 JTAG setup 中通常如此。然而，debugger 在执行一系列动作后必须始终检查 sticky error status bit。如果发现任何 bit 置位，则应尝试再次执行相同动作，可能加入一些 delay，或显式检查 status bit。

## B.1 Debug Module Interface Access

要读取任意 Debug Module register，选择 `dmi`，并 scan in 一个 `op=1`、`address` 为所需 register address 的值。在 Update-DR 中 operation 将开始；在 Capture-DR 中，其结果将捕获到 `data`。如果 operation 未及时完成，`op` 将为 3，并且必须忽略 `data` 中的值。busy condition 必须通过写 `dtmcs` 中 `dmireset` 清除，然后第二次 scan 必须再次执行。该过程必须重复，直到 `op` 返回 0。在之后的 operation 中，debugger 应在 Capture-DR 和 Update-DR 之间留出更多时间。

要写任意 Debug Bus register，选择 `dmi`，并 scan in 一个 `op=2`、`address` 和 `data` 分别设置为所需 register address 和 data 的值。之后所有过程与 read 完全相同，只是执行的是 write 而不是 read。

几乎永远不应需要 scan IR，这避免了典型 JTAG 使用中的很大一部分低效率。

## B.2 Main Loop

debugger 持续监视 `haltsum`，以查看是否有任何 hart spontaneous halted。

## B.3 Halting

为了 halt 一个或多个 hart，debugger 选择它们，设置 `haltreq`，然后等待 `allhalted` 指示 hart 已 halted，最后把 `haltreq` 清为 0。

## B.4 Running

首先，debugger 应恢复任何被它 clobber 的 register。完成后，可以通过设置 `resumereq` 让选中 hart 运行。一旦 `allresumeack` 置位，debugger 就知道 hart 已 resumed，然后可以清除 `resumereq`。注意，hart 可能在 resume 后很快 halt（例如命中 software breakpoint），因此 debugger 不能使用 `allhalted`/`anyhalted` 检查 hart 是否 resumed。

## B.5 Single Step

使用 hardware single step feature 几乎与 regular running 相同。debugger 只需在让 core 运行之前设置 `dcsr` 中的 `step`。core 的行为与 running case 完全相同，区别是 interrupt 可能 disabled（取决于 `stepie`），并且它只 fetch 和 execute 单条指令，然后重新进入 Debug Mode。

## B.6 Accessing Registers

### B.6.1 Using Abstract Command

使用 abstract command 读取 `s0`：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `command` | `size=2, transfer, 0x1008` | Read `s0` |
| Read | `data0` | - | 返回原来在 `s0` 中的值 |

使用 abstract command 写 `mstatus`：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `data0` | new value |  |
| Write | `command` | `size=2, transfer, write, 0x300` | Write `mstatus` |

### B.6.2 Using Program Buffer

Abstract command 用于与 GPR 交换 data。使用该机制，可以通过把其他 register 的值移动到/移出 GPR 来访问它们。

使用 program buffer 写 `mstatus`：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `csrw s0, MSTATUS` |  |
| Write | `progbuf1` | `ebreak` |  |
| Write | `data0` | new value |  |
| Write | `command` | `size=2, postexec, transfer, write, 0x1008` | 写 `s0`，然后执行 program buffer |

使用 program buffer 读取 `f1`：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `fmv.x.s s0, f1` |  |
| Write | `progbuf1` | `ebreak` |  |
| Write | `command` | `postexec` | 执行 program buffer |
| Write | `command` | `transfer, 0x1008` | read `s0` |
| Read | `data0` | - | 返回原来在 `f1` 中的值 |

## B.7 Reading Memory

### B.7.1 Using System Bus Access

使用 system bus access 从 memory 读取一个 word：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `sbaddress0` | address |  |
| Write | `sbcs` | `sbaccess=2, sbsingleread` | 执行 read |
| Read | `sbdata0` | - | 从 memory 读取的值 |

使用 system bus access 读取 memory block：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `sbaddress0` | address |  |
| Write | `sbcs` | `sbaccess=2, sbsingleread, sbautoread, sbautoincrement` | 打开 autoread 和 autoincrement，并执行 read |
| Read | `sbdata0` | - | 从 memory 读取的值 |
| Read | `sbdata0` | - | 从 memory 读取的下一个值 |
| ... | ... | ... | ... |
| Write | `sbcs` | 0 | 清除 `sbautoread` |
| Read | `sbdata0` | - | 取得从 memory 读取的最后一个值 |

### B.7.2 Using Program Buffer

使用 program buffer 从 memory 读取一个 word：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `lw s0, 0(s0)` |  |
| Write | `progbuf1` | `ebreak` |  |
| Write | `data0` | address |  |
| Write | `command` | `write, postexec, 0x1008` | 写 `s0`，然后执行 program buffer |
| Write | `command` | `0x1008` | 读 `s0` |
| Read | `data0` | - | 从 memory 读取的值 |

使用 program buffer 读取 memory block：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `lw s1, 0(s0)` |  |
| Write | `progbuf1` | `addi s0, s0, 4` |  |
| Write | `progbuf2` | `ebreak` |  |
| Write | `data0` | address |  |
| Write | `command` | `write, postexec, 0x1008` | 写 `s0`，然后执行 program buffer |
| Write | `command` | `postexec, 0x1009` | 读 `s1`，然后执行 program buffer |
| Write | `abstractauto` | `autoexecdata[0]` | 设置 `autoexecdata[0]` |
| Read | `data0` | - | 取得从 memory 读取的值，然后执行 program buffer |
| Read | `data0` | - | 取得从 memory 读取的下一个值，然后执行 program buffer |
| ... | ... | ... | ... |
| Write | `abstractauto` | 0 | 清除 `autoexecdata[0]` |
| Read | `data0` | - | 取得从 memory 读取的最后一个值 |

表 B.1 展示使用该方法读取单个 word 时，调试器需要经历的典型 scan 序列。

表 B.1：Memory Read Timeline

| JTAG State | Activity |
|---|---|
| Shift-DR / Update-DR | 写入 `command`，请求执行 access register 或 program buffer |
| Run-Test/Idle | 等待 DM 完成 abstract command 或 program buffer 执行 |
| Shift-DR / Update-DR | 读取 `abstractcs`，检查 `busy` 与 `cmderr` |
| Shift-DR / Update-DR | 读取 `data0`，取得目标 memory word |

## B.8 Writing Memory

### B.8.1 Using System Bus Access

使用 system bus access 向 memory 写一个 word：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `sbaddress0` | address |  |
| Write | `sbdata0` | value |  |

使用 system bus access 写 memory block：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `sbaddress0` | address |  |
| Write | `sbcs` | `sbaccess=2, sbautoincrement` | 打开 autoincrement |
| Write | `sbdata0` | value0 |  |
| Write | `sbdata0` | value1 |  |
| ... | ... | ... | ... |
| Write | `sbdata0` | valueN |  |

### B.8.2 Using Program Buffer

使用 program buffer 向 memory 写一个 word：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `sw s1, 0(s0)` |  |
| Write | `progbuf1` | `ebreak` |  |
| Write | `data0` | value |  |
| Write | `command` | `write, 0x1008` | 写 `s0` |
| Write | `data0` | address |  |
| Write | `command` | `write, postexec, 0x1009` | 写 `s1`，然后执行 program buffer |

使用 program buffer 写 memory block：

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `sw s1, 0(s0)` |  |
| Write | `progbuf1` | `addi s0, s0, 4` |  |
| Write | `progbuf2` | `ebreak` |  |
| Write | `data0` | address |  |
| Write | `command` | `write, 0x1008` | 写 `s0` |
| Write | `data0` | value0 |  |
| Write | `command` | `write, postexec, 0x1009` | 写 `s1`，然后执行 program buffer |
| Write | `abstractauto` | `autoexecdata[0]` | 设置 `autoexecdata[0]` |
| Write | `data0` | value1 |  |
| ... | ... | ... | ... |
| Write | `data0` | valueN |  |
| Write | `abstractauto` | 0 | 清除 `autoexecdata[0]` |

## B.9 Handling Exceptions

通常 debugger 可以通过小心编写程序来避免 exception。但有时 exception 不可避免，例如用户要求访问未实现的 memory 或 CSR。典型 debugger 对平台了解不足，无法预知会发生什么，必须尝试访问以确定结果。

当执行 Program Buffer 时发生 exception，`cmderr` 会置位。debugger 可以检查该字段以查看 program 是否遇到 exception。如果发生 exception，则由 debugger 自己判断原因。

## B.10 Quick Access

为了执行单次 memory write，把 hart halt 最短时间。

有多种 instruction 可在 GPR 与 data register 之间传输 data。它们要么是 load/store，要么是 CSR read/write。具体地址也各不相同。这些都由 `hartinfo` 指定。这里的示例使用 pseudo-op `transfer dest, src` 表示所有这些选项。

| Op | Address | Value | Comment |
|---|---|---|---|
| Write | `progbuf0` | `transfer arg2, s0` | 保存 `s0` |
| Write | `progbuf1` | `transfer s0, arg0` | 读取第一个参数（address） |
| Write | `progbuf2` | `transfer arg0, s1` | 保存 `s1` |
| Write | `progbuf3` | `transfer s1, arg1` | 读取第二个参数（data） |
| Write | `progbuf4` | `sw s1, 0(s0)` |  |
| Write | `progbuf5` | `transfer s1, arg0` | 恢复 `s1` |
| Write | `progbuf6` | `transfer s0, arg2` | 恢复 `s0` |
| Write | `progbuf7` | `ebreak` |  |
| Write | `data0` | address |  |
| Write | `data1` | data |  |
| Write | `command` | `0x10000000` | 执行 quick access |

# 附录 C Future Ideas

本节中的所有项目都是未来想法，不应视为规范的一部分。

本规范的某个未来版本可能实现以下一些特性：

1. 规范定义若干 Device Tree 增补项，使 debugger 能发现系统中所有 core 的 hart ID 和受支持 trigger。
2. DTM 可以作为通用 bus slave 工作，因此对 bus master 来说它们看起来像普通 RAM。
3. hart 可以被划分为 group。同一 group 中的所有 hart 可同时 halted/run/stepped。当一个 hart 命中 breakpoint，同一 group 中所有其他 hart 也在几个 clock cycle 内 halt。
4. 为 USB、I2C、SPI 和 SWD 等协议规定 DTM。
5. 可以不 halt processor 而读取 core register。
6. debugger 可以与 power manager 通信，使 core 上电或下电，并查询它们的状态。
7. 当 send/receive queue 变 full/empty 时，serial port 可以 raise interrupt。
8. debug interrupt 可以被 running code masked。如果 interrupt 被 asserted、deasserted、然后再次 asserted，debug interrupt 仍会发生。该机制可用于例如以最小中断读写 memory，并确保绝不在关键代码片段期间中断。
9. debugger 可以非侵入式地从任何 running hart 采样 recent PC value。
10. Debug Module 可以包含 serial interface，用于把 DTM interface 复用为通用通信接口。

## C.1 Serial Ports

Debug Module 可以实现最多 8 个 serial port。它们支持基本 flow control 和 component 与 debugger 之间的 full duplex data transfer，本质上允许 Debug Transport 用于与 hart 上运行的 debug monitor 通信，或更一般地 emulate 不存在的 device。所有这些用途都需要软件支持，本文不进一步规定。规范只定义 Debug Module serial register 的 DMI 侧，因为 core 侧 interface 应看起来像 peripheral device。

表 C.1：Debug Module Debug Bus Registers

| Address | Name |
|---|---|
| `0x34` | Serial Control and Status |
| `0x35` | Serial TX Data |
| `0x36` | Serial RX Data |

### C.1.1 Serial Control and Status (`sercs`, at `0x34`)

如果 `serialcount` 为 0，则该寄存器不存在。

| Field | Description | Access | Reset |
|---|---|---|---|
| `serialcount` | 支持的 serial port 数量。 | R | Preset |
| `serial` | 选择由 `serrx` 和 `sertx` 访问的 serial port。 | R/W | 0 |
| `error0` | 当 serial port 0 的 debugger-to-core queue over/underflow 时为 1。该 bit 保持置位，直到向它写 1 reset。 | R/W1C | 0 |
| `valid0` | 当 serial port 0 的 core-to-debugger queue 非空时为 1。 | R | 0 |
| `full0` | 当 serial port 0 的 debugger-to-core queue 为 full 时为 1。 | R | 0 |

### C.1.2 Serial TX Data (`sertx`, at `0x35`)

如果 `serialcount` 为 0，则该寄存器不存在。

该寄存器提供对 `sercs` 中 `serial` 所选 serial port 的 write data queue 的访问。如果 error bit 未设置且 queue 未 full，则写该寄存器会把写入 data 添加到 core-to-debugger queue。否则设置 error bit，并且 write 返回 error。

读该寄存器返回最后写入的 data。字段为 `data[31:0]`。

### C.1.3 Serial RX Data (`serrx`, at `0x36`)

如果 `serialcount` 为 0，则该寄存器不存在。

该寄存器提供对 `sercs` 中 `serial` 所选 serial port 的 read data queue 的访问。如果 error bit 未设置且 queue 非空，则从该寄存器读取会读取 debugger-to-core queue 中最旧 entry，并从 queue 移除该 entry。否则设置 error bit，并且 read 返回 error。

整个寄存器只读。字段为 `data[31:0]`。

# 附录 D Change Log

| Revision | Date | Author(s) | Description |
|---|---|---|---|
| `f7f3277` | 2017-11-28 | Megan Wachs | 合并 pull request #183：来自 `riscv/c_ebreak`。 |
| `afda8d7` | 2017-11-28 | mwachs5 | 更新 PDF。 |
| `134d310` | 2017-11-28 | Megan Wachs | 修正 compressed version of `ebreak`。 |
| `6c7d031` | 2017-11-27 | Megan Wachs | 合并 pull request #179：来自 `riscv/step_corners`。 |
| `caa1258` | 2017-11-27 | Megan Wachs | `badaddr` 到 `tval`（Priv Spec 1.9 到 1.9.1）。 |
| `32b0f08` | 2017-11-22 | Tim Newsome | 纳入反馈。 |
| `2f7aa54` | 2017-11-22 | Tim Newsome | 简化并解释 trigger behavior。 |
| `3e5887f` | 2017-11-21 | Tim Newsome | 澄清一些 single step corner case。 |
| `f4b9ae2` | 2017-11-21 | Tim Newsome | 使 `ackhavereset` write-only（#178）。 |
| `efe3dc8` | 2017-11-21 | Tim Newsome | 使 `hartreset` 为 R/W（#177）。 |
| `ce1b359` | 2017-11-17 | Megan Wachs | reset 澄清（#172）。 |
| `f49bf1d` | 2017-11-16 | Tim Newsome | 合并来自 `riscv/context` 的 pull request #174。 |
| `852a70d` | 2017-11-16 | Megan Wachs | `icount`：移除 warning（#173）。 |
| `363348f` | 2017-11-16 | Tim Newsome | 解释 cache coherency 与 system bus access 的关系（#171）。 |
| `26ea898` | 2017-11-15 | Tim Newsome | 引用 ISA 和 privileged 文档。 |
| `e803d67` | 2017-11-03 | Tim Newsome | 合并来自 `riscv/index` 的 pull request #170。 |
| `ffc8c62` | 2017-11-03 | Tim Newsome | 在 “about this doc” 中提到 index。 |
| `a4257ef` | 2017-11-02 | Tim Newsome | 向文档添加 index。 |
| `f5f45a5` | 2017-10-30 | Megan Wachs | 添加 “has reset” status 和 control（#168）。 |
| `46f3f54` | 2017-10-25 | Tim Newsome | 纳入 review feedback。 |
| `104247f` | 2017-10-24 | Megan Wachs | 更新 README.md。 |
| `cb1a847` | 2017-10-24 | Megan Wachs | 在 README 中添加关于 built PDF 的注释。 |
| `e00625f` | 2017-10-18 | Tim Newsome | include PDF。 |
| `c23e729` | 2017-10-18 | Tim Newsome | 进一步澄清。 |
| `83f9faf` | 2017-10-11 | Tim Newsome | 澄清 `impebreak` 做什么。 |
| `0378324` | 2017-10-11 | mwachs5 | 添加 legend 并更新 Abstract Command State Machine diagram 的若干 transition。 |
| `fa2b600` | 2017-10-11 | Megan Wachs | 添加缺失句点。 |
| `0610630` | 2017-10-11 | Megan Wachs | 简单执行 `hmode` 到 `dmode` replacement。 |
| `16e11f3` | 2017-10-11 | Tim Newsome | 移除 `hmode` reference 以修复 build。 |
| `84b9a6a` | 2017-10-11 | Tim Newsome | 添加 `impebreak`，以支持 implicit `ebreak`。 |
| `cc90b77` | 2017-10-11 | mwachs5 | 从 figure 移除对 `H` mode 的 reference。 |
| `cc6a9de` | 2017-10-11 | Megan Wachs | 把旧 `hmode` reference 改为 `dmode`。 |
| `ea2877d` | 2017-10-10 | Tim Newsome | 把 how-to-debug 移到相关 section。 |
| `48f437b` | 2017-10-06 | Megan Wachs | 合并 unsupported access size 相关 pull request。 |
| `812686d` | 2017-10-06 | Tim Newsome | 合并 reset 相关 pull request。 |
| `486ecc6` | 2017-10-05 | Tim Newsome | 拒绝 unsupported bus access。 |
| `6ca221d` | 2017-10-05 | Tim Newsome | `haltreq`、`resumereq`、`hartreset` 是 per-hart bit。 |
| `d4118ab` | 2017-09-30 | Tim Newsome | `ndmreset` 不能 reset 访问 DM 所需逻辑。 |
| `c6bd8d1` | 2017-09-29 | Tim Newsome | `and` 到 `or`。 |
| `58c2441` | 2017-09-29 | Tim Newsome | 在 Single Step 中提到 `stepie`。 |
| `94c5f78` | 2017-09-29 | Tim Newsome | 澄清 `ndmreset`。 |
| `12810b4` | 2017-09-29 | Tim Newsome | 澄清 `sbaddress` 是 physical。 |
| `5862fdf` | 2017-09-29 | Tim Newsome | 统一 M mode 和 `mprv` 注释。 |
| `aea1bd5` | 2017-09-29 | Tim Newsome | 定义 `haltreq` 和 `resumereq` 同时设置时的行为。 |
| `052a8ab` | 2017-09-28 | Tim Newsome | 澄清 debugger 可能失去 hart 控制。 |
| `cc52cff` | 2017-09-28 | Tim Newsome | 添加 `dmerr`。 |
| `25685eb` | 2017-09-28 | Tim Newsome | 解释 bus master 或 `progbuf` 是必需的。 |
| `f75ee7d` | 2017-09-28 | Tim Newsome | 澄清 debugger 可以发现“几乎”全部内容。 |
| `71e6788` | 2017-09-27 | Tim Newsome | 移除 manual stepping 描述。 |
| `9aea347` | 2017-09-27 | Tim Newsome | 把 Running/Single Step 移到 Halting 附近。 |
| `2090d9b` | 2017-09-27 | Tim Newsome | 表中 `data0` 应为 `sbdata0`。 |
| `5858cfe` | 2017-09-27 | Tim Newsome | 澄清为什么存在 `priv`。 |
| `bc3c2aa` | 2017-09-27 | Tim Newsome | 提到 `priv` encoding 来自何处。 |
| `ef77cc4` | 2017-09-27 | Tim Newsome | 再次尝试澄清 single step 后的 DPC。 |
| `80a288e` | 2017-09-27 | Tim Newsome | 澄清在 `ebreak` 上 `instret` 不递增。 |
| `c163d22` | 2017-09-20 | Tim Newsome | 移除 `ebreakh`。 |
| `9971075` | 2017-09-20 | Tim Newsome | 澄清讨论的是 privilege。 |
| `3684854` | 2017-09-20 | Tim Newsome | 在 `sbdata0` 中使用 steps environment。 |
| `d4eda18` | 2017-09-20 | Tim Newsome | 解释只有 `sbdata0` 有副作用。 |
| `ae781c6` | 2017-09-20 | Tim Newsome | 不引用 internal system bus register。 |
| `875922e` | 2017-09-20 | Tim Newsome | 进一步解释 `sbdata0` stale。 |
| `cd44fd5` | 2017-09-20 | Tim Newsome | 澄清 autoread。 |
| `194484b` | 2017-09-20 | Tim Newsome | 澄清 `hawindow`。 |
| `02f1aac` | 2017-09-20 | Tim Newsome | 澄清 `dataaddr` 是 relative to zero。 |
| `0e9b6ae` | 2017-09-20 | Tim Newsome | 澄清 nonexistent 与 unavailable。 |
| `b55ff41` | 2017-09-20 | Tim Newsome | 修复 `devtreevalid`。 |
| `2eccb86` | 2017-09-20 | Tim Newsome | 明确说明哪些 register 是 read-only。 |
| `4af505c` | 2017-09-20 | Tim Newsome | 为 register 显示 section number。 |
| `19c206f` | 2017-09-20 | Tim Newsome | 澄清如何确定 `progbuf` 是否为 RAM。 |
| `0651f7d` | 2017-09-20 | Tim Newsome | 解释缺少 `ebreak` 时发生什么。 |
| `e889dae` | 2017-09-20 | Tim Newsome | 把 state figure 移到自己的 section。 |
| `cff7b80` | 2017-09-20 | Tim Newsome | 解释什么时候可能使用 `transfer`。 |
| `6b2ee61` | 2017-09-20 | Tim Newsome | 解释 `size` encoding 来源。 |
| `c9f3b73` | 2017-09-14 | Tim Newsome | 修复 typo。 |
| `4b25400` | 2017-09-13 | Tim Newsome | 在 CSR abstract register numbers 中提到 `dpc`。 |
| `c3ee426` | 2017-09-13 | Tim Newsome | 把 abstract `regno` table 移到更靠近其引用处。 |
| `111b9a3` | 2017-09-13 | Tim Newsome | `cycle` 到 `operation`。 |
| `994afdc` | 2017-09-13 | Tim Newsome | 考虑多个选中 hart。 |
| `aa4a297` | 2017-09-13 | Tim Newsome | Halt Control 到 Run Control。 |
| `e97c821` | 2017-09-13 | Tim Newsome | `continuous` 到 `contiguous`。 |
| `97f73ff` | 2017-09-13 | Tim Newsome | 澄清 `ndmreset` behavior。 |
| `6078220` | 2017-09-13 | Tim Newsome | 解释 `ndmreset`。 |
| `a3d4f30` | 2017-09-13 | Tim Newsome | 描述 halt region。 |
| `272b3d9` | 2017-09-13 | Tim Newsome | 澄清访问 unimplemented DM DMI register。 |
| `3e91f1b` | 2017-09-13 | Tim Newsome | 澄清 Prog Buf 或 Sys Bus Acc 二者之一是必需的。 |
| `e8a6145` | 2017-09-13 | Tim Newsome | 澄清 CSR access；移除 serial port。 |
| `1195a61` | 2017-09-18 | Tim Newsome | 为 clang 生成 unsigned constants。 |
| `8967b0a` | 2017-08-16 | Megan Wachs | compressed instruction 是 `c.foo`，不是 `foo.c`。 |
| `b5698a9` | 2017-08-16 | Megan Wachs | 澄清 `progbufsize` description。 |
| `d221bab` | 2017-08-16 | Megan Wachs | 从 register description 移除 `progbufsize` enum。 |
| `0498102` | 2017-08-16 | Megan Wachs | appendix：对 `sw` 使用 standard assembly format。 |
| `4e51a25` | 2017-08-10 | Tim Newsome | 合并 `trigsign` 相关 pull request。 |
| `4456d99` | 2017-08-09 | Tim Newsome | Rename `progsize` to `progbufsize`。 |
| `55d5b66` | 2017-08-09 | Tim Newsome | 澄清 trigger comparison 是 unsigned。 |
| `21e35ef` | 2017-08-09 | Tim Newsome | Configuration String 到 Device Tree。 |
| `f044f45` | 2017-08-02 | Tim Newsome | 不要求 target 在 VCC 上提供 25mA。 |
| `c883943` | 2017-08-02 | Tim Newsome | 添加 Abstract Command Type 表。 |
| `95b9108` | 2017-08-02 | mwachs5 | DTM：澄清不存在 DMI 实际返回 error 的情形。 |
| `9c9e0c0` | 2017-08-02 | mwachs5 | SystemBus 不再返回 error，因此 DMI 没有 `error` return code。 |
| `5ba18f9` | 2017-07-27 | Tim Newsome | 修复更多 typo。 |
| `dbc65bf` | 2017-07-26 | Tim Newsome | 修复 typo。 |
| `bba0ad9` | 2017-07-26 | Tim Newsome | 收紧 introduction list。 |
| `e22d5eb` | 2017-07-26 | Tim Newsome | 为 “not compatible” 添加 version constant。 |
| `c79038e` | 2017-07-26 | Tim Newsome | 小澄清。 |
| `9df0411` | 2017-07-21 | Tim Newsome | 纳入 review feedback。 |
| `d67419c` | 2017-07-21 | Tim Newsome | 澄清 `dpc` contents。 |
| `0e707f1` | 2017-07-11 | Megan Wachs | 合并 quick access errors 相关 pull request。 |
| `65d596e` | 2017-07-11 | Megan Wachs | 合并 error halt resume 相关 pull request。 |
| `9f50c05` | 2017-07-11 | Tim Newsome | 使用 LL 而不是 L 作为 64-bit constant suffix。 |
| `23fd24a` | 2017-07-10 | Megan Wachs | 清理 whitespace。 |
| `cf6e3f2` | 2017-07-10 | Megan Wachs | 澄清 `DCSR.cause`。 |
| `79ffbb9` | 2017-07-10 | Megan Wachs | 澄清 CSR read、write、halt 的影响。 |
| `013e191` | 2017-07-10 | Megan Wachs | 澄清什么时候会得到 error halt/resume。 |
| `231e457` | 2017-07-10 | Megan Wachs | Quick Access error 澄清。 |
| `6defcb8` | 2017-07-03 | mwachs5 | serial：把 serial port 从 main spec 移到 Future Work appendix。 |
| `3541152` | 2017-07-03 | Megan Wachs | 合并 remove trace 相关 pull request。 |
| `52a122b` | 2017-06-30 | mwachs5 | 移除 trace section。 |
| `d9e166b` | 2017-06-30 | mwachs5 | 移除 trace register。 |
| `7caf4e5` | 2017-06-30 | mwachs5 | 移除 trace appendix。 |
