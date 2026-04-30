# Chapter 1 Introduction

在复杂系统中，理解程序行为并不容易。不出意外，在这类系统中，软件有时不会按预期运行。这可能由多种因素导致，例如与其他 core、软件、外设、realtime events 的交互，较差的实现，或者上述因素的某种组合。

并不总能使用 debugger 来观察运行中系统的行为，因为这具有侵入性。提供程序执行的可见性非常重要。同时，这件事需要在不以大量数据淹没系统的前提下完成。

实现这一点的一种方法是 Processor Branch Trace。

它的工作方式是从一个已知起始地址跟踪执行，并发送程序所经历的 address delta 相关消息。这些 delta 通常由 jump、call、return 和 branch 类型指令引入，不过 interrupt 和 exception 也是 delta 的类型。

从概念上看，系统包含以下一个或多个基本组件：

- 一个带有 instruction trace interface 的 core，该接口输出成功创建 processor branch trace 以及更多信息所需的全部相关信息。这是一个高带宽接口：在大多数实现中，它会在 core 的每个执行时钟周期提供大量数据，包括 instruction address、instruction type、context information 等。
- 一个连接到该 instruction trace interface 的硬件 encoder，它把这些信息压缩成较低带宽的 trace packets。
- 一个用于传输这些 trace packets 的 transmission channel，或者一个用于存储这些 trace packets 的 memory。
- 一个 decoder，通常是在外部 PC 上运行的软件，它接收 encoder 发出的 trace packets，并凭借对发起端 hart 上正在运行的 program binary 的了解来重建 program flow。这个 decoding 步骤可以离线完成，也可以在 hart 执行时实时完成。

在 RISC-V 中，所有指令都是无条件执行的，或者至少可以基于 program binary 判定它们是否执行。delta 之间的指令都可以假定为顺序执行。因此，trace 中不需要报告 sequential instructions，只需要报告 branch 是否 taken，以及 taken indirect branch 或 jump 的地址。如果 program counter 的变化量无法从 execution binary 判定，trace decoder 就需要获得 destination address，也就是下一条有效指令的地址。例如 indirect branch 或 jump，其下一条 instruction address 由寄存器内容决定，而不是由 program binary 中嵌入的常量决定。

Interrupt 通常相对于程序执行异步发生，而不是作为某条特定指令或事件的有意结果。Exception 也可以用同样方式理解，尽管它们通常可以回溯到某个特定 instruction address。decoder 通常不知道 interrupt 在指令序列中的什么位置发生，所以 trace encoder 必须报告正常 program flow 停止的位置，还要给出 asynchronous destination 的指示；这种指示可以简单到只报告 exception type。当发生 interrupt 或 exception，或者 processor 被 halted 时，之前退休的最后一条指令必须包含在 trace 中。

本文档用于规定 ingress port，即 RISC-V core 与 encoder 之间的信号、compressed branch trace algorithm，以及封装 compressed branch trace information 所使用的 packet format。

## 1.1 Terminology

以下术语在本规范中具有特定含义。

- ATB：Arm trace bus。
- branch：有条件地改变 execution flow 的指令。
- CSR：control/status register。
- decoder：一种软件，它接收 encoder 发出的 trace packets，并重建 RISC-V hart 所执行代码的 execution flow。
- delta：program counter 的一种变化，且该变化不是内存中连续放置的两条指令之间的差值。
- discontinuity：`delta` 的另一个名称。
- ELF：executable and linkable format。
- encoder：一种硬件，它从 RISC-V hart 接收 instruction execution information，并将其转换为 trace packets。
- exception：运行时在 RISC-V hart 中与某条指令相关联的异常条件。
- hart：RISC-V hardware thread。
- interrupt：外部异步事件，可能导致 RISC-V hart 发生非预期的控制转移。
- ISA：instruction set architecture。
- jump：无条件改变 execution flow 的指令。
- direct jump：通过常量值改变 PC，从而无条件改变 execution flow 的指令。
- indirect jump：通过把 PC 改为计算值，从而无条件改变 execution flow 的指令。
- inferable jump：目标地址由 jump opcode 内嵌常量提供的 jump。
- uninferable jump：不可 infer 的 jump。
- LSB：least significant bit。
- MSB：most significant bit。
- packet：encoder 发出的 encoded trace information 的原子单位。
- PC：program counter。
- program counter：包含正在执行指令地址的寄存器。
- retire：执行指令的最终阶段，此时机器状态被更新；有时也称为 `commit` 或 `graduate`。
- trap：由 exception 或 interrupt 导致的控制转移，转到 trap handler。
- updiscon：`uninferable PC discontinuity` 的缩写。

## 1.2 Nomenclature

在后续章节中，粗体项目表示 packet 内的 signal 或 field。

粗斜体项目表示 RISC-V ISA 定义的 instruction 或 CSR mnemonic。

名称以 `_p` 结尾的斜体项目表示构建到硬件中的参数，或可配置硬件值。
