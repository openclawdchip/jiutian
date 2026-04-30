# 第 1 章 Introduction

当一个设计从仿真推进到硬件实现时，用户对系统当前状态的控制能力和理解程度会急剧下降。为了 bring-up 并调试底层软件和硬件，在硬件中内建良好的调试支持至关重要。当一个健壮的 OS 在 core 上运行时，软件可以处理许多调试任务。然而，在许多场景下，硬件支持是必不可少的。

本文档概述 RISC-V 平台上的外部调试支持标准架构。该架构允许多种实现和取舍，这与 RISC-V 实现范围广泛的特点相互补充。同时，本规范定义公共接口，使调试工具和组件能够面向多种基于 RISC-V ISA 的平台。

系统设计者可以选择增加额外的硬件调试支持，但本规范为通用功能定义标准接口。

## 1.1 Terminology

platform 是一个由一个或多个组件组成的单个集成电路。有些组件可能是 RISC-V core，另一些组件可能具有不同功能。通常，它们都会连接到一条系统总线。单个 RISC-V core 包含一个或多个硬件线程，称为 hart。

### 1.1.1 Context

本文档按以下文档配合使用而编写：

1. The RISC-V Instruction Set Manual, Volume I: User-Level ISA, Document Version 2.2
2. The RISC-V Instruction Set Manual, Volume II: Privileged Architecture, Version 1.10

## 1.2 About This Document

### 1.2.1 Structure

本文档包含两个部分。文档主体是规范，位于编号章节中。第二部分是一组附录。附录中的信息用于澄清和提供示例，但不属于实际规范。

### 1.2.2 Register Definition Format

本文档中的所有寄存器定义都遵循下列格式。一个简单图形展示寄存器中有哪些字段。每个字段的高、低 bit 索引显示在字段左上和右上。字段中的 bit 总数显示在字段下方。

图形之后是一张表；对于每个字段，表中列出字段名、描述、允许访问类型和 reset value。允许访问类型列在表 1.1。

表 1.1：寄存器访问缩写

| 缩写 | 含义 |
|---|---|
| R | Read-only。 |
| R/W | Read/Write。 |
| R/W0 | Read/Write。只有写 0 有效果。 |
| R/W1 | Read/Write。只有写 1 有效果。 |
| R/W1C | Read/Write。对于字段中的每个 bit，写 1 会清除该 bit；写 0 没有效果。 |
| W | Write-only。读取该字段时返回 0。 |
| W1 | Write-only。只有写 1 有效果。 |

寄存器及其 bit 的名称都是到其定义的超链接。如果正在纸面阅读，文档第 70 页有包含全部名称的索引。

#### 1.2.2.1 Long Name (`shortname`, at `0x123`)

示例寄存器图：

| bit | 字段 |
|---|---|
| 31:8 | 0 |
| 7:0 | `field` |

| Field | Description | Access | Reset |
|---|---|---|---|
| `field` | 描述该字段用途。 | R/W | 15 |

## 1.3 Background

专用调试硬件有多种用例，既包括 CPU core 内部调试硬件，也包括带外部连接的调试硬件。本规范处理下面列出的用例。实现可以选择不实现每个特性，这意味着某些用例可能不受支持。

- 在没有 OS 或其他软件的情况下调试底层软件。
- 调试 OS 本身的问题。
- 在系统中还没有任何可执行代码路径之前，对系统进行 bootstrapping，以测试、配置和编程组件。
- 在没有可工作的 CPU 的系统上访问硬件。

此外，即使没有硬件调试接口，RISC-V CPU 中的架构支持也可以通过允许硬件 trigger 和 breakpoint 来帮助软件调试和性能分析。本规范旨在定义可用于不同场景的公共资源。

在调试软件时，本规范区分两种外部调试形式。第一种是 halt mode debugging，在此模式下，外部调试器 halt 平台中的部分或全部组件，并在它们处于静止状态时检查其状态。调试器可以读取并/或修改状态，然后指示硬件执行单条指令，或者继续自由运行。

第二种是 run mode debugging。在此模式下，软件 debug agent 在某个组件上运行（例如由 RISC-V core 上的 timer interrupt 或 breakpoint 触发），它在不 halt 该组件、只短暂中断其程序流的情况下向调试器传输数据或从调试器接收数据。如果该组件正在控制某种实时系统（例如硬盘），长时间时序延迟可能造成物理损坏，那么这种功能就是必不可少的。这需要额外的软件支持（系统上和调试器上都需要），并且需要组件与调试器之间的高效通信通道。

## 1.4 Supported Features

本规范描述的 debug interface 支持以下特性：

1. 支持 RV32、RV64 和未来的 RV128。
2. 平台中的任何 hart 都可以独立调试。
3. 调试器几乎可以自行发现它需要知道的一切，不需要用户配置。
4. 每个 hart 都可以从执行的第一条指令开始被调试。
5. 当执行 software breakpoint instruction 时，RISC-V hart 可以被 halted。
6. 硬件 single-step 可以一次执行一条指令。
7. Debug 功能独立于所使用的 debug transport。
8. 调试器不需要知道正在调试的 core 的任何微架构信息。
9. 可以同时 halt 和 resume 任意 hart 子集。（可选）
10. 可以在 halted hart 上执行任意指令。这意味着，当 core 具有额外或自定义指令或状态时，只要存在能把该状态移动到 GPR 中的程序，就不需要新的 debug 功能。（可选）
11. 可以不 halt 而访问寄存器。（可选）
12. 可以指示一个 running hart 以很小开销执行一小段指令序列。（可选）
13. system bus master 允许在不涉及任何 hart 的情况下访问 memory。（可选）
14. 当 trigger 匹配 PC、读/写地址/数据或 instruction opcode 时，RISC-V hart 可以被 halted。（可选）

虽然执行任意指令的机制和 system bus master 都是可选的，但二者至少必须实现一个。否则就没有访问 memory 的机制。

本文档不建议用于硬件测试、调试或错误检测技术的策略或实现。Scan、BIST 等均超出本规范范围，但本规范无意限制它们在 RISC-V 系统中的使用。
