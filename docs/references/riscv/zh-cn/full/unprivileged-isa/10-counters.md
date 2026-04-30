# 第 10 章 Counters

RISC-V ISA 提供最多 32 个 64-bit performance counter 和 timer。它们可通过 unprivileged XLEN read-only CSR register `0xC00`-`0xC1F` 访问（在 RV32 上，高 32 bit 通过 CSR register `0xC80`-`0xC9F` 访问）。其中前三个（`CYCLE`、`TIME` 和 `INSTRET`）具有专用功能，分别是 cycle count、real-time clock 和 instructions-retired；其余 counter 如果实现，则提供 programmable event counting。

## 10.1 Base Counters and Timers

```text
31 20 19 15 14 12 11 7 6 0
csr   rs1   funct3 rd   opcode
12    5     3      5    7

RDCYCLE[H]    0 CSRRS dest SYSTEM
RDTIME[H]     0 CSRRS dest SYSTEM
RDINSTRET[H]  0 CSRRS dest SYSTEM
```

RV32I 提供若干 64-bit read-only user-level counter，它们映射到 12-bit CSR address space，并使用 `CSRRS` 指令以 32-bit piece 访问。在 RV64I 中，CSR 指令可以操作 64-bit CSR。特别地，`RDCYCLE`、`RDTIME` 和 `RDINSTRET` pseudoinstruction 读取 `cycle`、`time` 和 `instret` counter 的完整 64 bit。因此，RV64I 不需要 `RDCYCLEH`、`RDTIMEH` 和 `RDINSTRETH` 指令。

> 某些 execution environment 可能禁止访问 counter，以阻碍 timing side-channel attack。

`RDCYCLE` pseudoinstruction 读取 `cycle` CSR 的低 XLEN bit。`cycle` CSR 保存从过去某个任意起点开始，运行该 hart 的 processor core 所执行的 clock cycle 数。`RDCYCLEH` 是 RV32I 指令，读取同一 `cycle` counter 的 bits 63-32。底层 64-bit counter 在实践中不应 overflow。`cycle` counter 增长的速率取决于实现和 operating environment。execution environment 应提供一种方式，用于确定 `cycle` counter 当前递增速率（cycles/second）。

> `RDCYCLE` 旨在返回 processor core 执行的 cycle 数，而不是 hart 执行的 cycle 数。鉴于某些实现选择（例如 AMD Bulldozer），精确定义什么是 “core” 很困难。鉴于实现范围（包括 software emulation），精确定义什么是 “clock cycle” 也很困难；但意图是把 `RDCYCLE` 与其他 performance counter 一起用于 performance monitoring。特别是在 one hart/core 的情况下，人们会期望 cycle-count/instructions-retired 衡量某个 hart 的 CPI。

> core 完全不必暴露给软件，实现者可以选择假装一个 physical core 上的多个 hart 运行在单独 core 上，呈现为 one hart/core，并为每个 hart 提供单独的 cycle counter。在简单 barrel processor 中（例如 CDC 6600 peripheral processor），如果 hart 间 timing interaction 不存在或很小，这可能是合理的。

> 当存在 more than one hart/core 且使用 dynamic multithreading 时，通常无法把 cycle 按 hart 分离（尤其是 SMT）。也许可以定义一个单独 performance counter，试图捕捉某个特定 hart 正在运行的 cycle 数，但为了覆盖所有可能的 threading implementation，该定义必须非常模糊。例如，我们是否只统计向 execution 发射了该 hart 任意指令的 cycle，和/或任意指令退休的 cycle，还是也包括该 hart 占用机器资源但由于 stall 无法执行、同时其他 hart 进入 execution 的 cycle？可能需要“以上全部”才能获得可理解的性能统计。

> 定义 per-hart cycle count 的复杂性，以及调优 multithreaded code 时无论如何都需要 total per-core cycle count，促使我们只标准化 per-core cycle counter；它也恰好适用于常见的 single hart/core 情况。

> 标准化 “sleep” 期间发生什么并不实际，因为 “sleep” 的含义在不同 execution environment 中并未标准化。不过，如果整个 core 被暂停（在 deep sleep 中完全 clock-gated 或 powered-down），那么它没有执行 clock cycle，按本规范 cycle count 不应增加。这里有许多细节，例如从 power-down event 唤醒后 reset processor 所需的 clock cycle 是否应被计数，这些被视为 execution-environment-specific 细节。

> 即使没有一个适用于所有平台的精确定义，该设施对大多数平台仍然有用；在这里，一个不精确、通用、“通常正确”的标准比没有标准更好。`RDCYCLE` 的意图主要是 performance monitoring/tuning，本规范也是以该目标为念编写的。

`RDTIME` pseudoinstruction 读取 `time` CSR 的低 XLEN bit。`time` CSR 统计从过去某个任意起点开始已经经过的 wall-clock real time。`RDTIMEH` 是仅 RV32I 的指令，读取同一 real-time counter 的 bits 63-32。底层 64-bit counter 在实践中不应 overflow。execution environment 应提供一种方式，用于确定 real-time counter 的 period（seconds/tick）。该 period 必须是常量。同一 user application 中所有 hart 的 real-time clock 应同步到 real-time clock 的一个 tick 以内。environment 应提供一种方式来确定 clock 的 accuracy。

> 在某些简单平台上，cycle count 可能是 `RDTIME` 的有效实现；但在这种情况下，平台应把 `RDTIME` 指令实现为 `RDCYCLE` 的 alias，以使代码更可移植，而不是让软件使用 `RDCYCLE` 衡量 wall-clock time。

`RDINSTRET` pseudoinstruction 读取 `instret` CSR 的低 XLEN bit。`instret` CSR 统计从过去某个任意起点开始，该 hart 退休的指令数量。`RDINSTRETH` 是仅 RV32I 的指令，读取同一 instruction counter 的 bits 63-32。底层 64-bit counter 在实践中不应 overflow。

以下代码序列会把有效的 64-bit `cycle` counter 值读入 `x3:x2`，即使 counter 在读取高半部分和低半部分之间发生低半部分 overflow 也能正确工作。

```asm
again:
    rdcycleh x3
    rdcycle  x2
    rdcycleh x4
    bne      x3, x4, again
```

图 10.1：在 RV32 中读取 64-bit cycle counter 的示例代码。

> 我们建议实现提供这些基础 counter，因为它们对基本 performance analysis、adaptive and dynamic optimization，以及允许 application 与 real-time stream 协作是必不可少的。还应提供额外 counter 以帮助诊断性能问题，并且这些 counter 应以低开销从 user-level application code 访问。

> 我们要求 counter 即使在 RV32 上也为 64 bit 宽，因为否则软件很难判断值是否 overflow。对于 low-end implementation，每个 counter 的高 32 bit 可以使用 software counter 实现，并由低 32 bit overflow 触发的 trap handler 递增。上面描述的示例代码展示了如何使用单独 32-bit 指令安全读取完整 64-bit 宽值。

> 在某些应用中，能够在同一瞬间读取多个 counter 很重要。在 multitasking environment 下运行时，user thread 在尝试读取 counter 时可能发生 context switch。一种解决方案是，user thread 在读取其他 counter 之前和之后读取 real-time counter，以判断该序列中间是否发生 context switch；如果发生，则可以重试读取。我们考虑过增加 output latch，让 user thread 可以原子地 snapshot counter value，但这会增加 user context 大小，尤其对于具有更丰富 counter 集合的实现。

## 10.2 Hardware Performance Counters

CSR space 中为 29 个额外 unprivileged 64-bit hardware performance counter 分配了空间，即 `hpmcounter3`-`hpmcounter31`。对于 RV32，这些 performance counter 的高 32 bit 可通过额外 CSR `hpmcounter3h`-`hpmcounter31h` 访问。这些 counter 统计 platform-specific event，并通过额外 privileged register 配置。这些额外 counter 的数量和宽度，以及它们统计的 event 集合，都是 platform-specific 的。

privileged architecture manual 描述了控制这些 counter 访问权限以及设置要统计 event 的 privileged CSR。

> 最终标准化 event setting 会很有用，例如统计 ISA-level metric（如执行的 floating-point instruction 数量），也可能包括少数常见 microarchitectural metric，例如 “L1 instruction cache misses”。
