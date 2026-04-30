# 第 4 章 RISC-V Debug

为支持 debug 而对 RISC-V core 做出的修改保持最小。有一种特殊执行模式（Debug Mode）和少量额外 CSR。其余部分由 DM 处理。

## 4.1 Debug Mode

Debug Mode 是一种特殊 processor mode，仅在 core 为外部调试而 halted 时使用。这里不规定 Debug Mode 如何实现。

从 Program Buffer 执行代码时，processor 保持在 Debug Mode，并适用以下规则：

1. 所有操作都以 machine mode privilege level 执行，但 `mstatus` 中的 `mprv` 被忽略。
2. 所有 interrupt 都被 masked。
3. exception 不更新任何 register，包括 `cause`、`epc`、`tval`、`dpc` 和 `mstatus`。它们会结束 Program Buffer 的执行。
4. 如果 trigger 匹配，不采取任何动作。
5. trace 被 disabled。
6. counter 可以停止，取决于 `dcsr` 中的 `stopcount`。
7. timer 可以停止，取决于 `dcsr` 中的 `stoptime`。
8. `wfi` instruction 表现为 `nop`。
9. 几乎所有改变 privilege level 的 instruction 行为都未定义。这包括 `ecall`、`mret`、`hret`、`sret` 和 `uret`。（要改变 privilege level，debugger 可以写 `dcsr` 中的 `prv`。）唯一例外是 `ebreak`。在 Debug Mode 中执行 `ebreak` 时，它会再次 halt processor，但不更新 `dpc` 或 `dcsr`。

## 4.2 Load-Reserved/Store-Conditional Instructions

由 `lr` instruction 在某个 memory address 上登记的 reservation，可能在进入 Debug Mode 或处于 Debug Mode 时丢失。这意味着，如果在 `lr` 和 `sc` 对之间进入 Debug Mode，可能没有 forward progress。

## 4.3 Single Step

debugger 可以通过在设置 `resumereq` 前设置 `step`，使 halted hart 执行单条指令，然后重新进入 Debug Mode。

如果执行或取该指令导致 exception，则在 PC 改为 exception handler 且相应 `tval` 和 `cause` register 更新后，立即重新进入 Debug Mode。

如果执行或取该指令导致 trigger fire，则在该 trigger 已 fire 后立即重新进入 Debug Mode。在这种情况下，`cause` 设置为 2（trigger），而不是 4（single step）。该指令是否执行取决于 trigger 的具体配置。

如果执行的指令导致 PC 改到某个地址，而在该地址进行 instruction fetch 会导致 exception，则该 exception 直到 hart 下一次 resume 时才发生。类似地，新地址处的 trigger 直到 hart 实际尝试执行该指令时才 fire。

## 4.4 Reset

当 hart 脱离 reset 时，如果 halt signal（由 Debug Module 中该 hart 的 halt request bit 驱动）被 asserted，则 hart 必须在执行任何指令前进入 Debug Mode，但要在执行第一条指令前通常会发生的任何初始化之后进入。

### 4.4.1 `dret` Instruction

为了从 Debug Mode 返回，定义一条新指令：`dret`。其编码为 `0x7b200073`。

在支持该指令的 hart 上，在 Debug Mode 中执行 `dret` 会把 `pc` 改为 `dpc` 中存储的值。当前 privilege level 改为 `dcsr` 中 `prv` 指定的级别。hart 不再处于 debug mode。

debugger 不需要知道某个实现是否支持 `dret`，因为 Debug Module 会确保在必要时执行它。本规范定义它只是为了保留 opcode，并允许可复用的 Debug Module 实现。

## 4.5 Core Debug Registers

每个可调试 hart 必须实现受支持的 Core Debug Register。这些寄存器只能从 Debug Mode 访问。

表 4.1：Core Debug Registers

| Address | Name |
|---|---|
| `0x7b0` | Debug Control and Status |
| `0x7b1` | Debug PC |
| `0x7b2` | Debug Scratch Register 0 |
| `0x7b3` | Debug Scratch Register 1 |

### 4.5.1 Debug Control and Status (`dcsr`, at `0x7b0`)

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `xdebugver` | 0：没有 external debug support。4：存在本文档描述的 external debug support。15：存在 external debug support，但不符合本规范任何可用版本。 | R | Preset |
| `ebreakm` | 为 1 时，Machine Mode 中的 `ebreak` instruction 进入 Debug Mode。 | R/W | 0 |
| `ebreaks` | 为 1 时，Supervisor Mode 中的 `ebreak` instruction 进入 Debug Mode。 | R/W | 0 |
| `ebreaku` | 为 1 时，User/Application Mode 中的 `ebreak` instruction 进入 Debug Mode。 | R/W | 0 |
| `stepie` | 0：single stepping 期间 interrupt disabled。1：single stepping 期间 interrupt enabled。实现可以把该 bit hard wire 为 0。debugger 必须读回写入值，以检查是否支持该特性。若不支持，interrupt behavior 可由 debugger emulate。 | R/W | 0 |
| `stopcount` | 0：counter 照常递增。1：处于 Debug Mode 时，或导致进入 Debug Mode 的 `ebreak` instruction 上，不递增任何 counter。这些 counter 包括 `cycle` 和 `instret` CSR。对大多数调试场景这是首选。实现可以选择不支持写该 bit；debugger 必须读回写入值以检查是否支持。 | R/W | Preset |
| `stoptime` | 0：timer 照常递增。1：Debug Mode 中不递增任何 hart-local timer。实现可以选择不支持写该 bit；debugger 必须读回写入值以检查是否支持。 | R/W | Preset |
| `cause` | 说明进入 Debug Mode 的原因。当一个 cycle 中有多个进入 Debug Mode 的原因时，写入最高优先级的 cause。1：执行了 `ebreak` instruction（priority 3）。2：Trigger Module 导致 breakpoint exception（priority 4）。3：debugger 请求进入 Debug Mode（priority 2）。4：由于 `step` 被设置，hart single stepped（priority 1）。其他值保留供未来使用。 | R | 0 |
| `step` | 置位且不在 Debug Mode 中时，hart 只执行单条指令，然后进入 Debug Mode。如果该指令因 exception 而未完成，则 hart 会在执行 trap handler 前立即进入 Debug Mode，并设置相应 exception register。 | R/W | 0 |
| `prv` | 包含进入 Debug Mode 时 hart 正在运行的 privilege level。编码见表 4.4。debugger 可以改变该值，以改变离开 Debug Mode 时 hart 的 privilege level。并非所有 hart 都支持所有 privilege level。如果写入的编码不受支持，或 debugger 不允许切换到该级别，hart 可以切换到任何受支持 privilege level。 | R/W | 0 |

### 4.5.2 Debug PC (`dpc`, at `0x7b1`)

进入 debug mode 时，`dpc` 被更新为下一条将执行指令的 virtual address。行为详见表 4.2。

表 4.2：进入 Debug Mode 时 DPC 中的虚拟地址

| Cause | Virtual Address in DPC |
|---|---|
| `ebreak` | `ebreak` instruction 的地址。 |
| single step | 若没有调试本应接下来执行的指令地址。例如，对不改变 program flow 的 32-bit instruction 为 `pc + 4`，对 taken jump/branch 为目标 PC，等等。 |
| trigger module | 若 `timing` 为 0，则为导致 trigger fire 的 instruction 地址。若 `timing` 为 1，则为进入 debug mode 时下一条要执行的 instruction 地址。 |
| halt request | 进入 debug mode 时下一条要执行的 instruction 地址。 |

resume 时，hart 的 PC 被更新为 `dpc` 中存储的 virtual address。debugger 可以写 `dpc` 以改变 hart resume 的位置。字段为 `dpc[XLEN-1:0]`。

### 4.5.3 Debug Scratch Register 0 (`dscratch0`, at `0x7b2`)

可选 scratch register，可由需要它的实现使用。除非 `hartinfo` 明确提到它，否则 debugger 不得写该寄存器（Debug Module 可在内部使用该寄存器）。

### 4.5.4 Debug Scratch Register 1 (`dscratch1`, at `0x7b3`)

可选 scratch register，可由需要它的实现使用。除非 `hartinfo` 明确提到它，否则 debugger 不得写该寄存器（Debug Module 可在内部使用该寄存器）。

## 4.6 Virtual Debug Registers

Virtual debug register 是对 debugger software/interface 的要求，不是对 Core designer 的要求。debugger 的用户不应需要了解 core debug register，但可能希望改变受它们影响的事物。virtual register 并不直接存在于硬件中，而是 debugger 像它存在一样向外暴露。

表 4.3：Virtual Core Debug Registers

| Address | Name |
|---|---|
| virtual | Privilege Level |

### 4.6.1 Privilege Level (`priv`, at virtual)

用户可以读取该寄存器，以检查 hart halted 时正在运行的 privilege level。用户可以写该寄存器，以改变 hart resume 时将运行的 privilege level。

该寄存器包含 `dcsr` 中的 `prv`，但位于期望用户访问的位置。用户不应直接访问 `dcsr`，因为这样可能干扰 debugger。

表 4.4：Privilege Level Encoding

| Encoding | Privilege Level |
|---|---|
| 0 | User/Application |
| 1 | Supervisor |
| 3 | Machine |

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `prv` | 包含进入 Debug Mode 时 hart 正在运行的 privilege level。编码见表 4.4，并匹配 RISC-V Privileged ISA Specification 中的 privilege level encoding。用户可以写该值以改变离开 Debug Mode 时 hart 的 privilege level。 | R/W | 0 |
