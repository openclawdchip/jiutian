# Chapter 23 `Ztso` Standard Extension for Total Store Ordering, v0.1

本章定义 `Ztso` 扩展，用于 RISC-V Total Store Ordering（RVTSO）内存一致性模型。RVTSO 被定义为相对于 RVWMO 的增量；RVWMO 在 14.1 节中定义。

`Ztso` 扩展旨在方便移植最初为 x86 或 SPARC 架构编写的代码，因为这两种架构默认使用 TSO。它也支持那些天然提供 RVTSO 行为、并希望把这一事实暴露给软件的实现。

RVTSO 对 RVWMO 做出以下调整：

- 所有 load operations 的行为都像带有 `acquire-RCpc` annotation。
- 所有 store operations 的行为都像带有 `release-RCpc` annotation。
- 所有 AMOs 的行为都像同时带有 `acquire-RCsc` 和 `release-RCsc` annotations。

这些规则使除 4-7 以外的所有 PPO rules 都变得冗余。它们还使任何没有同时设置 `PW` 和 `SR` 的 non-I/O fences 变得冗余。最后，它们还意味着任何内存操作都不会在任一方向上重排越过 AMO。

在 RVTSO 语境中，与 RVWMO 一样，storage ordering annotations 由 PPO rules 5-7 简洁且完整地定义。在这两种内存模型中，Load Value Axiom 允许一个 hart 把其 store buffer 中的值转发给 program order 中后续的 load；也就是说，stores 可以在对其他 harts 可见之前先在本地转发。

尽管 `Ztso` 没有向 ISA 添加任何新指令，但假定 RVTSO 编写的代码无法在不支持 `Ztso` 的实现上正确运行。编译为仅在 `Ztso` 下运行的二进制文件应通过 binary 中的标志指明这一点，使未实现 `Ztso` 的平台可以直接拒绝运行它们。
