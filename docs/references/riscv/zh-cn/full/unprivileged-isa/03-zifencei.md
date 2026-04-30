# 第 3 章 `Zifencei` Instruction-Fetch Fence，版本 2.0

本章定义 `Zifencei` 扩展。该扩展包含 `FENCE.I` 指令，用于在同一 hart 上，显式同步对 instruction memory 的写入与 instruction fetch。目前，该指令是唯一的标准机制，用于确保对某个 hart 可见的 store，也会对该 hart 的 instruction fetch 可见。

> 我们考虑过但没有加入 “store instruction word” 指令（如 MAJC 中的做法）。JIT compiler 可以在一次 `FENCE.I` 之前生成很长的 instruction trace，并通过把翻译后的指令写入已知不驻留在 I-cache 中的 memory region，来摊销任何 instruction cache snooping/invalidation 开销。

> `FENCE.I` 指令设计为支持范围广泛的实现。简单实现可以在执行 `FENCE.I` 时 flush 本地 instruction cache 和 instruction pipeline。更复杂的实现可以在每次 data cache miss 时 snoop instruction cache，或在每次 instruction cache miss 时 snoop data cache；也可以使用 inclusive unified private L2 cache，在本地 store instruction 正在写入某些 line 时，使 primary instruction cache 中的这些 line 失效。如果 instruction cache 和 data cache 以这种方式保持 coherent，或者 memory system 仅由 uncached RAM 组成，那么 `FENCE.I` 只需要 flush fetch pipeline。

> `FENCE.I` 指令过去是 base `I` instruction set 的一部分。虽然在本文写作时它仍然是维护 instruction-fetch coherence 的唯一标准方法，但有两个主要问题促使它从 mandatory base 中移出。
>
> 第一，已经认识到在某些系统上，`FENCE.I` 的实现成本会很高，并且 memory model task group 正在讨论替代机制。特别是，对于具有 incoherent instruction cache 和 incoherent data cache 的设计，或 instruction cache refill 不 snoop coherent data cache 的设计，当遇到 `FENCE.I` 指令时，两个 cache 都必须被完全 flush。如果在 unified cache 或外层 memory system 前面有多级 I-cache 和 D-cache，这个问题会进一步加剧。
>
> 第二，在 Unix-like operating system environment 中，该指令能力不足以直接提供给 user level。`FENCE.I` 只同步本地 hart，而 OS 可以在 `FENCE.I` 之后把 user hart 重新调度到另一个 physical hart。这样会要求 OS 在每次 context migration 时额外执行一次 `FENCE.I`。因此，标准 Linux ABI 已经从 user-level 移除 `FENCE.I`，现在要求通过 system call 维护 instruction-fetch coherence。这允许 OS 在当前系统上最小化所需的 `FENCE.I` 执行次数，并为未来改进的 instruction-fetch coherence 机制提供前向兼容。
>
> 正在讨论的未来 instruction-fetch coherence 方法包括：提供更受限版本的 `FENCE.I`，只针对由 `rs1` 指定的给定地址；以及/或者允许软件使用依赖 machine-mode cache-maintenance operation 的 ABI。

```text
31       20 19 15 14 12 11 7 6 0
imm[11:0]  rs1 funct3 rd   opcode
12         5   3      5    7

0          0   FENCE.I 0   MISC-MEM
```

`FENCE.I` 指令用于同步 instruction stream 和 data stream。RISC-V 不保证对 instruction memory 的 store 会对某个 RISC-V hart 的 instruction fetch 可见，直到该 hart 执行 `FENCE.I` 指令。`FENCE.I` 指令保证：在某个 RISC-V hart 上，后续 instruction fetch 会看到已经对同一 RISC-V hart 可见的任何先前 data store。

在 multiprocessor system 中，`FENCE.I` 不保证其他 RISC-V hart 的 instruction fetch 会观察到本地 hart 的 store。若要使对 instruction memory 的 store 对所有 RISC-V hart 可见，执行写入的 hart 必须先执行 data `FENCE`，然后请求所有远程 RISC-V hart 执行 `FENCE.I`。

`FENCE.I` 指令中未使用的字段 `imm[11:0]`、`rs1` 和 `rd` 为未来扩展中的 finer-grain fence 保留。为了前向兼容，base implementation 应忽略这些字段，standard software 应将这些字段置零。

> 由于 `FENCE.I` 只把 store 与某个 hart 自己的 instruction fetch 排序，application code 只有在 application thread 不会迁移到另一个 hart 时，才应依赖 `FENCE.I`。EEI 可以提供高效 multiprocessor instruction-stream synchronization 的机制。
