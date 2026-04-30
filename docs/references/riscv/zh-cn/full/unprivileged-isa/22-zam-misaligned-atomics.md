# Chapter 22 `Zam` Standard Extension for Misaligned Atomics, v0.1

本章定义 `Zam` 扩展。`Zam` 扩展通过标准化对 misaligned atomic memory operations（AMOs）的支持来扩展 `A` 扩展。在实现 `Zam` 的平台上，misaligned AMOs 只需要相对于其他访问原子执行，且这些其他访问必须是对相同地址、相同大小的访问，包括 non-atomic loads 和 stores。更准确地说，实现 `Zam` 的执行环境受以下公理约束。

Atomicity Axiom for misaligned atomics：如果 `r` 和 `w` 是来自某 hart `h` 的一对 paired misaligned load 和 store 指令，它们具有相同地址和相同大小，那么不能存在一条来自 hart `h` 以外的 store 指令 `s`，使得 `s` 与 `r` 和 `w` 具有相同地址和相同大小，并且 `s` 生成的 store 操作在 global memory order 中位于 `r` 和 `w` 生成的内存操作之间。此外，也不能存在一条来自 hart `h` 以外的 load 指令 `l`，使得 `l` 与 `r` 和 `w` 具有相同地址和相同大小，并且 `l` 生成的 load 操作在 global memory order 中位于 `r` 或 `w` 生成的两个内存操作之间。

这种受限形式的 atomicity 旨在平衡两方面需求：一方面是应用需要支持 misaligned atomics，另一方面是实现实际提供所需原子性程度的能力。

在 `Zam` 下，对齐指令继续按照它们在 RVWMO 下的通常行为执行。

`Zam` 的意图是可以通过以下两种方式之一实现：

1. 对于原生支持指定地址和大小上的 atomic misaligned accesses 的硬件，例如单个 cache line 内的 misaligned accesses，只需遵循适用于 aligned AMOs 的相同规则。
2. 对于不原生支持指定地址和大小上的 misaligned accesses 的硬件，对具有该地址和大小的所有指令（包括 loads）进行 trap，并在一个由给定内存地址和访问大小决定的 mutex 内执行它们，执行可以使用任意数量的内存操作。AMOs 可以通过拆分为单独的 load 和 store 操作来仿真，但所有 preserved program order 规则，例如进入和离开的 syntactic dependencies，都必须表现得好像该 AMO 仍然是单个内存操作。
