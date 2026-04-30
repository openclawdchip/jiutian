# Appendix A RVWMO Explanatory Material, Version 0.1

本附录使用更非正式的语言和具体示例，对 RVWMO（Chapter 14）提供更多解释。这些解释旨在澄清 axioms 和 preserved program order rules 的含义与意图。本附录应视为 commentary；所有规范性材料都在 Chapter 14 以及 ISA 规范正文其余部分中给出。所有当前已知差异列在 A.7 节中。任何其他差异都是非有意的。

## A.1 Why RVWMO?

内存一致性模型大致分布在从 weak 到 strong 的松散谱系上。weak memory models 允许更多硬件实现灵活性，并且相较 strong models，可以说能提供更好的性能、每瓦性能、功耗、可扩展性和硬件验证开销；代价是编程模型更复杂。strong models 提供更简单的编程模型，但代价是对 pipeline 和 memory system 中可以执行的（非 speculative）硬件优化类型施加更多限制，进而在功耗、面积开销和验证负担方面带来一定成本。

RISC-V 选择了 RVWMO memory model，这是 release consistency 的一种变体。它位于内存模型谱系两个极端之间。RVWMO memory model 使架构师可以构建简单实现、激进实现、深度嵌入更大系统并受复杂内存系统交互影响的实现，或许多其他可能实现；同时它又足够强，可以高性能支持 programming language memory models。

为了便于从其他架构移植代码，一些硬件实现可以选择实现 `Ztso` 扩展，该扩展默认提供更严格的 RVTSO ordering semantics。为 RVWMO 编写的代码自动且天然兼容 RVTSO；但假定 RVTSO 编写的代码不能保证在 RVWMO 实现上正确运行。事实上，大多数 RVWMO 实现会（也应该）直接拒绝运行 RVTSO-only binaries。因此，每个实现都必须选择，是优先考虑与 RVTSO 代码的兼容性（例如便于从 x86 移植），还是优先考虑与实现 RVWMO 的其他 RISC-V cores 的兼容性。

在为 RVWMO 编写的代码中，某些 fences 和/或 memory ordering annotations 在 RVTSO 下可能变得冗余；RVWMO 作为默认模型给 `Ztso` 实现施加的成本，是获取这些 fences 的增量开销，例如 `FENCE R,RW` 和 `FENCE RW,W`，而这些 fences 在该实现上会成为 no-ops。不过，如果希望与非 `Ztso` 实现兼容，这些 fences 必须仍然保留在代码中。

## A.2 Litmus Tests

本章解释使用 litmus tests，即设计用于测试或突出内存模型某一特定方面的小程序。图 A.1 给出一个具有两个 harts 的 litmus test 示例。作为本图以及本章后续所有图的约定，假设 `s0`-`s2` 在所有 harts 中预先设置为相同值，`s0` 保存标记为 `x` 的地址，`s1` 保存 `y`，`s2` 保存 `z`，其中 `x`、`y` 和 `z` 是互不重叠且按 8 字节边界对齐的内存位置。每个图左侧显示 litmus test 代码，右侧显示某个特定有效或无效执行的可视化。

图 A.1：一个示例 litmus test 和一个 forbidden execution（`a0=1`）。

```text
Hart 0                         Hart 1
...                            ...
li t1,1                        li t4,4
(a) sw t1,0(s0)                (e) sw t4,0(s0)
...                            ...
li t2,2
(b) sw t2,0(s0)
... 
(c) lw a0,0(s0)
...
li t3,3                        li t5,5
(d) sw t3,0(s0)                (f) sw t5,0(s0)
...

Execution candidate:
a: Wx=1
b: Wx=2
c: Rx=1
d: Wx=3
e: Wx=4
f: Wx=5
Edges include co, rf, and fr.
```

litmus tests 用于理解内存模型在具体场景中的含义。例如，在图 A.1 的 litmus test 中，第一个 hart 中 `a0` 的最终值可以是 2、4 或 5，这取决于运行时两个 hart 指令流的动态交错。不过在这个示例中，Hart 0 中 `a0` 的最终值绝不会是 1 或 3；直观地说，在 load 执行时，值 1 已经不再可见，而在 load 执行时，值 3 还尚未可见。下面会分析这个测试以及许多其他测试。

每个 litmus test 右侧的图显示所考虑的特定 execution candidate 的可视化表示。这些图使用内存模型文献中常见的一种记法，用于约束可能产生相关执行的 global memory orders 集合。它也是 Appendix B.2 中 herd models 的基础。该记法在表 A.1 中解释。在列出的关系中，harts 之间的 `rf` edges、`co` edges、`fr` edges 和 `ppo` edges 会直接约束 global memory order；`fence`、`addr`、`data` 和某些 `ctrl` edges 也会经由 `ppo` 约束 global memory order。其他 edges（例如 intra-hart `rf` edges）提供信息，但不约束 global memory order。

表 A.1：本附录 litmus test diagrams 的图例。

| Edge | Full Name and explanation |
|---|---|
| `rf` | Reads From：从每个 store 指向返回该 store 所写值的 loads |
| `co` | Coherence：每个地址上的 stores 全序 |
| `fr` | From-Reads：从每个 load 指向该 load 所读 store 的 `co` successors |
| `ppo` | Preserved Program Order |
| `fence` | 由 `FENCE` 指令强制的 orderings |
| `addr` | Address Dependency |
| `ctrl` | Control Dependency |
| `data` | Data Dependency |

例如，在图 A.1 中，`a0=1` 只有在以下某种情况为真时才可能发生：

- `(b)` 在 global memory order 中先于 `(a)`，并且在 coherence order `co` 中也先于 `(a)`。然而，这违反 RVWMO PPO rule 1。从 `(b)` 到 `(a)` 的 `co` edge 突出了这一矛盾。
- `(a)` 在 global memory order 中先于 `(b)`，并且在 coherence order `co` 中也先于 `(b)`。然而在这种情况下，Load Value Axiom 会被违反，因为 `(a)` 不是 program order 中 `(c)` 之前的最新 matching store。从 `(c)` 到 `(b)` 的 `fr` edge 突出了这一矛盾。

由于这两种情形都不满足 RVWMO axioms，结果 `a0=1` 被禁止。

除本附录描述内容之外，还有一个包含七千多个 litmus tests 的套件，可在 `https://github.com/litmus-tests/litmus-tests-riscv` 获取。litmus tests repository 还提供了如何在 RISC-V 硬件上运行 litmus tests，以及如何把结果与 operational 和 axiomatic models 比较的说明。未来，预计这些 memory model litmus tests 也会被调整为 RISC-V compliance test suite 的一部分。

## A.3 Explaining the RVWMO Rules

本节为所有 RVWMO rules 和 axioms 提供解释和示例。

### A.3.1 Preserved Program Order and Global Memory Order

preserved program order 表示必须在 global memory order 中遵守的 program order 子集。概念上，同一 hart 中由 preserved program order 排序的 events，必须从其他 harts 和/或 observers 的视角以该顺序出现。另一方面，同一 hart 中没有由 preserved program order 排序的 events，可以从其他 harts 和/或 observers 的视角看起来发生了重排。

非正式地说，global memory order 表示 loads 和 stores perform 的顺序。形式化内存模型文献已经不再围绕 performing 概念构建规范，但这个思想仍有助于建立非正式直觉。当某个 load 的返回值被确定时，可称该 load 已 perform。store 并不是在 pipeline 内执行时就 perform，而是只有当其值传播到 globally visible memory 时才 perform。从这个意义上说，global memory order 也表示 coherence protocol 和/或内存系统其余部分如何把每个 hart 发出的（可能被重排的）内存访问交错进一个所有 harts 都同意的单一全序。

loads perform 的顺序并不总是直接对应这两个 loads 返回值的相对新旧。特别是，对同一地址的 load `b` 可以先于另一个 load `a` perform，即 `b` 可以先于 `a` 执行，并且 `b` 可以在 global memory order 中先于 `a`；但 `a` 仍可能返回比 `b` 更旧的值。这种差异捕捉了放在 core 和 memory 之间的 buffering 所导致的重排效果。例如，`b` 可能从 store buffer 中的某个 store 返回值，而 `a` 可能忽略这个更年轻的 store，并改为从内存读取更旧值。为解释这一点，每个 load perform 时，其返回值由 load value axiom 决定，而不仅仅严格由 global memory order 中对同一地址的最近 store 决定，如下所述。

### A.3.2 Load Value Axiom

Load Value Axiom：每个 load `i` 的每个字节，返回以下 stores 中在 global memory order 中最新的那个 store 写入该字节的值：

1. 写入该字节且在 global memory order 中先于 `i` 的 stores。
2. 写入该字节且在 program order 中先于 `i` 的 stores。

preserved program order 不要求遵守一个 store 后跟一个对重叠地址的 load 的顺序。这种复杂性源于几乎所有实现中普遍存在的 store buffers。非正式地说，load 可以通过从 store buffer 中的 store 转发而 perform（返回值），此时该 store 仍在 store buffer 中，因此 load 可能先于 store 自身 perform（写回 globally visible memory）。因此，任何其他 hart 都会观察到 load 在 store 之前 perform。

图 A.2：store buffer forwarding litmus test（结果允许）。

```text
Hart 0                         Hart 1
li t1, 1                       li t1, 1
(a) sw t1,0(s0)                (e) sw t1,0(s1)
(b) lw a0,0(s0)                (f) lw a2,0(s1)
(c) fence r,r                  (g) fence r,r
(d) lw a1,0(s1)                (h) lw a3,0(s0)

Outcome: a0=1, a1=0, a2=1, a3=0
```

在带 store buffers 的实现上运行图 A.2 程序时，可以按如下方式得到最终结果 `a0=1, a1=0, a2=1, a3=0`：

- `(a)` 执行并进入第一个 hart 的 private store buffer。
- `(b)` 执行，并从 store buffer 中的 `(a)` 转发其返回值 1。
- `(c)` 执行，因为所有先前 loads，即 `(b)`，已经完成。
- `(d)` 执行并从内存读取值 0。
- `(e)` 执行并进入第二个 hart 的 private store buffer。
- `(f)` 执行，并从 store buffer 中的 `(e)` 转发其返回值 1。
- `(g)` 执行，因为所有先前 loads，即 `(f)`，已经完成。
- `(h)` 执行并从内存读取值 0。
- `(a)` 从第一个 hart 的 store buffer 排出到内存。
- `(e)` 从第二个 hart 的 store buffer 排出到内存。

因此，内存模型必须能够解释这种行为。

换句话说，假设 preserved program order 的定义包含以下假想规则：如果 memory access `a` 在 program order 中先于 memory access `b`，且 `a` 和 `b` 是对同一内存位置的访问，`a` 是 write，`b` 是 read，则 `a` 在 preserved program order 中先于 `b`，因此也在 global memory order 中先于 `b`。称之为 “Rule X”。那么得到：

- `(a)` 先于 `(b)`：由 rule X。
- `(b)` 先于 `(d)`：由 rule 4。
- `(d)` 先于 `(e)`：由 load value axiom。否则，如果 `(e)` 先于 `(d)`，则 `(d)` 必须返回值 1。
- `(e)` 先于 `(f)`：由 rule X。
- `(f)` 先于 `(h)`：由 rule 4。
- `(h)` 先于 `(a)`：同样由 load value axiom。

global memory order 必须是全序，不能循环，因为循环意味着循环中的每个 event 都先于自身，这是不可能的。因此，上述执行会被禁止，而加入 rule X 就会禁止带 store buffer forwarding 的实现，这显然是不希望的。

然而，即使 `(b)` 在 global memory order 中先于 `(a)`，和/或 `(f)` 先于 `(e)`，在这个示例中唯一合理的可能性仍然是 `(b)` 返回 `(a)` 写入的值，`(f)` 和 `(e)` 同理。这种情形组合导致 load value axiom 定义中的第二个选项。即使 `(b)` 在 global memory order 中先于 `(a)`，由于 `(b)` 执行时 `(a)` 位于 store buffer 中，`(a)` 对 `(b)` 仍然可见。因此，即使 `(b)` 在 global memory order 中先于 `(a)`，`(b)` 也应返回 `(a)` 写入的值，因为 `(a)` 在 program order 中先于 `(b)`。`(e)` 和 `(f)` 同理。

图 A.3：“PPOCA” store buffer forwarding litmus test（结果允许）。

```text
Hart 0                         Hart 1
li t1, 1                       li t1, 1
(a) sw t1,0(s0)                LOOP:
(b) fence w,w                  (d) lw a0,0(s1)
(c) sw t1,0(s1)                beqz a0, LOOP
                               (e) sw t1,0(s2)
                               (f) lw a1,0(s2)
                               xor a2,a1,a1
                               add s0,s0,a2
                               (g) lw a2,0(s0)

Outcome: a0=1, a1=1, a2=0
```

另一个突出 store buffers 行为的测试见图 A.3。在该示例中，`(d)` 因 control dependency 而排在 `(e)` 之前，`(f)` 因 address dependency 而排在 `(g)` 之前。不过，`(e)` 不一定排在 `(f)` 之前，即使 `(f)` 返回 `(e)` 写入的值。这可以对应以下事件序列：

- `(e)` speculative 执行并进入第二个 hart 的 private store buffer，但尚未排出到内存。
- `(f)` speculative 执行，并从 store buffer 中的 `(e)` 转发其返回值 1。
- `(g)` speculative 执行并从内存读取值 0。
- `(a)` 执行，进入第一个 hart 的 private store buffer，并排出到内存。
- `(b)` 执行并 retire。
- `(c)` 执行，进入第一个 hart 的 private store buffer，并排出到内存。
- `(d)` 执行并从内存读取值 1。
- `(e)`、`(f)` 和 `(g)` commit，因为 speculation 结果正确。
- `(e)` 从 store buffer 排出到内存。

### A.3.3 Atomicity Axiom

Atomicity Axiom（for Aligned Atomics）：如果 `r` 和 `w` 是某 hart `h` 中由 aligned `LR` 和 `SC` 指令生成的一对 load 和 store 操作，`s` 是对字节 `x` 的 store，且 `r` 返回由 `s` 写入的值，那么 `s` 必须在 global memory order 中先于 `w`，并且在 global memory order 中，不能有来自 hart `h` 以外、对字节 `x` 的 store 位于 `s` 之后且 `w` 之前。

RISC-V 架构把 atomicity 概念与 ordering 概念解耦。不同于 TSO 等架构，RVWMO 下的 RISC-V atomics 默认不施加任何 ordering requirements。ordering semantics 只由其他适用的 PPO rules 保证。

RISC-V 包含两类 atomics：AMOs 和 LR/SC pairs。二者概念上行为不同。LR/SC 的行为仿佛旧值被带到 core，在该内存位置上的 reservation 持有期间被修改并写回内存。AMOs 则概念上仿佛直接在内存中 perform。因此 AMOs 是天然 atomic 的，而 LR/SC pairs 的 atomic 含义稍有不同：在原 hart 持有 reservation 期间，相关内存位置不会被另一个 hart 修改。

图 A.4：在以下四段独立代码中，store-conditional `(c)` 被允许成功，但不保证成功。

```text
(a) lr.d a0, 0(s0)        (a) lr.d a0, 0(s0)
(b) sd t1, 0(s0)          (b) sw t1, 4(s0)
(c) sc.d t2, 0(s0)        (c) sc.d t2, 0(s0)

(a) lr.w a0, 0(s0)        (a) lr.w a0, 0(s0)
(b) sw t1, 4(s0)          (b) sw t1, 4(s0)
(c) sc.w t2, 0(s0)        (c) sc.w t2, 8(s0)
```

atomicity axiom 禁止其他 harts 的 stores 在 global memory order 中交错到某个 LR 与其配对 SC 之间。atomicity axiom 不禁止 loads 在 program order 或 global memory order 中交错到配对操作之间，也不禁止同一 hart 的 stores 或对 non-overlapping locations 的 stores 在 program order 或 global memory order 中出现在配对操作之间。例如，图 A.4 中的 SC 指令可以成功（但不保证成功）。这些成功都不会违反 atomicity axiom，因为中间的 non-conditional stores 来自与 paired load-reserved 和 store-conditional 指令相同的 hart。这样，按 cache line 粒度跟踪内存访问的 memory system 不会被迫让一个 store-conditional 指令失败，即使它恰好与 reservation 持有的内存位置在同一 cache line 的另一部分发生 false sharing。

atomicity axiom 在技术上还支持 LR 和 SC 触及不同地址和/或使用不同访问大小的情况；不过，这类行为的使用场景预计在实践中很少。同样，与 LR/SC pair 之间来自同一 hart 的 stores 实际重叠 LR 或 SC 引用的内存位置相比，中间 store 只是落在同一个 cache line 上的场景预计更常见。

### A.3.4 Progress Axiom

Progress Axiom：在 global memory order 中，任何内存操作之前都不能有无限序列的其他内存操作。

progress axiom 保证最小 forward progress。它保证一个 hart 的 stores 最终会在有限时间内对系统中的其他 harts 可见，并且来自其他 harts 的 loads 最终能够读取这些值（或其 successors）。如果没有这条规则，例如一个 spinlock 即使另一个 hart 有等待解锁该 spinlock 的 store，也可能合法地无限自旋在某个值上。

progress axiom 的意图不是向 RISC-V 实现中的 harts 施加任何其他 fairness、latency 或 quality of service 概念。任何更强的 fairness 概念都由 ISA 的其余部分、平台和/或设备定义和实现。

forward progress axiom 几乎在所有情况下都会由任何标准 cache coherence protocol 自然满足。带 non-coherent caches 的实现可能必须提供其他机制，以保证所有 stores（或其 successors）最终对所有 harts 可见。

### A.3.5 Overlapping-Address Orderings (Rules 1-3)

Rule 1：`b` 是 store，且 `a` 与 `b` 访问重叠内存地址。

Rule 2：`a` 和 `b` 都是 loads，`x` 是 `a` 和 `b` 都读取的字节，在 program order 中 `a` 和 `b` 之间没有对 `x` 的 store，并且 `a` 和 `b` 对 `x` 返回由不同内存操作写入的值。

Rule 3：`a` 由 AMO 或 SC 指令生成，`b` 是 load，并且 `b` 返回由 `a` 写入的值。

same-address ordering 中后一项为 store 的情况很直接：load 或 store 永远不能与后续对重叠内存位置的 store 重排。从微架构角度看，通常很难或不可能撤销一个 speculative reordered store（如果 speculation 结果无效），因此模型直接不允许这种行为。

另一方面，从 store 到后续 load 的 same-address ordering 不需要强制。如 A.3.2 节所述，这反映了从 buffered stores 向后续 loads 转发值的实现的可观察行为。

same-address load-load ordering requirements 更微妙。基本要求是：同一 hart 中对同一地址的 younger load 不得返回比 older load 返回值更旧的值。这通常称为 `CoRR`（Coherence for Read-Read pairs），或更广义的 “coherence” 或 “sequential consistency per location” requirement 的一部分。过去有些架构放松了 same-address load-load ordering，但事后看来，这通常会使编程模型过于复杂，因此 RVWMO 要求强制 CoRR ordering。不过，由于 global memory order 对应 loads perform 的顺序，而不是返回值的排序，用 global memory order 捕捉 CoRR requirements 需要一点间接表达。

图 A.5：Litmus test `MP+fence.w.w+fri-rfi-addr`（结果允许）。

```text
Hart 0                         Hart 1
li t1, 1                       li t2, 2
(a) sw t1,0(s0)                (d) lw a0,0(s1)
(b) fence w, w                 (e) sw t2,0(s1)
(c) sw t1,0(s1)                (f) lw a1,0(s1)
                               (g) xor t3,a1,a1
                               (h) add s0,s0,t3
                               (i) lw a2,0(s0)

Outcome: a0=1, a1=2, a2=0
```

图 A.5 是更一般 `fri-rfi` 模式的一个实例。术语 `fri-rfi` 指序列 `(d)`、`(e)`、`(f)`：`(d)` “from-reads”（即从比 `(e)` 更早的 write 读取），`(e)` 与它在同一 hart，`(f)` 从同一 hart 中的 `(e)` 读取。从微架构角度，结果 `a0=1, a1=2, a2=0` 是合法的。直观地说，以下过程会产生该结果：

- `(d)` 因某种原因 stalled，可能是在等待其他前序指令。
- `(e)` 执行并进入 store buffer，但尚未排出到内存。
- `(f)` 执行并从 store buffer 中的 `(e)` 转发。
- `(g)`、`(h)` 和 `(i)` 执行。
- `(a)` 执行并排出到内存，`(b)` 执行，`(c)` 执行并排出到内存。
- `(d)` 解除 stall 并执行。
- `(e)` 从 store buffer 排出到内存。

这对应 global memory order `(f), (i), (a), (c), (d), (e)`。注意，即使 `(f)` 先于 `(d)` perform，`(f)` 返回的值也比 `(d)` 返回的值更新。因此，该执行合法，不违反 CoRR requirements。

类似地，如果两个 back-to-back loads 返回由同一个 store 写入的值，那么它们也可以在 global memory order 中乱序出现而不违反 CoRR。注意，这并不等同于说两个 loads 返回相同值，因为两个不同 stores 可以写入相同值。

图 A.6：Litmus test RSW（结果允许）。

```text
Hart 0                         Hart 1
li t1, 1                       (d) lw a0,0(s1)
(a) sw t1,0(s0)                (e) xor t2,a0,a0
(b) fence w, w                 (f) add s4,s2,t2
(c) sw t1,0(s1)                (g) lw a1,0(s4)
                               (h) lw a2,0(s2)
                               (i) xor t3,a2,a2
                               (j) add s0,s0,t3
                               (k) lw a3,0(s0)

Outcome: a0=1, a1=v, a2=v, a3=0
```

图 A.6 中的结果 `a0=1, a1=v, a2=v, a3=0`（其中 `v` 是另一个 hart 写入的某值）可以通过允许 `(g)` 和 `(h)` 重排而观察到。这可能以 speculative 方式完成，并且微架构可以证明该 speculation 合理，例如通过 snooping cache invalidations 且没有发现 invalidation，因为在 `(g)` 之后 replay `(h)` 无论如何都会返回由同一 store 写入的值。因此，假设 `a1` 和 `a2` 最终将获得同一个 store 写入的同一值，则 `(g)` 和 `(h)` 可以合法重排。该执行对应的 global memory order 是 `(h),(k),(a),(c),(d),(g)`。

如果图 A.6 测试中 `a1` 不等于 `a2`，那么确实要求 `(g)` 在 global memory order 中先于 `(h)`。在这种情况下，如果允许 `(h)` 在 global memory order 中先于 `(g)`，就会违反 CoRR，因为 `(h)` 将返回比 `(g)` 返回值更旧的值。因此，PPO rule 2 禁止这种 CoRR violation。由此，PPO rule 2 在两个目标之间取得细致平衡：一方面在所有情况下强制 CoRR，另一方面又足够弱，以允许真实微架构中常见的 `RSW` 和 `fri-rfi` 模式。

还有一条 overlapping-address rule：PPO rule 3 简单规定，在 AMO 或 SC 已经（对于 SC，是成功地）globally perform 之前，不能把来自 AMO 或 SC 的值返回给后续 load。这比较自然地来自概念视图，即 AMOs 和 SC 指令都应在内存中 atomic perform。值得注意的是，PPO rule 3 规定硬件甚至不能把 AMOSWAP 存储的值 non-speculatively forwarding 给后续 load，即使对 AMOSWAP 而言，该 store value 在语义上并不依赖内存中的先前值，不像其他 AMOs 那样。即使 SC store values 在语义上不依赖 paired LR 返回的值，也同样如此。

上述三条 PPO rules 也适用于相关内存访问只部分重叠的情况。例如，使用不同大小的访问来访问同一个 object 时会发生这种情况。还要注意，两个 overlapping memory operations 的 base addresses 不一定相同，两个内存访问也可以重叠。当使用 misaligned memory accesses 时，overlapping-address PPO rules 独立适用于每个 component memory access。

### A.3.6 Fences (Rule 4)

Rule 4：存在一条 `FENCE` 指令把 `a` 排在 `b` 之前。

默认情况下，`FENCE` 指令确保 program order 中位于 fence 之前的指令的所有内存访问（predecessor set）在 global memory order 中早于 program order 中位于 fence 之后的指令的内存访问（successor set）。不过，fences 可以选择性地进一步把 predecessor set 和/或 successor set 限制为更小的内存访问集合，以提供某种加速。具体地，fences 有 `PR`、`PW`、`SR` 和 `SW` 位，用于限制 predecessor 和/或 successor sets。predecessor set 当且仅当 `PR`（相应地 `PW`）置位时包含 loads（相应地 stores）。类似地，successor set 当且仅当 `SR`（相应地 `SW`）置位时包含 loads（相应地 stores）。

`FENCE` 编码目前在四个位 `PR`、`PW`、`SR`、`SW` 上有九种非平凡组合，另有一个额外编码 `FENCE.TSO`，便于映射 “acquire+release” 或 RVTSO semantics。剩余七种组合具有空的 predecessor 和/或 successor sets，因此是 no-ops。在十种非平凡选项中，实践中通常只使用六种：

- `FENCE RW,RW`
- `FENCE.TSO`
- `FENCE RW,W`
- `FENCE R,RW`
- `FENCE R,R`
- `FENCE W,W`

使用任何其他 `PR`、`PW`、`SR`、`SW` 组合的 `FENCE` 指令保留。强烈建议程序员坚持使用这六种。其他组合可能与内存模型产生未知或意外交互。

最后，由于 RISC-V 使用 multi-copy atomic memory model，程序员可以以 thread-local 方式推理 fence bits。这里没有在非 multi-copy atomic 的内存模型中出现的复杂 “fence cumulativity” 概念。

### A.3.7 Explicit Synchronization (Rules 5-8)

Rule 5：`a` 带有 acquire annotation。

Rule 6：`b` 带有 release annotation。

Rule 7：`a` 和 `b` 都带有 RCsc annotations。

Rule 8：`a` 与 `b` 成对。

acquire operation 通常用于 critical section 开始处，它要求 program order 中 acquire 之后的所有内存操作在 global memory order 中也位于 acquire 之后。这确保例如 critical section 内的所有 loads 和 stores 相对于用于保护它的 synchronization variable 都是最新的。acquire ordering 可以用两种方式强制：使用 acquire annotation，它只相对于 synchronization variable 本身强制排序；或使用 `FENCE R,RW`，它相对于所有先前 loads 强制排序。

图 A.7：使用 atomics 的 spinlock。

```text
sd x1, (a1)                  # Arbitrary unrelated store
ld x2, (a2)                  # Arbitrary unrelated load
li t0, 1                     # Initialize swap value.
again:
amoswap.w.aq t0, t0, (a0)    # Attempt to acquire lock.
bnez t0, again               # Retry if held.
# ...
# Critical section.
# ...
amoswap.w.rl x0, x0, (a0)    # Release lock by storing 0.
sd x3, (a3)                  # Arbitrary unrelated store
ld x4, (a4)                  # Arbitrary unrelated load
```

考虑图 A.7。由于该示例使用 `aq`，critical section 中的 loads 和 stores 保证在 global memory order 中出现在用于 acquire lock 的 AMOSWAP 之后。不过，假设 `a0`、`a1` 和 `a2` 指向不同内存位置，critical section 中的 loads 和 stores 在 global memory order 中可以出现在示例开头 “Arbitrary unrelated load” 之后，也可以不在其后。

图 A.8：使用 fences 的 spinlock。

```text
sd x1, (a1)                  # Arbitrary unrelated store
ld x2, (a2)                  # Arbitrary unrelated load
li t0, 1                     # Initialize swap value.
again:
amoswap.w t0, t0, (a0)       # Attempt to acquire lock.
fence r, rw                  # Enforce "acquire" memory ordering
bnez t0, again               # Retry if held.
# ...
# Critical section.
# ...
fence rw, w                  # Enforce "release" memory ordering
amoswap.w x0, x0, (a0)       # Release lock by storing 0.
sd x3, (a3)                  # Arbitrary unrelated store
ld x4, (a4)                  # Arbitrary unrelated load
```

再考虑图 A.8 的替代方案。在这种情况下，即使 AMOSWAP 不通过 `aq` 位强制 ordering，fence 仍然会强制 acquire AMOSWAP 在 global memory order 中早于 critical section 中所有 loads 和 stores。不过，在这种情况下，fence 还强制额外 orderings：它还要求程序开头的 “Arbitrary unrelated load” 在 global memory order 中早于 critical section 的 loads 和 stores。（这个特定 fence 不会相对于片段开头的 “Arbitrary unrelated store” 强制任何 ordering。）因此，fence-enforced orderings 略粗于由 `.aq` 强制的 orderings。

release orderings 与 acquire orderings 完全相同，只是方向相反。release semantics 要求 program order 中 release operation 之前的所有 loads 和 stores 在 global memory order 中也先于 release operation。这确保例如 critical section 中的 memory accesses 在 global memory order 中出现在释放 lock 的 store 之前。与 acquire semantics 一样，release semantics 可以使用 release annotations 或 `FENCE RW,W` 操作强制。使用同一示例时，critical section 中 loads/stores 与代码片段末尾 “Arbitrary unrelated store” 之间的 ordering 只由图 A.8 中的 `FENCE RW,W` 强制，而不是由图 A.7 中的 `rl` 强制。

仅有 RCpc annotations 时，不会强制 store-release-to-load-acquire ordering。这便于移植在 TSO 和/或 RCpc memory models 下编写的代码。要强制 store-release-to-load-acquire ordering，代码必须使用 store-release-RCsc 和 load-acquire-RCsc operations，使 PPO rule 7 适用。RCpc 单独对 C/C++ 中许多用例已经足够，但对 C/C++、Java 和 Linux 中许多其他用例不足；详见 A.5 节。

PPO rule 8 表示 SC 必须在 global memory order 中出现在其 paired LR 之后。这通常会从 LR/SC 用于执行 atomic read-modify-write operation 的常见用法中自然得出，因为存在 inherent data dependency。不过，即使所存储的值不 syntactically depend on paired LR 返回的值，PPO rule 8 也适用。

最后，与 fences 一样，程序员分析 ordering annotations 时不需要担心 “cumulativity”。

### A.3.8 Syntactic Dependencies (Rules 9-11)

Rule 9：`b` 对 `a` 具有 syntactic address dependency。

Rule 10：`b` 对 `a` 具有 syntactic data dependency。

Rule 11：`b` 是 store，且 `b` 对 `a` 具有 syntactic control dependency。

RVWMO memory model 会遵守同一 hart 中从 load 到后续 memory operation 的 dependencies。Alpha memory model 因选择不强制这类 dependencies 的排序而著名，但大多数现代硬件和软件内存模型都认为允许 dependent instructions 被重排过于令人困惑且违反直觉。此外，现代代码有时会有意使用这类 dependencies 作为特别轻量的 ordering enforcement mechanism。

14.1 节中的术语工作方式如下。当写入每个 destination register 的值是 source register(s) 的函数时，称指令把 dependencies 从其 source register(s) 传递到 destination register(s)。对大多数指令，这意味着 destination register(s) 携带来自所有 source register(s) 的 dependency。不过有几个重要例外。对于 memory instructions，写入 destination register 的值最终来自 memory system，而不是直接来自 source register(s)，因此这会切断从 source register(s) 携带的 dependency 链。对于 unconditional jumps，写入 destination register 的值来自当前 `pc`（memory model 从不把 `pc` 视为 source register），因此类似地，`JALR`（唯一带 source register 的 jump）不会把 dependency 从 `rs1` 传递到 `rd`。

图 A.9：`(c)` 通过 `fflags` 对 `(a)` 和 `(b)` 都有 syntactic dependency，`fflags` 是 `(a)` 与 `(b)` 都隐式 accumulate into 的 destination register。

```text
(a) fadd f3,f1,f2
(b) fadd f6,f4,f5
(c) csrrs a0,fflags,x0
```

accumulating into a destination register 而非写入它的概念，反映了 `fflags` 等 CSRs 的行为。特别是，对寄存器的 accumulation 不会 clobber 同一寄存器上的任何先前 writes 或 accumulations。例如在图 A.9 中，`(c)` 对 `(a)` 和 `(b)` 都有 syntactic dependency。

与其他现代内存模型一样，RVWMO memory model 使用 syntactic 而不是 semantic dependencies。换言之，这一定义取决于不同指令访问的寄存器身份，而不是这些寄存器的实际内容。这意味着即使计算似乎可以被 “optimized away”，address、control 或 data dependency 也必须被强制。这个选择确保 RVWMO 与使用这些 false syntactic dependencies 作为轻量 ordering mechanism 的代码兼容。

图 A.10：syntactic address dependency。

```text
ld a1,0(s0)
xor a2,a1,a1
add s1,s1,a2
ld a5,0(s1)
```

例如，图 A.10 中第一条指令生成的 memory operation 到最后一条指令生成的 memory operation 存在 syntactic address dependency，即使 `a1 XOR a1` 为零，因此对第二个 load 访问的地址没有影响。

使用 dependencies 作为轻量 synchronization mechanism 的好处是，ordering enforcement requirement 只限于所讨论的两个具体指令。其他 non-dependent instructions 可以被激进实现自由重排。一种替代方案是使用 load-acquire，但这会对第一个 load 与所有后续指令强制 ordering。另一种替代方案是使用 `FENCE R,R`，但这会包含所有先前和所有后续 loads，使该选项更昂贵。

图 A.11：syntactic control dependency。

```text
lw x1,0(x2)
bne x1,x0,next
sw x3,0(x4)
next: sw x5,0(x6)
```

control dependencies 与 address 和 data dependencies 不同，因为 control dependency 总是扩展到 program order 中原始目标之后的所有指令。考虑图 A.11：`next` 处的指令总会执行，但最后一条指令生成的 memory operation 仍然从第一条指令生成的 memory operation 获得 control dependency。

图 A.12：另一个 syntactic control dependency。

```text
lw x1,0(x2)
bne x1,x0,next
next: sw x3,0(x4)
```

类似地，考虑图 A.12。即使两个 branch outcomes 具有相同目标，从该片段第一条指令生成的 memory operation 到最后一条指令生成的 memory operation 仍存在 control dependency。这种 control dependency 定义比其他语境（例如 C++）中可能见到的定义略强，但符合文献中 control dependencies 的标准定义。

值得注意的是，PPO rules 9-11 也有意设计为遵守源自成功 store-conditional 指令输出的 dependencies。通常，SC 指令之后会有一个条件分支检查结果是否成功；这意味着从 SC 指令生成的 store operation 到分支之后的任何 memory operations 存在 control dependency。PPO rule 11 进而意味着任何后续 store operations 在 global memory order 中都会出现在 SC 生成的 store operation 之后。不过，由于 control、address 和 data dependencies 定义在 memory operations 上，而 unsuccessful SC 不生成 memory operation，因此 unsuccessful SC 与其 dependent instructions 之间不会强制 order。此外，由于 SC 被定义为只有成功时才把 dependencies 从 source registers 传递到 `rd`，unsuccessful SC 对 global memory order 没有影响。

图 A.13：LB litmus test 的变体（结果禁止）。

```text
Initial values: 0(s0)=1; 0(s1)=1

Hart 0                         Hart 1
(a) ld a0,0(s0)                (e) ld a3,0(s2)
(b) lr a1,0(s1)                (f) sd a3,0(s0)
(c) sc a2,a0,0(s1)
(d) sd a2,0(s2)

Outcome: a0=0, a3=0
```

此外，选择遵守源自 store-conditional 指令的 dependencies，可以防止某些类似 out-of-thin-air 的行为。考虑图 A.13。假设某个假想实现偶尔可以提前保证某个 store-conditional 操作会成功。在这种情况下，`(c)` 可以提前（在实际执行前）把 0 返回给 `a2`，从而允许序列 `(d)`、`(e)`、`(f)`、`(a)`，然后 `(b)` 执行，随后 `(c)` 可能只在此时执行并成功。这意味着 `(c)` 把自己的成功值写入 `0(s1)`！幸运的是，RVWMO 遵守源自 successful SC instructions 生成 stores 的 dependencies，因此这种情况以及类似情况被阻止。

还要注意，指令之间的 syntactic dependencies 只有在形成 syntactic address、control 和/或 data dependency 时才具有约束力。例如，两个 `F` 指令之间经由 14.3 节中某个 accumulating CSR 的 syntactic dependency，并不意味着这两个 `F` 指令必须按顺序执行。这样的 dependency 只会最终为这两个 `F` 指令到后续访问相关 CSR flag 的 CSR 指令建立 dependency。

### A.3.9 Pipeline Dependencies (Rules 12-13)

Rule 12：`b` 是 load，并且在 program order 中 `a` 和 `b` 之间存在某个 store `m`，使得 `m` 对 `a` 具有 address 或 data dependency，并且 `b` 返回由 `m` 写入的值。

Rule 13：`b` 是 store，并且在 program order 中 `a` 和 `b` 之间存在某条指令 `m`，使得 `m` 对 `a` 具有 address dependency。

PPO rules 12 和 13 反映了几乎所有真实处理器 pipeline 实现的行为。Rule 12 表示，load 不能从 store 转发，直到该 store 的地址和数据已知。

图 A.14：由于 PPO rule 12 以及从 `(d)` 到 `(e)` 的 data dependency，`(d)` 也必须在 global memory order 中先于 `(f)`（结果禁止）。

```text
Hart 0                         Hart 1
li t1, 1                       (d) lw a0, 0(s1)
(a) sw t1,0(s0)                (e) sw a0, 0(s2)
(b) fence w, w                 (f) lw a1, 0(s2)
(c) sw t1,0(s1)                xor a2,a1,a1
                               add s0,s0,a2
                               (g) lw a3,0(s0)

Outcome: a0=1, a3=0
```

考虑图 A.14：`(f)` 不能执行，直到 `(e)` 的数据已经解析，因为 `(f)` 必须返回 `(e)` 写入的值（或 global memory order 中甚至更晚的某个值），并且在 `(d)` 有机会 perform 之前，旧值不能被 `(e)` 的 writeback clobber。因此，`(f)` 永远不会在 `(d)` perform 之前 perform。

如果在 `(e)` 和 `(f)` 之间有另一个对同一地址的 store，如图 A.15 所示，则 `(f)` 不再依赖 `(e)` 的数据已解析，因此 `(f)` 对产生 `(e)` 数据的 `(d)` 的 dependency 被切断。

图 A.15：由于 `(e)` 和 `(g)` 之间有额外 store，`(d)` 不再必然先于 `(g)`（结果允许）。

```text
Hart 0                         Hart 1
li t1, 1                       li t1, 1
(a) sw t1,0(s0)                (d) lw a0, 0(s1)
(b) fence w, w                 (e) sw a0, 0(s2)
(c) sw t1,0(s1)                (f) sw t1, 0(s2)
                               (g) lw a1, 0(s2)
                               xor a2,a1,a1
                               add s0,s0,a2
                               (h) lw a3,0(s0)

Outcome: a0=1, a3=0
```

Rule 13 与上一条规则类似：store 不能在所有可能访问同一地址的先前 loads 自身已经 perform 之前在内存中 perform。这类 load 必须看起来在 store 之前执行，但如果 store 在 load 有机会读取旧值之前覆盖内存中的值，它就不能做到这一点。类似地，store 通常不能 perform，直到已知前序指令不会因为地址解析失败而产生异常；从这个意义上说，rule 13 可以被视为 rule 11 的某种特殊情况。

图 A.16：由于从 `(d)` 到 `(e)` 的 address dependency，`(d)` 也先于 `(f)`（结果禁止）。

```text
Hart 0                         Hart 1
li t1, 1
(a) lw a0,0(s0)                (d) lw a1, 0(s1)
(b) fence rw,rw                (e) lw a2, 0(a1)
(c) sw s2,0(s1)                (f) sw t1, 0(s0)

Outcome: a0=1, a1=t
```

考虑图 A.16：`(f)` 不能执行，直到 `(e)` 的地址被解析，因为地址可能匹配，即 `a1=s0`。因此，在 `(d)` 已执行并确认地址是否确实重叠之前，`(f)` 不能发送到内存。

## A.4 Beyond Main Memory

RVWMO 当前没有试图形式化描述 `FENCE.I`、`SFENCE.VMA`、I/O fences 和 PMAs 的行为。所有这些行为都将由未来形式化描述。在此期间，`FENCE.I` 的行为见 2.7 节，`SFENCE.VMA` 的行为见 RISC-V Instruction Set Privileged Architecture Manual，I/O fences 的行为和 PMAs 的影响如下所述。

### A.4.1 Coherence and Cacheability

RISC-V Privileged ISA 定义了 Physical Memory Attributes（PMAs），它们规定地址空间部分是否 coherent 和/或 cacheable 等属性。完整细节见 RISC-V Privileged ISA Specification。这里仅讨论每个 PMA 中的各种细节如何与内存模型相关：

- Main memory vs. I/O，以及 I/O memory ordering PMAs：按定义，内存模型适用于 main memory regions。I/O ordering 见下文。
- Supported access types 和 atomicity PMAs：内存模型只是应用在每个 region 支持的 primitives 之上。
- Cacheability PMAs：cacheability PMAs 通常不影响内存模型。Non-cacheable regions 可能具有比 cacheable regions 更受限的行为，但允许行为集合不因此改变。不过，一些 platform-specific 和/或 device-specific cacheability settings 可能不同。
- Coherence PMAs：标记为 non-coherent 的内存 regions 的 memory consistency model 当前是 platform-specific 和/或 device-specific 的：load-value axiom、atomicity axiom 和 progress axiom 在 non-coherent memory 中都可能被违反。不过要注意，coherent memory 不要求硬件 cache coherence protocol。RISC-V Privileged ISA Specification 建议不鼓励 hardware-incoherent regions of main memory，但内存模型兼容 hardware coherence、software coherence、由于 read-only memory 产生的 implicit coherence、由于只有一个 agent 有访问权限而产生的 implicit coherence，或其他方式。
- Idempotency PMAs：Idempotency PMAs 用于指定 loads 和/或 stores 可能具有 side effects 的 memory regions，微架构进而据此决定例如 prefetches 是否合法。这一区分不影响内存模型。

### A.4.2 I/O Ordering

对于 I/O，load value axiom 和 atomicity axiom 通常不适用，因为 reads 和 writes 都可能有 device-specific side effects，并且可能返回不同于同一地址最近 store “写入”的值。不过，以下 preserved program order rules 通常仍适用于访问 I/O memory：如果 `a` 在 program order 中先于 `b`，并且满足以下一个或多个条件，则 memory access `a` 在 global memory order 中先于 memory access `b`：

1. `a` 按 Chapter 14 中定义的 preserved program order 先于 `b`，但 acquire 和 release ordering annotations 只从一个 memory operation 应用到另一个 memory operation，以及从一个 I/O operation 应用到另一个 I/O operation，而不从 memory operation 应用到 I/O，也不反向应用。
2. `a` 和 `b` 是对 I/O region 中重叠地址的访问。
3. `a` 和 `b` 是对同一 strongly-ordered I/O region 的访问。
4. `a` 和 `b` 是对 I/O regions 的访问，并且与 `a` 或 `b` 所访问 I/O region 关联的 channel 是 channel 1。
5. `a` 和 `b` 是对与同一 channel 关联的 I/O regions 的访问，但 channel 0 除外。

注意，`FENCE` 指令在其 predecessor 和 successor sets 中区分 main memory operations 和 I/O operations。要强制 I/O operations 与 main memory operations 之间的 ordering，代码必须使用带 `PI`、`PO`、`SI` 和/或 `SO`，以及 `PR`、`PW`、`SR` 和/或 `SW` 的 `FENCE`。例如，要强制对 main memory 的写入与对 device register 的 I/O write 之间的 ordering，需要 `FENCE W,O` 或更强 fence。

图 A.17：排序 memory 和 I/O accesses。

```text
sd t0, 0(a0)
fence w,o
sd a0, 0(a1)
```

当确实使用 fence 时，实现必须假设设备在收到 MMIO signal 后可能立即尝试访问内存，并且该设备随后对内存的 memory accesses 必须观察到在该 MMIO operation 之前排序的所有 accesses 的效果。换言之，在图 A.17 中，假设 `0(a0)` 位于 main memory，`0(a1)` 是 I/O memory 中的 device register 地址。如果设备在收到 MMIO write 时访问 `0(a0)`，则根据 RVWMO memory model 规则，该 load 概念上必须出现在第一个对 `0(a0)` 的 store 之后。在一些实现中，确保这一点的唯一方式是要求第一个 store 确实在发出 MMIO write 之前完成。其他实现可能找到更激进的方式，还有一些实现对 I/O 和 main memory accesses 可能完全无需做任何不同处理。不过，RVWMO memory model 不区分这些选项；它只提供一种 implementation-agnostic 机制来指定必须强制的 orderings。

许多架构包含 “ordering” fences 和 “completion” fences 的独立概念，特别是在涉及 I/O（相对于 regular main memory）时。Ordering fences 只确保 memory operations 保持顺序，而 completion fences 确保 predecessor accesses 全部完成后，任何 successors 才变得可见。RISC-V 不显式区分 ordering 和 completion fences。相反，这一区分只是从 `FENCE` 位的不同用法推断出来。

对于符合 RISC-V Unix Platform Specification 的实现，I/O devices 和 DMA operations 必须 coherently 且经由 strongly-ordered I/O channels 访问内存。因此，被外部设备并发访问的 regular main memory regions 也可以使用标准 synchronization mechanisms。不符合 Unix Platform Specification 的实现，和/或设备不 coherently 访问内存的实现，需要使用当前 platform-specific 或 device-specific 的机制来强制 coherency。

地址空间中的 I/O regions 应在这些 regions 的 PMAs 中视为 non-cacheable regions。如果没有任何 agent 缓存这些 regions，则 PMA 可以把它们视为 coherent。

本节中的 ordering guarantees 可能不适用于 RISC-V cores 与设备之间 platform-specific 边界之外。特别是，经外部总线（例如 PCIe）发送的 I/O accesses 可能在到达最终目的地之前被重排。在这类情况下，必须根据这些外部设备和总线的 platform-specific rules 强制 ordering。

## A.5 Code Porting and Mapping Guidelines

表 A.2：TSO operations 到 RISC-V operations 的映射。

| x86/TSO Operation | RVWMO Mapping |
|---|---|
| Load | `l{b|h|w|d}; fence r,rw` |
| Store | `fence rw,w; s{b|h|w|d}` |
| Atomic RMW | `amo<op>.{w|d}.aqrl` 或 `loop: lr.{w|d}.aq; <op>; sc.{w|d}.aqrl; bnez loop` |
| Fence | `fence rw,rw` |

表 A.2 给出 TSO memory operations 到 RISC-V memory instructions 的映射。普通 x86 loads 和 stores 天然都是 acquire-RCpc 和 release-RCpc operations：TSO 默认强制所有 load-load、load-store 和 store-store ordering。因此，在 RVWMO 下，所有 TSO loads 必须映射为 load 后跟 `FENCE R,RW`，所有 TSO stores 必须映射为 `FENCE RW,W` 后跟 store。TSO atomic read-modify-writes 和使用 LOCK prefix 的 x86 指令是 fully-ordered 的，可以用同时设置 `aq` 和 `rl` 的 AMO 实现，也可以用设置 `aq` 的 LR、相关 arithmetic operation、同时设置 `aq` 和 `rl` 的 SC，以及检查成功条件的条件分支来实现。在后一种情况下，LR 上的 `rl` annotation 出于不明显原因是冗余的，可以省略。

表 A.2 之外的替代映射也是可能的。TSO store 可以映射到设置 `rl` 的 `AMOSWAP`。不过，由于 RVWMO PPO Rule 3 禁止从 AMOs 向后续 loads 转发值，使用 `AMOSWAP` 实现 stores 可能对性能有负面影响。TSO load 可以用设置 `aq` 的 LR 映射：所有这类 LR 指令都是 unpaired，但这一事实本身并不妨碍使用 LR 作为 loads。不过，如果这给 reservation mechanism 施加比原计划更大的压力，该映射也可能对性能有负面影响。

表 A.3：Power operations 到 RISC-V operations 的映射。

| Power Operation | RVWMO Mapping |
|---|---|
| Load | `l{b|h|w|d}` |
| Load-Reserve | `lr.{w|d}` |
| Store | `s{b|h|w|d}` |
| Store-Conditional | `sc.{w|d}` |
| `lwsync` | `fence.tso` |
| `sync` | `fence rw,rw` |
| `isync` | `fence.i; fence r,r` |

表 A.3 给出 Power memory operations 到 RISC-V memory instructions 的映射。Power `ISYNC` 在 RISC-V 上映射为 `FENCE.I` 后跟 `FENCE R,R`；后一条 fence 是必需的，因为 `ISYNC` 用于定义一种 RVWMO 中不存在的 “control+control fence” dependency。

表 A.4：ARM operations 到 RISC-V operations 的映射。

| ARM Operation | RVWMO Mapping |
|---|---|
| Load | `l{b|h|w|d}` |
| Load-Acquire | `fence rw,rw; l{b|h|w|d}; fence r,rw` |
| Load-Exclusive | `lr.{w|d}` |
| Load-Acquire-Exclusive | `lr.{w|d}.aqrl` |
| Store | `s{b|h|w|d}` |
| Store-Release | `fence rw,w; s{b|h|w|d}` |
| Store-Exclusive | `sc.{w|d}` |
| Store-Release-Exclusive | `sc.{w|d}.rl` |
| `dmb` | `fence rw,rw` |
| `dmb.ld` | `fence r,rw` |
| `dmb.st` | `fence w,w` |
| `isb` | `fence.i; fence r,r` |

表 A.4 给出 ARM memory operations 到 RISC-V memory instructions 的映射。由于 RISC-V 当前没有带 `aq` 或 `rl` annotations 的普通 load/store opcodes，ARM load-acquire 和 store-release operations 应使用 fences 映射。此外，为强制 store-release-to-load-acquire ordering，在 store-release 和 load-acquire 之间必须有 `FENCE RW,RW`；表 A.4 通过总是在每个 acquire operation 前放置 fence 来强制这一点。ARM load-exclusive 和 store-exclusive 指令同样可以映射到 RISC-V LR 和 SC 等价物，但我们不在设置 `aq` 的 LR 前放置 `FENCE RW,RW`，而是同时设置 `rl`。ARM `ISB` 在 RISC-V 上映射为 `FENCE.I` 后跟 `FENCE R,R`，类似于 Power 的 `ISYNC` 映射。

表 A.5 给出 Linux memory ordering macros 到 RISC-V memory instructions 的映射。Linux fences `dma_rmb()` 和 `dma_wmb()` 分别映射为 `FENCE R,R` 和 `FENCE W,W`，因为 RISC-V Unix Platform 要求 coherent DMA；但在带 non-coherent DMA 的平台上，它们将分别映射为 `FENCE RI,RI` 和 `FENCE WO,WO`。带 non-coherent DMA 的平台还可能需要某种机制来 flush 和/或 invalidate cache lines。这类机制将是 device-specific，和/或在未来 ISA 扩展中标准化。

Linux release operations 的映射可能看起来强于必要程度，但这些映射是为了覆盖 Linux 要求比更直观映射更强 ordering 的一些情况。特别是，在写作时，Linux 正在积极讨论是否要求同一 hart 中受同一 synchronization object 保护的某个 critical section 中的 accesses，与后续 critical section 中的 accesses 之间存在 load-load、load-store 和 store-store orderings。并非所有 `FENCE RW,W`/`FENCE R,RW` 映射与 `aq`/`rl` 映射的组合都能提供这类 orderings。解决该问题有几种方法：

1. 总是使用 `FENCE RW,W`/`FENCE R,RW`，永远不使用 `aq`/`rl`。这足够但不理想，因为会违背 `aq`/`rl` modifiers 的目的。
2. 总是使用 `aq`/`rl`，永远不使用 `FENCE RW,W`/`FENCE R,RW`。由于缺少带 `aq` 和 `rl` modifiers 的 load/store opcodes，这当前不可行。
3. 加强 release operations 的映射，使其在存在任一 acquire mapping 类型时都能强制足够 orderings。这是当前推荐方案，也是表 A.5 中展示的方案。

表 A.5：Linux memory primitives 到 RISC-V primitives 的映射。其他构造（例如 spinlocks）应相应遵循。带 non-coherent DMA 的平台或设备可能需要额外 synchronization，例如 cache flush 或 invalidate mechanisms；当前任何这类额外 synchronization 都将是 device-specific。

| Linux Operation | RVWMO Mapping |
|---|---|
| `smp_mb()` | `fence rw,rw` |
| `smp_rmb()` | `fence r,r` |
| `smp_wmb()` | `fence w,w` |
| `dma_rmb()` | `fence r,r` |
| `dma_wmb()` | `fence w,w` |
| `mb()` | `fence iorw,iorw` |
| `rmb()` | `fence ri,ri` |
| `wmb()` | `fence wo,wo` |
| `smp_load_acquire()` | `l{b|h|w|d}; fence r,rw` |
| `smp_store_release()` | `fence.tso; s{b|h|w|d}` |

| Linux Construct | RVWMO AMO Mapping |
|---|---|
| `atomic_<op>_relaxed` | `amo<op>.{w|d}` |
| `atomic_<op>_acquire` | `amo<op>.{w|d}.aq` |
| `atomic_<op>_release` | `amo<op>.{w|d}.rl` |
| `atomic_<op>` | `amo<op>.{w|d}.aqrl` |

| Linux Construct | RVWMO LR/SC Mapping |
|---|---|
| `atomic_<op>_relaxed` | `loop: lr.{w|d}; <op>; sc.{w|d}; bnez loop` |
| `atomic_<op>_acquire` | `loop: lr.{w|d}.aq; <op>; sc.{w|d}; bnez loop` |
| `atomic_<op>_release` | `loop: lr.{w|d}; <op>; sc.{w|d}.aqrl; bnez loop` 或 `fence.tso; loop: lr.{w|d}; <op>; sc.{w|d}; bnez loop` |
| `atomic_<op>` | `loop: lr.{w|d}.aq; <op>; sc.{w|d}.aqrl; bnez loop` |

图 A.18：Linux 中 critical sections 之间的 orderings。

```text
Linux code:
(a) int r0 = *x;
(bc) spin_unlock(y, 0);
...
(d) spin_lock(y);
(e) int r1 = *z;

RVWMO Mapping:
(a) lw a0, 0(s0)
(b) fence.tso        // vs. fence rw,w
(c) sd x0,0(s1)
...
loop:
(d) amoswap.d.aq a1,t1,0(s1)
bnez a1,loop
(e) lw a2,0(s2)
```

例如，Linux 社区当前正在讨论的 critical section ordering rule 会要求图 A.18 中 `(a)` 排在 `(e)` 之前。如果这确实会被要求，那么把 `(b)` 映射为 `FENCE RW,W` 就不够。也就是说，随着 Linux Kernel Memory Model 演进，这些映射可能改变。

表 A.6：C/C++ primitives 到 RISC-V primitives 的映射。

| C/C++ Construct | RVWMO Mapping |
|---|---|
| Non-atomic load | `l{b|h|w|d}` |
| `atomic load(memory_order_relaxed)` | `l{b|h|w|d}` |
| `atomic load(memory_order_acquire)` | `l{b|h|w|d}; fence r,rw` |
| `atomic load(memory_order_seq_cst)` | `fence rw,rw; l{b|h|w|d}; fence r,rw` |
| Non-atomic store | `s{b|h|w|d}` |
| `atomic store(memory_order_relaxed)` | `s{b|h|w|d}` |
| `atomic store(memory_order_release)` | `fence rw,w; s{b|h|w|d}` |
| `atomic store(memory_order_seq_cst)` | `fence rw,w; s{b|h|w|d}` |
| `atomic_thread_fence(memory_order_acquire)` | `fence r,rw` |
| `atomic_thread_fence(memory_order_release)` | `fence rw,w` |
| `atomic_thread_fence(memory_order_acq_rel)` | `fence.tso` |
| `atomic_thread_fence(memory_order_seq_cst)` | `fence rw,rw` |

| C/C++ Construct | RVWMO AMO Mapping |
|---|---|
| `atomic_<op>(memory_order_relaxed)` | `amo<op>.{w|d}` |
| `atomic_<op>(memory_order_acquire)` | `amo<op>.{w|d}.aq` |
| `atomic_<op>(memory_order_release)` | `amo<op>.{w|d}.rl` |
| `atomic_<op>(memory_order_acq_rel)` | `amo<op>.{w|d}.aqrl` |
| `atomic_<op>(memory_order_seq_cst)` | `amo<op>.{w|d}.aqrl` |

| C/C++ Construct | RVWMO LR/SC Mapping |
|---|---|
| `atomic_<op>(memory_order_relaxed)` | `loop: lr.{w|d}; <op>; sc.{w|d}; bnez loop` |
| `atomic_<op>(memory_order_acquire)` | `loop: lr.{w|d}.aq; <op>; sc.{w|d}; bnez loop` |
| `atomic_<op>(memory_order_release)` | `loop: lr.{w|d}; <op>; sc.{w|d}.rl; bnez loop` |
| `atomic_<op>(memory_order_acq_rel)` | `loop: lr.{w|d}.aq; <op>; sc.{w|d}.rl; bnez loop` |
| `atomic_<op>(memory_order_seq_cst)` | `loop: lr.{w|d}.aqrl; <op>; sc.{w|d}.rl; bnez loop` |

表 A.6 给出 C11/C++11 atomic operations 到 RISC-V memory instructions 的映射。如果引入带 `aq` 和 `rl` modifiers 的 load/store opcodes，则表 A.7 中的映射将足够。注意，这两种映射只有在 `atomic_<op>(memory_order_seq_cst)` 映射为同时设置 `aq` 和 `rl` 的 LR 时才能正确互操作。

任何 AMO 都可以由 LR/SC pair 仿真，但必须小心确保所有源自 LR 的 PPO orderings 也源自 SC，并且所有终止于 SC 的 PPO orderings 也终止于 LR。例如，LR 也必须遵守 AMO 具有的任何 data dependencies，因为 load operations 本身没有 data dependency 概念。同样，同一 hart 中其他位置的 `FENCE R,R` 的效果也必须应用到 SC，而 SC 原本不会遵守该 fence。emulator 可以通过把 AMOs 简单映射为 `lr.aq; <op>; sc.aqrl` 达到这一效果，这与其他地方 fully-ordered atomics 的映射相匹配。

表 A.7：如果引入原生 load-acquire 和 store-release opcodes，C/C++ primitives 到 RISC-V primitives 的假想映射。

| C/C++ Construct | RVWMO Mapping |
|---|---|
| Non-atomic load | `l{b|h|w|d}` |
| `atomic load(memory_order_relaxed)` | `l{b|h|w|d}` |
| `atomic load(memory_order_acquire)` | `l{b|h|w|d}.aq` |
| `atomic load(memory_order_seq_cst)` | `l{b|h|w|d}.aq` |
| Non-atomic store | `s{b|h|w|d}` |
| `atomic store(memory_order_relaxed)` | `s{b|h|w|d}` |
| `atomic store(memory_order_release)` | `s{b|h|w|d}.rl` |
| `atomic store(memory_order_seq_cst)` | `s{b|h|w|d}.rl` |
| `atomic_thread_fence(memory_order_acquire)` | `fence r,rw` |
| `atomic_thread_fence(memory_order_release)` | `fence rw,w` |
| `atomic_thread_fence(memory_order_acq_rel)` | `fence.tso` |
| `atomic_thread_fence(memory_order_seq_cst)` | `fence rw,rw` |

| C/C++ Construct | RVWMO AMO Mapping |
|---|---|
| `atomic_<op>(memory_order_relaxed)` | `amo<op>.{w|d}` |
| `atomic_<op>(memory_order_acquire)` | `amo<op>.{w|d}.aq` |
| `atomic_<op>(memory_order_release)` | `amo<op>.{w|d}.rl` |
| `atomic_<op>(memory_order_acq_rel)` | `amo<op>.{w|d}.aqrl` |
| `atomic_<op>(memory_order_seq_cst)` | `amo<op>.{w|d}.aqrl` |

| C/C++ Construct | RVWMO LR/SC Mapping |
|---|---|
| `atomic_<op>(memory_order_relaxed)` | `lr.{w|d}; <op>; sc.{w|d}` |
| `atomic_<op>(memory_order_acquire)` | `lr.{w|d}.aq; <op>; sc.{w|d}` |
| `atomic_<op>(memory_order_release)` | `lr.{w|d}; <op>; sc.{w|d}.rl` |
| `atomic_<op>(memory_order_acq_rel)` | `lr.{w|d}.aq; <op>; sc.{w|d}.rl` |
| `atomic_<op>(memory_order_seq_cst)` | `lr.{w|d}.aq*; <op>; sc.{w|d}.rl` |

`*` 为了与按表 A.6 映射的代码互操作，必须使用 `lr.{w|d}.aqrl`。

## A.6 Implementation Guidelines

RVWMO 和 RVTSO memory models 绝不排除微架构使用复杂 speculation 技术或其他优化形式来提供更高性能。这些模型也不要求使用任何特定 cache hierarchy，甚至不要求使用 cache coherence protocol。相反，这些模型只规定可以暴露给软件的行为。微架构可以自由使用任何 pipeline design、任何 coherent 或 non-coherent cache hierarchy、任何 on-chip interconnect 等，只要设计只允许满足内存模型规则的执行即可。尽管如此，为了帮助人们理解内存模型的实际实现，本节给出一些指导，说明架构师和程序员应如何解释模型规则。

RVWMO 和 RVTSO 都是 multi-copy atomic（或 “other-multi-copy-atomic”）：任何对最初发出该值的 hart 之外某个 hart 可见的 store value，也必须概念上对系统中所有其他 harts 可见。换言之，harts 可以在自己的先前 stores 尚未对所有 harts globally visible 之前从这些 stores 转发，但不允许早期 inter-hart forwarding。multi-copy atomicity 可以通过许多方式强制。它可能由于 caches 和 store buffers 的物理设计而天然成立，也可以通过 single-writer/multiple-reader cache coherence protocol 强制，或通过其他机制成立。

虽然 multi-copy atomicity 对微架构施加一些限制，但它是防止内存模型变得极端复杂的关键属性之一。例如，hart 不能合法地从邻近 hart 的 private store buffer 转发值，除非该转发以不会使新的非法行为在架构上可见的方式完成。cache coherence protocol 也不能在 invalidated 所有其他 caches 中的更旧副本之前，把值从一个 hart 转发到另一个 hart。当然，微架构可以（高性能实现很可能会）通过 speculation 或其他优化在内部违反这些规则，只要任何 non-compliant behaviors 不暴露给程序员即可。

作为解释 RVWMO 中 PPO rules 的粗略指导，从软件角度预计：

- 程序员会经常且主动使用 PPO rules 1 和 4-8。
- expert programmers 会使用 PPO rules 9-11 来加速重要数据结构的 critical paths。
- 即使 expert programmers 也很少或几乎不会直接使用 PPO rules 2-3 和 12-13。它们被包含进来，是为了支持常见微架构优化（rule 2）以及 B.3 节描述的 operational formal modeling approach（rules 3 和 12-13）。它们也有助于从具有类似规则的其他架构移植代码。

从硬件角度预计：

- PPO rules 1 和 3-6 反映了架构师应很熟悉的规则，不应带来多少意外。
- PPO rule 2 反映了一种自然且常见的硬件优化，但非常微妙，因此值得仔细复核。
- PPO rule 7 对架构师可能不是立即显然的，但它是标准内存模型要求。
- load value axiom、atomicity axiom，以及 PPO rules 8-13 反映了大多数硬件实现会自然强制的规则，除非它们包含极端优化。当然，实现仍应确保仔细复核这些规则。硬件还必须确保 syntactic dependencies 不被 “optimized away”。

架构可以自由地以任意保守方式实现任何内存模型规则。例如，硬件实现可以选择执行以下任意或全部行为：

- 把所有 fences 解释为 `FENCE RW,RW`（或如果涉及 I/O，则为 `FENCE IORW,IORW`），无论实际设置了哪些位。
- 把所有带 `PW` 和 `SR` 的 fences 实现为 `FENCE RW,RW`（或如果涉及 I/O，则为 `FENCE IORW,IORW`），因为 `PW` 与 `SR` 组合本来就是四种可能 main memory ordering components 中最昂贵的一种。
- 按 A.5 节描述模拟 `aq` 和 `rl`。
- 强制所有 same-address load-load ordering，即使存在 `fri-rfi` 和 `RSW` 等模式。
- 禁止从 store buffer 中的 store 向后续同地址 AMO 或 LR 转发任何值。
- 禁止从 store buffer 中的 AMO 或 SC 向后续同地址 load 转发任何值。
- 对所有内存访问实现 TSO，并忽略任何不包含 `PW` 和 `SR` ordering 的 main memory fences，例如 `Ztso` 实现将这样做。
- 无论 annotation 如何，都把所有 atomics 实现为 RCsc，甚至 fully-ordered。

实现 RVTSO 的架构可以安全地：

- 忽略所有没有同时带 `PW` 和 `SR` 的 fences，除非该 fence 还排序 I/O。
- 忽略除 rules 4 到 7 之外的所有 PPO rules，因为在 RVTSO 假设下，其余规则与其他 PPO rules 冗余。

其他一般说明：

- Silent stores，即写入某内存位置中已经存在的同一值的 stores，从内存模型角度看与任何其他 store 一样。类似地，实际上不改变内存中值的 AMOs，例如 `rs2` 中的值小于当前内存值的 `AMOMAX`，语义上仍视为 store operations。尝试实现 silent stores 的微架构必须小心确保仍遵守内存模型，特别是在 RSW（A.3.5 节）等通常与 silent stores 不兼容的场景中。
- Writes 可以被合并，即对同一地址的两个连续 writes 可以合并；也可以被 subsumed，即对同一地址 back-to-back writes 中较早的 write 可以省略，只要所得行为不以其他方式违反内存模型语义。

write subsumption 问题可以通过以下示例理解。

图 A.19：Write subsumption litmus test，allowed execution。

```text
Hart 0                         Hart 1
li t1, 3                       li t3, 2
li t2, 1
(a) sw t1,0(s0)                (d) lw a0,0(s1)
(b) fence w, w                 (e) sw a0,0(s0)
(c) sw t2,0(s1)                (f) sw t3,0(s0)
```

按写出的程序，如果 load `(d)` 读取值 1，则 `(a)` 必须在 global memory order 中先于 `(f)`：

- `(a)` 由于 rule 2 在 global memory order 中先于 `(c)`。
- `(c)` 由于 Load Value axiom 在 global memory order 中先于 `(d)`。
- `(d)` 由于 rule 7 在 global memory order 中先于 `(e)`。
- `(e)` 由于 rule 1 在 global memory order 中先于 `(f)`。

换言之，`s0` 中地址所对应内存位置的最终值必须是 2（store `(f)` 写入的值），不能是 3（store `(a)` 写入的值）。

一个非常激进的微架构可能错误地决定丢弃 `(e)`，因为 `(f)` 覆盖它；这又可能导致微架构破坏现在被消除的 `(d)` 和 `(f)` 之间的 dependency（以及因此 `(a)` 和 `(f)` 之间的 dependency）。这会违反内存模型规则，因此被禁止。在其他情况下 write subsumption 可能是合法的，例如如果 `(d)` 与 `(e)` 之间没有 data dependency。

### A.6.1 Possible Future Extensions

预计以下任意或全部可能未来扩展都将与 RVWMO memory model 兼容：

- `V` vector ISA extensions。
- `T` ISA extension 的 transactional memory subset。
- `J` JIT extension。
- 带 `aq` 和 `rl` 设置的 load 和 store opcodes 的 native encodings。
- 限于某些地址的 fences。
- Cache writeback/flush/invalidate 等指令。

图 A.20：Mixed-size discrepancy（axiomatic models 允许，operational model 禁止）。

```text
Hart 0                         Hart 1
li t1, 1                       li t1, 1
(a) lw a0,0(s0)                (d) lw a1,0(s1)
(b) fence rw,rw                (e) amoswap.w.rl a2,t1,0(s2)
(c) sw t1,0(s1)                (f) ld a3,0(s2)
                               (g) lw a4,4(s2)
                               xor a5,a4,a4
                               add s0,s0,a5
                               (h) sw a2,0(s0)

Outcome: a0=1, a1=1, a2=0, a3=1, a4=0
```

图 A.21：Mixed-size discrepancy（axiomatic models 允许，operational model 禁止）。

```text
Hart 0                         Hart 1
li t1, 1                       li t1, 1
(a) lw a0,0(s0)                (d) ld a1,0(s1)
(b) fence rw,rw                (e) lw a2,4(s1)
(c) sw t1,0(s1)                xor a3,a2,a2
                               add s0,s0,a3
                               (f) sw a2,0(s0)

Outcome: a0=0, a1=1, a2=0
```

图 A.22：Mixed-size discrepancy（axiomatic models 允许，operational model 禁止）。

```text
Hart 0                         Hart 1
li t1, 1                       li t1, 1
(a) lw a0,0(s0)                (d) sw t1,4(s1)
(b) fence rw,rw                (e) ld a1,0(s1)
(c) sw t1,0(s1)                (f) lw a2,4(s1)
                               xor a3,a2,a2
                               add s0,s0,a3
                               (g) sw a2,0(s0)

Outcome: a0=1, a1=0x100000001, a1=1
```

## A.7 Known Issues

### A.7.1 Mixed-size RSW

在图 A.20-A.22 所示的 mixed-size RSW variants 家族中，operational 和 axiomatic specifications 之间存在已知差异。为解决这一点，可能会选择加入类似以下的新 PPO rule：如果 `a` 在 program order 中先于 `b`，`a` 和 `b` 都访问 regular main memory（而非 I/O regions），`a` 是 load，`b` 是 store，在 `a` 和 `b` 之间有一个 load `m`，存在一个字节 `x` 同时被 `a` 和 `m` 读取，在 `a` 和 `m` 之间没有写入 `x` 的 store，并且 `m` 在 PPO 中先于 `b`，则 memory operation `a` 在 preserved program order 中先于 memory operation `b`，因此也在 global memory order 中先于 `b`。换言之，用 herd syntax 表示，可能会向 PPO 添加 `(po-loc & rsw);ppo;[W]`。许多实现已经会自然强制这种 ordering。因此，即使该规则尚非官方规则，仍建议 implementers 强制它，以确保与未来可能加入 RVWMO 的该规则 forwards compatibility。
